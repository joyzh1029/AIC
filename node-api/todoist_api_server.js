// api_server.js
const express = require('express');
const cors = require('cors');
const { SSEClient } = require('./sse_client');
require('dotenv').config();

const app = express();

// 미들웨어
app.use(cors());
app.use(express.json());

// MCP 연결 설정
let mcpClient = null;
const MCP_SERVER_URL = process.env.MCP_SERVER_URL || `http://localhost:${process.env.MCP_SERVER_PORT || 8002}`;

// MCP 서버에 연결
async function connectToMCP(apiToken) {
  try {
    if (!mcpClient) {
      mcpClient = new SSEClient(MCP_SERVER_URL);
    }
    
    // 제공된 토큰 또는 환경변수의 토큰 사용
    const token = apiToken || process.env.TODOIST_API_TOKEN;
    
    // connect_todoist 도구를 호출하여 연결 확인
    const result = await mcpClient.callTool('connect_todoist', {
      api_token: token
    });
    
    return result;
  } catch (error) {
    console.error('MCP 연결 오류:', error);
    throw error;
  }
}

// API 라우트

// Todoist 연결
app.post('/api/mcp/todoist/connect', async (req, res) => {
  try {
    const { api_token } = req.body;
    const result = await connectToMCP(api_token);
    
    if (result.success) {
      res.json({ success: true, message: 'Todoist MCP에 성공적으로 연결되었습니다' });
    } else {
      res.status(400).json({ success: false, error: result.error });
    }
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 프로젝트 목록 가져오기
app.get('/api/mcp/todoist/projects', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const result = await mcpClient.callTool('get_projects', {});
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 작업 목록 가져오기
app.get('/api/mcp/todoist/tasks', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const { project_id, filter } = req.query;
    const params = {};
    
    if (project_id) params.project_id = project_id;
    if (filter) params.filter = filter;
    
    const result = await mcpClient.callTool('get_tasks', params);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 작업 생성
app.post('/api/mcp/todoist/tasks', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const { content, description, project_id, priority, due_date, labels } = req.body;
    
    const result = await mcpClient.callTool('create_task', {
      content,
      description,
      project_id,
      priority: priority || 4,
      due_date,
      labels
    });
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 작업 완료
app.post('/api/mcp/todoist/tasks/:taskId/complete', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const { taskId } = req.params;
    const result = await mcpClient.callTool('complete_task', {
      task_id: taskId
    });
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 작업 업데이트
app.put('/api/mcp/todoist/tasks/:taskId', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const { taskId } = req.params;
    const { content, description, priority, due_date, labels } = req.body;
    
    const result = await mcpClient.callTool('update_task', {
      task_id: taskId,
      content,
      description,
      priority,
      due_date,
      labels
    });
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 작업 삭제
app.delete('/api/mcp/todoist/tasks/:taskId', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const { taskId } = req.params;
    const result = await mcpClient.callTool('delete_task', {
      task_id: taskId
    });
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 리소스 가져오기 (오늘의 작업)
app.get('/api/mcp/todoist/resources/today', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const result = await mcpClient.getResource('todoist://today');
    res.json({ content: result });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 프로젝트 작업 리소스 가져오기
app.get('/api/mcp/todoist/resources/projects/:projectName', async (req, res) => {
  try {
    if (!mcpClient) {
      return res.status(400).json({ error: 'MCP 서버에 연결되지 않았습니다' });
    }
    
    const { projectName } = req.params;
    const result = await mcpClient.getResource(`todoist://projects/${projectName}`);
    res.json({ content: result });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 서버 시작
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`API 서버가 포트 ${PORT}에서 실행 중입니다`);
});
