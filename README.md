
## 快速啟動 Qwen3-tts

1. 使用Docker建立環境:
   ```bash
   docker build -t qwen3tts_api .
   ```

2. 啟動 API:
    ```bash
    docker run --rm —gpus all -d \
        -p 10006:8000 \
        -v /伺服器路徑/model_weights:/app/model_weights \
        --name tts_test3 \
        qwen3tts_api
    ```

    啟動後請訪問：http://<伺服器網址>:10006/docs 進入 Swagger UI 進行測試。

3. 關閉 API:
    ```bash
    docker stop tts_test3 
    docker rm tts_test3
    ```

## 使用說明

### (5/18) 更新符合公司規定的API規格

API端點```/tts```已根據要求將參數做以下設置：
```
    - content_to_synthesize: 要合成的文字內容
    - speaker_prompt_audio: 參考音檔
    - speaker_prompt_text_transcription: 參考音檔的文字稿
```

curl 命令方式：
```curl
# 預設方法
curl -X POST "http://localhost:8000/tts" \
  -F "speaker_prompt_audio=@/path/to/audio.m4a" \
  -F "speaker_prompt_text_transcription=這是參考音檔的文字稿" \
  -F "content_to_synthesize=你好，我是虛擬助理，今天很高興認識你。" \
  -F "language=Chinese" \
  --output output.wav
```

--------------------------------------------------------------------------------
### 原始版本說明：
Qwen3-tts的優勢情緒生成，會推測提示詞文本的語氣生成最貼近情境的語調、音色

Qwen3-tts的API先實裝了Voice Clone一種功能，其餘功能相較VoxCPM2沒有明顯優勢：

1.  Voice Clone
    於text處輸入希望TTS模型生成的語句
    於language輸入生成語言
    於ref_audio上傳需要克隆的音檔
    於ref_text上傳音檔文字稿
    由於是中國研發的TTS模型，Prompt建議使用簡體中文以避免發音錯誤

2. 其他功能
    模型支援非語言發音，如嘆氣、大笑...等等
    請參考原始模型[Github](https://github.com/QwenLM/Qwen3-TTS?tab=readme-ov-file#quickstart)
    如僅需進行簡單功能測試，可以直接線上使用[ Hugging Face Demo  ](https://huggingface.co/spaces/Qwen/Qwen3-TTS)
