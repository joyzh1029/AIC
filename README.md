
# 📰 News Agent - GNews 기반 뉴스 요약 RAG 시스템

> GNews API를 통해 최신 뉴스를 수집하고, LangChain + FAISS + Gemini를 이용해 요약하는 뉴스 요약 시스템입니다.

---

## 📌 주요 기능

- ✅ GNews API로 뉴스 수집
- 🧠 LangChain 문서 포맷화 및 임베딩 처리
- 🔍 FAISS 기반 유사 문서 검색
- 🤖 Gemini API를 통한 뉴스 요약
- 💾 캐시 기능으로 중복 API 요청 최소화
- 🌐 FastAPI 서버 및 CLI 실행 지원

---

## ⚙️ 실행 방법

### ✅ 1. 환경 설정

`.env` 파일에 아래 내용 추가:

```env
GNEWS_API_KEY=your_gnews_api_key
GEMINI_API_KEY=your_gemini_api_key
```

---

### ✅ 2. CLI 실행

```bash
python main.py
```

### ✅ 3. API 서버 실행

```bash
uvicorn server:app --reload
```

API 문서 자동 제공: [http://localhost:8000/docs](http://localhost:8000/docs)
추후 변경 예정

---

## 💬 예시 요청

```
GET /ask_news?query=오늘 한국 경제 뉴스 알려줘
```

---

## 🚧 향후 개선

- [ ] SQLite / Redis 기반 뉴스 저장소
- [ ] LangGraph 기반 에이전트 흐름 구성
- [ ] 프론트엔드 연동
- [ ] 키워드 기반 트렌드 시각화
