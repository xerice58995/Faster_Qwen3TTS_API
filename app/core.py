import os

import soundfile as sf
import torch
from faster_qwen3_tts import FasterQwen3TTS


class FasterQwen3TTSEngine:
    def __init__(self):
        self.model = None

    def load_model(self):
        self.model = FasterQwen3TTS.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map="cuda:0",
            dtype=torch.bfloat16,
            cache_dir="/app/model_weights",
            attn_implementation="flash_attention_2",
        )
        print(f"模型已成功載入至設備")

    def generate(self, **kwargs):
        if self.model is None:
            raise RuntimeError("模型尚未載入")
        wav, sr = self.model.generate_voice_design(**kwargs)
        return wav, sr
