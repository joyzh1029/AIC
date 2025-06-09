
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

![image](https://github.com/user-attachments/assets/b43efbe8-e342-499e-a893-46f0c8bafde2)
![image](https://github.com/user-attachments/assets/b2b10885-9623-449b-a02c-5fd1750d71b7)
![image](https://github.com/user-attachments/assets/57454aff-7b3d-43c9-8c6c-43a7be87b932)

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

- FastVLM 모델 사용 보류
- 하드웨어 성능 부족
  ![image](https://github.com/user-attachments/assets/ff23cfdf-2d7f-4965-866e-61c8053e50a1)



## My AI Chingu (AI 친구)

현대적인 웹 기반 AI 컴패니언 인터랙션 애플리케이션 (React + TypeScript 기반)

![My AI Chingu 로고](frontend/public/example_avatar_profile.png AI 컴패니언과의 실시간 채팅 인터페이스
- 👤 개인화된 AI 프로필 시스템
- 🎨 현대적이고 반응형 UI 디자인
- 🎯 참여도 기반 포인트 시스템
- 🎁 선물 및 상호작용 기능
- 🌤️ 날씨 통합 기능
- 🔊 음성 입력 지원
- 📸 이미지 공유 기능

## 기술 스택

### 백엔드
- FastAPI
- TTS (Text-to-Speech)
- OpenAI Whisper

### 프론트엔드
- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui 컴포넌트
- Lucide 아이콘
- Axios (HTTP 클라이언트)

## 프로젝트 구조

```
AIC/
├── backend/                # 백엔드 애플리케이션
│   ├── TTS/                # TTS 서비스
│   │   ├── tts.py          # FastAPI TTS 서버
│   │   └── tts_audio/      # 오디오 파일 저장소
│   │       └── example.mp3 # 음성 재생 테스트용 샘플 파일
│   ├── uploads/             # 사용자 업로드 파일 저장소
│   │   ├── original/       # 원본 사진 저장
│   │   └── generated/      # 생성된 아바타 저장
│   └── avata_generate.py   # 아바타 생성 모듈
├── frontend/               # 프론트엔드 애플리케이션
│   ├── public/             # 정적 파일
│   ├── src/                # 소스 파일
│   │   ├── components/     # 재사용 가능 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── styles/         # 글로벌 스타일
│   │   └── App.tsx         # 메인 애플리케이션 컴포넌트
│   ├── package.json        # 프론트엔드 의존성
│   └── vite.config.ts      # Vite 설정 파일
├── requirements.txt        # Python 패키지 의존성
└── README.md               # 프로젝트 문서
```

## 시작하기

### 사전 요구사항
- Node.js (v18 이상)
- Python (v3.10)
- CUDA 11.8 (GPU 사용 시)
- 가상환경 권장
- npm 또는 yarn

### 1. 저장소 복제
```bash
git clone https://github.com/joyzh1029/AIC.git
cd AIC
```

### 2. CUDA 호환 PyTorch 설치
```bash

# 가상환경 생성 및 활성화 후 Python 패키지 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
# 기본적으로 PyPI에서 패키지를 찾고, 없는 경우 'https://download.pytorch.org/whl/cu118' 경로에서 찾겠다는 의미(extra index)

# fer 패키지 별도 설치 (의존성 체크 없이)
pip install fer==22.5.1 --no-deps
# pip freeze 명령어로 requirements.txt 파일 생성 시, fer 패키지는 제외할 것
```

### 3. 백엔드 설정 및 실행
```bash
cd backend
pip install fastapi uvicorn python-multipart

# 재훈님 작업물 테스트 (루트 디렉토리에서 실행)
python -m backend.main

# TTS 서버가 실행 중이어야 음성 출력 가능
# 현재는 예제 오디오 파일(example.mp3) 재생
cd TTS
python -m uvicorn tts:app --host 0.0.0.0 --port 8181 --reload
```

### 4. 프론트엔드 설정 및 실행
```bash
cd frontend
npm install
npm run dev
```

### 5. 애플리케이션 접속
- 프론트엔드: http://localhost:8080
- 백엔드 TTS API: http://localhost:8181
- 백엔드 상태 확인: http://localhost:8181/health


## 설치 확인
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```


## 주의사항 
fer 패키지는 PyTorch 2.7.0과 직접 호환되지 않아 --no-deps 옵션으로 설치</br>
이는 임시조치로, 추후 얼굴 표정 인식 라이브러리 교체 예정

## API 엔드포인트

### 아바타 관련 API
- `POST /api/avatar/upload`: 사용자 사진 업로드
  - 요청: `multipart/form-data` (파일 + user_id)
  - 응답: `{"success": true, "file_path": "filename.jpg"}`

- `POST /api/avatar/generate`: 아바타 생성
  - 요청: `multipart/form-data` (file_path + user_id)
  - 응답: `{"success": true, "avatar_path": "/uploads/generated/filename.png"}`


## 개발 중인 기능
- [ ] 음성 채팅 통합
- [ ] 이미지 인식 기능
- [ ] 향상된 AI 상호작용
- [ ] 모바일 애플리케이션
- [ ] 사용자 인증 시스템
- [x] 사용자 사진 기반 아바타 생성 기능

FastAPI 서버 실행 uvicorn main:app --reload --port 8181

