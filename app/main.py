import gc
import io
import os
import shutil
import tempfile
import threading
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core import FasterQwen3TTSEngine

engine = FasterQwen3TTSEngine()
model_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("正在載入 Qwen3TTS 模型至 GPU...")
    engine.load_model()
    yield
    print("正在關閉 API 並釋放顯存...")
    if engine.model is not None:
        engine.model = None

    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()  # 進階清理：清理進程間通訊的顯存


app = FastAPI(lifespan=lifespan)


# -------------------------
# 虛擬大值 Header，用於在SwaggerUI內進行串流
# -------------------------
def _wav_header_chunk(sample_rate=24000, channels=1, bits_per_sample=16) -> bytes:
    """
    構造一個虛擬的 WAV 標頭。
    將音訊總長度設為一個極大值（約 1.8 GB，相當於 3 小時），
    這樣能強制讓瀏覽器、Swagger UI 和播放器『立刻開始播放』而不會等待下載結束。
    """
    fake_data_size = 1800000000
    fake_riff_size = fake_data_size + 36
    byte_rate = sample_rate * channels * (bits_per_sample // 8)
    block_align = channels * (bits_per_sample // 8)

    header = bytearray()
    header.extend(b"RIFF")
    header.extend(fake_riff_size.to_bytes(4, "little"))
    header.extend(b"WAVE")
    header.extend(b"fmt ")
    header.extend((16).to_bytes(4, "little"))  # Subchunk1Size
    header.extend((1).to_bytes(2, "little"))  # AudioFormat (1 = PCM)
    header.extend(channels.to_bytes(2, "little"))
    header.extend(sample_rate.to_bytes(4, "little"))
    header.extend(byte_rate.to_bytes(4, "little"))
    header.extend(block_align.to_bytes(2, "little"))
    header.extend(bits_per_sample.to_bytes(2, "little"))
    header.extend(b"data")
    header.extend(fake_data_size.to_bytes(4, "little"))
    return bytes(header)


# -------------------------
# 將模型輸出的 float32 轉換為標準純 PCM 16bit 二進位流
# -------------------------


def _to_pcm16_bytes(wav) -> bytes:
    if hasattr(wav, "cpu"):
        wav = wav.cpu().numpy()
    elif isinstance(wav, list):
        wav = np.array(wav)

    wav = wav.astype(np.float32).flatten()

    # 防爆音正規化
    if np.abs(wav).max() > 0:
        wav = wav / np.abs(wav).max()

    return (wav * 32767).astype(np.int16).tobytes()


# -------------------------
# TTS API - Voice Clone Streaming
# -------------------------


@app.post("/tts")
def tts_voice_clone_stream(
    speaker_prompt_audio: UploadFile = File(
        ...,
        description="【必填】參考音檔（樣本），15秒左右，用於克隆說話者的音色。",
    ),
    speaker_prompt_text_transcription: Optional[str] = Form(
        None,
        description="【選填】參考音檔的文字稿，可留白。",
    ),
    content_to_synthesize: str = Form(
        ...,
        description="【必填】想要模型說出的文字內容，使用簡體中文以避免發音錯誤。",
        examples=[
            "你好，我是一位虚拟助理，今天很高兴能够有这个机会认识各位，并和各位介绍功能。"
        ],
    ),
    language: str = Form(
        default="Auto",
        description="【選填】想要模型生成的語言，預設為 Auto",
        examples=["Auto"],
    ),
):

    filename = speaker_prompt_audio.filename or "audio.wav"
    ext = os.path.splitext(filename)[1]
    temp_ref_path = f"temp_ref_{uuid.uuid4()}{ext}"

    with open(temp_ref_path, "wb") as buffer:
        shutil.copyfileobj(speaker_prompt_audio.file, buffer)

    def audio_stream_generator():
        try:
            # 在串流的開頭，使用虛擬的 WAV Header
            yield _wav_header_chunk(sample_rate=24000)

            with model_lock:
                stream_gen = engine.generate(
                    text=content_to_synthesize,
                    language=language,
                    ref_audio=temp_ref_path,
                    ref_text=speaker_prompt_text_transcription,
                )

                # 2. 隨後片段輸出 PCM16 數據
                for chunk, sr, timing in stream_gen:
                    yield _to_pcm16_bytes(chunk)
        except Exception as e:
            print(f"錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail="推理失敗")
        finally:
            if os.path.exists(temp_ref_path):
                os.remove(temp_ref_path)

    # 媒體類型設為標準的 audio/wav，Swagger UI 看到這個就會立刻渲染出播放器！
    return StreamingResponse(audio_stream_generator(), media_type="audio/wav")
