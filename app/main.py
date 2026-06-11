import gc
import io
import os
import shutil
import tempfile
import threading
import time
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
        torch.cuda.ipc_collect()


app = FastAPI(lifespan=lifespan)

# -------------------------
# 將模型輸出的 float32 轉換為標準純 PCM 16bit 二進位流
# -------------------------


def _to_pcm16_bytes(wav):
    if hasattr(wav, "cpu"):
        wav = wav.cpu().numpy()

    wav = np.asarray(wav, dtype=np.float32).flatten()

    wav = np.clip(wav, -1.0, 1.0)

    return (wav * 32767).astype(np.int16).tobytes()


# -------------------------
# TTS API - Voice Clone Streaming
# -------------------------


@app.post("/tts")
def tts_voice_clone_stream(
    speaker_prompt_audio: UploadFile = File(...),
    speaker_prompt_text_transcription: Optional[str] = Form(None),
    content_to_synthesize: str = Form(...),
    language: str = Form(default="Chinese"),
    chunk_size: int = Form(default=8),
):
    # 【核心修正 1】改用系統標準 Temp 目錄，避免在專案目錄下產生權限或衝突問題
    temp_dir = tempfile.gettempdir()
    filename = speaker_prompt_audio.filename or "audio.wav"
    ext = os.path.splitext(filename)[1]
    temp_ref_path = os.path.join(temp_dir, f"tts_ref_{uuid.uuid4()}{ext}")

    with open(temp_ref_path, "wb") as buffer:
        shutil.copyfileobj(speaker_prompt_audio.file, buffer)

    # 【核心修正 2】將推理過程與檔案生命週期優化隔離
    def audio_stream_generator():
        try:
            # 確保推理時獨佔模型資源
            with model_lock:
                print("A. 準備呼叫 engine.generate")
                stream_gen = engine.generate(
                    text=content_to_synthesize,
                    language=language,
                    ref_audio=temp_ref_path,
                    ref_text=speaker_prompt_text_transcription,
                    chunk_size=chunk_size,
                )
                print("B. engine.generate 已返回")

                for chunk, sr, timing in stream_gen:
                    print(f"{len(chunk)=} {time.strftime('%H:%M:%S')}")
                    print(
                        f"shape={chunk.shape}",
                        f"dtype={chunk.dtype}",
                        f"min={chunk.min()}",
                        f"max={chunk.max()}",
                        f"sr={sr}",
                    )
                    yield _to_pcm16_bytes(chunk)

        except Exception as e:
            print(f"❌ 推理運行中發生錯誤: {str(e)}")
        finally:
            # 【核心修正 3】當整個串流徹底結束（或斷開）後，才安全地移除暫存檔
            if os.path.exists(temp_ref_path):
                try:
                    os.remove(temp_ref_path)
                    print(f"🧹 已安全清理暫存檔: {temp_ref_path}")
                except Exception as e:
                    print(f"⚠️ 清理暫存檔失敗: {str(e)}")

    return StreamingResponse(audio_stream_generator(), media_type="audio/x-raw")
