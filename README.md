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
- Node.js
- Express.js
- MongoDB
- WebSocket
- RESTful API

### 프론트엔드
- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui 컴포넌트
- Lucide 아이콘

## 프로젝트 구조

```
AIC/
├── backend/               # 백엔드 애플리케이션
│   ├── src/               # 소스 파일
│   │   ├── controllers/   # 컨트롤러
│   │   ├── models/        # 데이터 모델
│   │   ├── routes/        # API 라우트
│   │   └── config/        # 설정 파일
│   └── package.json       # 백엔드 의존성
├── frontend/              # 프론트엔드 애플리케이션
│   ├── public/            # 정적 파일
│   ├── src/               # 소스 파일
│   │   ├── components/    # 재사용 가능 컴포넌트
│   │   ├── pages/        # 페이지 컴포넌트
│   │   ├── styles/       # 글로벌 스타일
│   │   └── App.tsx       # 메인 애플리케이션 컴포넌트
│   ├── package.json      # 프론트엔드 의존성
│   └── vite.config.ts    # Vite 설정 파일
└── README.md             # 프로젝트 문서
```

## 시작하기

1. 저장소 복제
```bash
git clone https://github.com/joyzh1029/AIC.git
cd AIC
```

2. 프론트엔드 의존성 설치
```bash
cd frontend
npm install
```

3. 개발 서버 실행
```bash
npm run dev
```

애플리케이션은 `http://localhost:8080`에서 확인 가능

## 개발 중인 기능

- [ ] 음성 채팅 통합
- [ ] 이미지 인식 기능
- [ ] 향상된 AI 상호작용
- [ ] 모바일 애플리케이션
- [ ] 사용자 인증 시스템

---


