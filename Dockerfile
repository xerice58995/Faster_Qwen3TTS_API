# 使用支援 CUDA 的 PyTorch 映像檔
FROM pytorch/pytorch:2.5.1-cuda12.8-cudnn9-runtime

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update -o Acquire::AllowInsecureRepositories=true -o Acquire::AllowDowngradeToInsecureRepositories=true && \
    apt-get install -y --allow-unauthenticated \
    libsndfile1 \
    ffmpeg \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# 安裝 Qwen3-tts
RUN pip install --no-cache-dir -U faster-qwen3-tts

# 複製依賴文件並安裝
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[demo]

# 複製程式碼
COPY . .

# 開放 API 連接埠
EXPOSE 8000

# 啟動指令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
