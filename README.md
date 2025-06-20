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
│   ├── uploads/            # 사용자 업로드 파일 저장소
│   │   ├── original/       # 원본 사진 저장
│   │   └── generated/      # 생성된 아바타 저장
│   ├── avata_generate.py   # 아바타 생성 모듈
│   │
│   │
│   │
│   └── routers/
│         └─  ...           # ComfyUI 관련
│
│
│
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

# !!! 따로 추가 설치, 의존성 충돌 발생 가능
pip install firebase_admin websocket websockets websocket-client tf-keras chromadb sentence_transformers

터미널에서 python main.py로 실행
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
