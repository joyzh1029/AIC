# main.py (LangGraph 사용)

from core import create_app
from utils import save_cache

def main():
    app = create_app()
    query = "오늘 한국 정치 뉴스 중 주요 이슈 알려줘"
    result = app.invoke({"query": query})
    print(f"🧠 Gemini 요약 결과:\n\n{result['answer']}")
    
    if result.get("articles"):
        save_cache(result["articles"])

if __name__ == "__main__":
    main()