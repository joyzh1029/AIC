from backend.config import config
from backend.agent import SimpleAgent

def main():
    """Tavily API를 활용한 AI 검색 에이전트"""
    print("🔍 AI 검색 에이전트")
    print("=" * 30)
    
    try:
        agent = SimpleAgent()
        print("✅ 초기화 완료")
        print("💬 검색하고 싶은 내용을 말해보세요!")
        print("📝 예시: '최신 뉴스', 'AI 관련 정보', '게임 업계 동향'")
        print("🚪 종료: quit\n")
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == 'quit':
                print("👋 안녕히 가세요!")
                break
            if user_input:
                response = agent.query(user_input)
                print(f"Agent: {response}\n")
                
    except Exception as e:
        print(f"❌ 오류: {e}")
        print("💡 .env 파일의 API 키를 확인해주세요.")

if __name__ == "__main__":
    main()