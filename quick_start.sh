#!/bin/bash
# quick_start.sh - Todoist MCP 통합 빠른 시작

echo "🚀 Todoist MCP 빠른 시작 스크립트"
echo "=========================="

# Python 설치 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ 오류: Python 3을 찾을 수 없습니다. Python을 먼저 설치해주세요"
    exit 1
fi

# Node.js 설치 확인
if ! command -v node &> /dev/null; then
    echo "❌ 오류: Node.js를 찾을 수 없습니다. Node.js를 먼저 설치해주세요"
    exit 1
fi

# 환경변수 파일 확인
if [ ! -f .env ]; then
    echo "📝 .env 파일 생성 중..."
    cat > .env << EOF
TODOIST_API_TOKEN=your_todoist_api_token
PORT=3001
MCP_SERVER_PORT=8000
REACT_APP_API_URL=http://localhost:3001
REACT_APP_TODOIST_API_TOKEN=your_todoist_api_token   
EOF
    echo "⚠️  .env 파일을 편집하여 Todoist API Token을 추가해주세요"
    echo "   그 다음 이 스크립트를 다시 실행해주세요"
    exit 1
fi

# API Token 설정 확인
source .env
if [ "$TODOIST_API_TOKEN" = "your_todoist_api_token" ]; then
    echo "⚠️  .env 파일에서 Todoist API Token을 먼저 설정해주세요"
    exit 1
fi

# Python 의존성 설치
echo "📦 Python 의존성 설치 중..."
pip3 install fastmcp requests python-dotenv

# Node.js 의존성 설치
echo "📦 Node.js 의존성 설치 중..."
cd node-api
npm install express cors eventsource dotenv
npm install eventsource

cd frontend
npm install eventsource

# 필요한 디렉토리 생성
mkdir -p mcp_project

# 서비스 시작
echo "🔧 서비스 시작 중..."

# MCP 서버 시작
echo "▶️  Todoist MCP 서버 시작 중 (포트 $MCP_SERVER_PORT)..."
cd mcp_project && python3 todoist_server.py &
MCP_PID=$!
cd ..

# MCP 서버 시작 대기
sleep 3

# API 서버 시작
echo "▶️  API 서버 시작 중 (포트 $PORT)..."
node todoist_api_server.js &
API_PID=$!



echo ""
echo "✅ 서비스 시작 성공!"
echo "=========================="
echo "📍 API 서버: http://localhost:$PORT"
echo "📍 MCP 서버: http://localhost:$MCP_SERVER_PORT"
echo ""
echo "🔹 MCP 서버 PID: $MCP_PID"
echo "🔹 API 서버 PID: $API_PID"
echo ""
echo "📌 React 애플리케이션에서 TodoistPanel 컴포넌트를 가져와서 사용하세요"
echo "📌 또는 API 엔드포인트를 사용하세요: http://localhost:$PORT/api/mcp/todoist/*"
echo ""
echo "모든 서비스를 중지하려면 Ctrl+C를 누르세요"

# 종료 신호 캐치
trap "echo ''; echo '🛑 모든 서비스 중지 중...'; kill $MCP_PID $API_PID 2>/dev/null; exit" INT TERM

# 스크립트 실행 유지
wait
