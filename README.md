# 🧠 Emotion Agent Project

사람의 얼굴 표정, 음성 텍스트, (추가 예정: 목소리 톤)를 분석해 감정을 파악하고, 공감하는 AI 응답을 생성하는 프로젝트입니다.

## 📁 파일 구조
```
.
├── main.py                   # 전체 실행 파이프라인
├── smol_vlm_module.py       # 얼굴 이미지 → 감정 추론
├── stt_module.py            # 음성 → 텍스트(STT)
├── emotion_core.py          # 감정 추출 및 합성
├── llm_module.py            # Gemini로 공감 메시지 생성
└── voice_emotion_module.py  # (예정) 목소리 톤 기반 감정 분석
```

## 🔧 주요 기능
- 얼굴 분석 (SmolVLM 기반)
- 음성 텍스트 분석 (Whisper)
- 감정 종합 판단
- 공감 기반 자연어 생성 (Gemini API)
- 📌 **추가 예정**: 목소리 톤 기반 감정 인식 (wav2vec2 등)
- 📌 **추가 예정**: 얼굴 표정 세부 파악
- 📌 **추가 예정**: DB 연결 내용 (날씨, 과거 체팅 내역 등등)

얼굴 표정 세부 파악
모델 : https://huggingface.co/ElenaRyumina/face_emotion_recognition <--- 테스트까지 완료!
![image](https://github.com/user-attachments/assets/a9930cd2-89c5-42c2-8f52-bee889d98fdf)


