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
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        print(f"模型已成功載入至設備")

    def generate(self, **kwargs):
        if self.model is None:
            raise RuntimeError("模型尚未載入")

        return self.model.generate_voice_clone_streaming(**kwargs)
