from qwen_tts import Qwen3TTSModel
import soundfile as sf
import os
import torch

class Qwen3TTSEngine:
    def __init__(self):
        self.model = None

    def load_model(self):
        self.model = Qwen3TTSModel.from_pretrained(
        "./model_weights/Qwen3-TTS-12Hz-1.7B-Base",
        device_map="cuda:0",
        dtype=torch.bfloat16,

        attn_implementation="flash_attention_2",
        )
        print(f"模型已成功載入至設備")

    def generate(self, **kwargs):
        if self.model is None:
            raise RuntimeError("模型尚未載入")
        wav, sr = self.model.generate_voice_design(**kwargs)
        return wav, sr
