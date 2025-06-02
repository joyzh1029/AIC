# 🔍 MA_CL - Simple Search Agent

Tavily API를 활용한 간단한 AI 검색 에이전트입니다.

## 📋 기능

- **웹 검색**: Tavily API를 통한 실시간 웹 검색
- **뉴스 검색**: 최신 뉴스 정보 검색  
- **AI 답변**: 질문에 대한 직접적인 답변 생성
- **Tool 활용**: OpenAI Function Calling을 통한 도구 사용

## 🚀 설치 및 실행

### 1. 요구사항 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. API 키 발급

#### OpenAI API
- [OpenAI Platform](https://platform.openai.com/) 방문
- API 키 생성

#### Tavily API  
- [Tavily](https://tavily.com/) 방문
- 회원가입 후 API 키 발급

### 4. 실행

```bash
python main.py
```

## 🛠️ 프로젝트 구조

```
ma_cl/
├── backend/
│   ├── __init__.py
│   ├── config.py          # 설정 및 API 키 관리
│   ├── tools.py           # Tavily 검색 도구  
│   └── agent.py           # OpenAI 에이전트
├── main.py                # 메인 실행 파일
├── requirements.txt       # 패키지 의존성
├── .env                   # 환경변수 (git에서 제외)
├── .gitignore            # Git 제외 파일
└── README.md             # 프로젝트 설명
```

## 💡 사용 예시

```
🔍 간단 검색 시스템
==============================
검색하고 싶은 내용을 말해보세요!
예시: '최신 뉴스 알려줘', 'AI 관련 뉴스 검색해줘'
종료: quit

You: 대선 관련 최신 뉴스 알려줘

Agent: 🔧 도구 사용: search_news - 대선
🔍 Tavily 검색: 대선 뉴스 최신
✅ 검색 결과: 3개

최근 대선 관련 주요 뉴스를 찾아드렸습니다:

1. [뉴스 제목]
   - 내용: ...
   - 출처: ...

------------------------------

You: quit
안녕히 가세요!
```

## 🔧 주요 컴포넌트

### SearchTool (`backend/tools.py`)
- `search_web()`: 일반 웹 검색
- `search_news()`: 뉴스 검색 (뉴스 키워드 추가)
- `get_answer()`: Tavily QnA 기능 활용

### SimpleAgent (`backend/agent.py`)
- OpenAI Function Calling 활용
- 3가지 도구 (search_web, search_news, get_answer) 지원
- 자동 도구 선택 및 실행

### Config (`backend/config.py`)
- 환경변수 관리
- API 키 검증
- 모델 설정 (기본: gpt-3.5-turbo)

## 🔑 필수 API 키

| 서비스 | 용도 | 발급 URL |
|--------|------|----------|
| OpenAI | LLM 및 Function Calling | https://platform.openai.com/ |
| Tavily | 실시간 검색 | https://tavily.com/ |

## 📦 주요 패키지

- `openai>=1.0.0`: OpenAI API 클라이언트
- `tavily-python`: Tavily 검색 API
- `python-dotenv`: 환경변수 관리
- `requests>=2.31.0`: HTTP 요청

## 🚨 주의사항

- `.env` 파일은 절대 커밋하지 마세요 (API 키 포함)
- API 키는 안전한 곳에 보관하세요
- Tavily API는 사용량 제한이 있을 수 있습니다

## 🐛 문제 해결

### Tavily API 오류
```bash
❌ Tavily 검색 오류: ...
```
- API 키가 올바른지 확인
- 사용량 한도 확인
- 네트워크 연결 확인

### OpenAI API 오류
```bash
오류: ...
```
- API 키 확인
- 모델 사용 권한 확인
- 잔액 확인

## 📄 라이선스

이 프로젝트는 개인 학습 목적으로 제작되었습니다.