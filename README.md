
## 快速啟動 Faster-Qwen3-tts

1. 使用Docker建立環境:
   ```bash
   docker build -t faster_qwen3tts_api .
   ```

2. 啟動 API:
    ```bash
    docker run --rm --gpus all -d \
        -p 10006:8000 \
        -v /伺服器路徑/model_weights:/app/model_weights \
        --name faster_tts_test3 \
        faster_qwen3tts_api
    ```

3. 測試API:
    由於FastAPI 的 Swagger UI 預設機制是必須等整個請求完全結束、二進位資料全部下載完後，才會在網頁上生成播放器，無法實現串流播放。
    請直接使用curl呼叫以達到快速回應(低TTFT)。
    ```curl
    curl -N -s \
      -X POST "http://localhost:8000/tts" \
      -F 'speaker_prompt_audio=@./Sample.wav;type=audio/wav' \
      -F 'speaker_prompt_text_transcription=你好，我是八维智能的虚拟助理，今天很高兴能够有这个机会认识各位，并和各位介绍这个功能。' \
      -F 'content_to_synthesize=今天是我第一天上班，对我来说是一个全新的开始，也是一个很重要的学习机会。虽然还在熟悉整个环境与流程，但我会尽快上手，把工作内容做好，也希望在接下来的时间里，能够顺利协助大家的需求。' \
      -F 'language=Chinese' \
      -F 'chunk_size=8' \
      | ffplay -f s16le -ar 24000 -i -
    ```

4. 關閉 API:
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
  curl -N -s \
    -X POST "http://localhost:8000/tts" \
    -F 'speaker_prompt_audio=@./Sample.wav;type=audio/wav' \
    -F 'speaker_prompt_text_transcription=你好，我是八维智能的虚拟助理，今天很高兴能够有这个机会认识各位，并和各位介绍这个功能。' \
    -F 'content_to_synthesize=今天是我第一天上班，对我来说是一个全新的开始，也是一个很重要的学习机会。虽然还在熟悉整个环境与流程，但我会尽快上手，把工作内容做好，也希望在接下来的时间里，能够顺利协助大家的需求。' \
    -F 'language=Chinese' \
    -F 'chunk_size=8'
    | ffplay -f s16le -ar 24000 -i -
  ```

--------------------------------------------------------------------------------
### 模型說明：
Faster-Qwen3-TTS為Qwen3-TTS的流式生成版本，將input文字進行文本切塊分成小片段(Chunk)，每當局部小片段生成完畢後就即時回傳，可達成超低首字延遲（TTFT:287ms on RTX3080）。生成品質約略和原生Qwen3-TTS相近。
Faster-Qwen3-TTS的API亦先實裝了Voice Clone一種功能。

其他:
Faster-Qwen-TTS原始Repo [Github](https://github.com/andimarafioti/faster-qwen3-tts)
Qwen-TTS原始模型 [Github](https://github.com/QwenLM/Qwen3-TTS?tab=readme-ov-file#quickstart)
模型支援非語言發音，如嘆氣、大笑...等等
