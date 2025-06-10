const express = require('express');
const cors = require('cors');
const { ScheduleAgentService } = require('./schedule_service.js');
const { StreamableHttpClient } = require('./streamable_http_client.js');

const app = express();
const PORT = process.env.PORT || 3001;

// 미들웨어
app.use(cors());
app.use(express.json());

// 서비스 초기화
const mcpClient = new StreamableHttpClient('http://localhost:8000');
const scheduleService = new ScheduleAgentService(mcpClient);

// API 라우트

// MCP 서버 연결 테스트
app.post('/api/mcp/todoist/connect', async (req, res) => {
  try {
    console.log('📞 MCP 연결 요청 수신');
    
    const result = await mcpClient.connect();
    console.log('✅ MCP 연결 성공');
    
    res.json({
      success: true,
      message: 'MCP 연결 성공',
      result: result
    });
  } catch (error) {
    console.error('❌ MCP 연결 실패:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// 도구 호출
app.post('/api/mcp/todoist/tool/:toolName', async (req, res) => {
  try {
    const { toolName } = req.params;
    const params = req.body || {};
    
    console.log(`🔧 도구 호출: ${toolName}`, params);
    
    const result = await mcpClient.callTool(toolName, params);
    
    res.json({
      success: true,
      result: result
    });
  } catch (error) {
    console.error(`❌ 도구 ${toolName} 호출 실패:`, error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// 도구 목록 조회
app.get('/api/mcp/todoist/tools', async (req, res) => {
  try {
    console.log('📋 도구 목록 조회');
    
    const tools = await mcpClient.listTools();
    
    res.json({
      success: true,
      tools: tools
    });
  } catch (error) {
    console.error('❌ 도구 목록 조회 실패:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// 스마트 일정 에이전트
app.post('/api/schedule/agent', async (req, res) => {
  try {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({
        success: false,
        error: '메시지가 필요합니다'
      });
    }
    
    console.log('🤖 일정 에이전트 요청:', message);
    const result = await scheduleService.processMessage(message);
    
    res.json({
      success: true,
      result: result
    });
  } catch (error) {
    console.error('❌ 일정 에이전트 오류:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// 서버 시작
app.listen(PORT, () => {
  console.log(`🚀 Node.js API 서버가 포트 ${PORT}에서 시작되었습니다`);
  console.log(`📡 StreamableHTTP MCP 클라이언트 준비됨`);
}); 