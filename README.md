
## 快速啟動 Faster-Qwen3-tts

1. 使用Docker建立環境:
   ```bash
   docker build -t faster_qwen3tts_api .
   ```

2. 啟動 API:
    ```bash
    docker run --rm —gpus all -d \
        -p 10006:8000 \
        -v /伺服器路徑/model_weights:/app/model_weights \
        --name faster_tts_test3 \
        faster_qwen3tts_api
    ```

    啟動後請訪問：http://<伺服器網址>:10006/docs 進入 Swagger UI 進行測試。

3. 關閉 API:
    ```bash
    docker stop faster_tts_test3 
    docker rm faster_tts_test3
    ```

## 使用說明

### API規格

API端點```/tts```已根據公司要求將參數做以下設置：
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
  | ffplay -nodisp -autoexit -f s16le -ar 24000 -ac 1 -
```

--------------------------------------------------------------------------------
### 模型說明：
Faster-Qwen3-TTS為Qwen3-TTS的流式生成版本，將input文字進行文本切塊分成小片段(Chunk)，每當局部小片段生成完畢後就即時回傳，可達成超低首字延遲（TTFT:287ms on RTX3080）。生成品質約略和原生Qwen3-TTS相近。
Faster-Qwen3-TTS的API亦先實裝了Voice Clone一種功能。

其他:
Faster-Qwen-TTS原始Repo [Github](https://github.com/andimarafioti/faster-qwen3-tts)
Qwen-TTS原始模型 [Github](https://github.com/QwenLM/Qwen3-TTS?tab=readme-ov-file#quickstart)
模型支援非語言發音，如嘆氣、大笑...等等
