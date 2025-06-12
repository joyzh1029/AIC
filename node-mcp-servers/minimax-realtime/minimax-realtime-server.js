// minimax-realtime-server.js - Node.js后端服务
import express from 'express';
import { WebSocketServer } from 'ws';
import cors from 'cors';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

const app = express();
const PORT = process.env.PORT || 3001;

// 中间件
app.use(cors());
app.use(express.json());

// 健康检查端点
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// MiniMax API配置
const MINIMAX_API_BASE = 'https://api.minimaxi.com/v1';
const MINIMAX_WS_BASE = 'wss://api.minimaxi.com/v1/realtime/stream';

// 客户端连接管理
const clients = new Map();

// 音频处理工具类
class AudioProcessor {
  constructor(config) {
    this.sampleRate = config.sampleRate || 16000;
    this.channels = config.channels || 1;
    this.encoding = config.encoding || 'pcm16';
  }

  // PCM转WAV (使用Node.js Buffer而非浏览器API)
  pcmToWav(pcmData) {
    const buffer = Buffer.from(pcmData);
    const length = buffer.length;
    const headerLength = 44;
    const totalLength = headerLength + length;
    
    // 创建WAV文件缓冲区
    const wavBuffer = Buffer.alloc(totalLength);
    
    // WAV文件头
    let offset = 0;
    
    // RIFF标识符
    wavBuffer.write('RIFF', offset); offset += 4;
    wavBuffer.writeUInt32LE(totalLength - 8, offset); offset += 4;
    
    // WAVE标识符
    wavBuffer.write('WAVE', offset); offset += 4;
    
    // fmt chunk
    wavBuffer.write('fmt ', offset); offset += 4;
    wavBuffer.writeUInt32LE(16, offset); offset += 4; // fmt chunk size
    wavBuffer.writeUInt16LE(1, offset); offset += 2; // audio format (PCM)
    wavBuffer.writeUInt16LE(this.channels, offset); offset += 2;
    wavBuffer.writeUInt32LE(this.sampleRate, offset); offset += 4;
    wavBuffer.writeUInt32LE(this.sampleRate * this.channels * 2, offset); offset += 4; // byte rate
    wavBuffer.writeUInt16LE(this.channels * 2, offset); offset += 2; // block align
    wavBuffer.writeUInt16LE(16, offset); offset += 2; // bits per sample
    
    // data chunk
    wavBuffer.write('data', offset); offset += 4;
    wavBuffer.writeUInt32LE(length, offset); offset += 4;
    
    // 复制PCM数据
    buffer.copy(wavBuffer, offset);
    
    return wavBuffer;
  }

  // 重采样
  resample(audioData, fromRate, toRate) {
    if (fromRate === toRate) return audioData;
    
    const ratio = fromRate / toRate;
    const newLength = Math.round(audioData.length / ratio);
    const result = new Float32Array(newLength);
    
    for (let i = 0; i < newLength; i++) {
      const index = i * ratio;
      const indexFloor = Math.floor(index);
      const indexCeil = Math.ceil(index);
      const interpolation = index - indexFloor;
      
      result[i] = audioData[indexFloor] * (1 - interpolation) + 
                  (indexCeil < audioData.length ? audioData[indexCeil] * interpolation : 0);
    }
    
    return result;
  }

  // 音频格式转换
  convertFormat(audioData, fromFormat, toFormat) {
    console.log(`Converting from ${fromFormat} to ${toFormat}`);
    return audioData;
  }
}

// 会话管理器
class SessionManager {
  constructor() {
    this.sessions = new Map();
  }

  createSession(clientId, config) {
    const session = {
      id: uuidv4(),
      clientId: clientId,
      startTime: Date.now(),
      config: config,
      messages: [],
      audioStats: {
        bytesSent: 0,
        bytesReceived: 0,
        duration: 0
      }
    };
    
    this.sessions.set(session.id, session);
    return session;
  }

  getSession(sessionId) {
    return this.sessions.get(sessionId);
  }

  updateSession(sessionId, updates) {
    const session = this.sessions.get(sessionId);
    if (session) {
      Object.assign(session, updates);
    }
    return session;
  }

  deleteSession(sessionId) {
    return this.sessions.delete(sessionId);
  }

  getActiveSessionsCount() {
    return this.sessions.size;
  }

  cleanupExpiredSessions(maxDuration = 3600000) { // 1小时
    const now = Date.now();
    for (const [sessionId, session] of this.sessions) {
      if (now - session.startTime > maxDuration) {
        this.deleteSession(sessionId);
      }
    }
  }
}

// 实例化管理器
const sessionManager = new SessionManager();
const audioProcessor = new AudioProcessor({
  sampleRate: 16000,
  channels: 1,
  encoding: 'pcm16'
});

// API路由 (移到WebSocket服务器创建之前)
app.post('/api/session/create', (req, res) => {
  try {
    const { clientId, config } = req.body;
    if (!clientId || !config) {
      return res.status(400).json({ 
        success: false, 
        error: 'clientId和config是必需的' 
      });
    }
    const session = sessionManager.createSession(clientId, config);
    res.json({ success: true, session });
  } catch (error) {
    console.error('创建会话失败:', error);
    res.status(500).json({ success: false, error: '创建会话失败' });
  }
});

app.get('/api/session/:id', (req, res) => {
  try {
    const session = sessionManager.getSession(req.params.id);
    if (session) {
      res.json({ success: true, session });
    } else {
      res.status(404).json({ success: false, error: 'Session not found' });
    }
  } catch (error) {
    console.error('获取会话失败:', error);
    res.status(500).json({ success: false, error: '获取会话失败' });
  }
});

app.delete('/api/session/:id', (req, res) => {
  try {
    const deleted = sessionManager.deleteSession(req.params.id);
    res.json({ success: deleted });
  } catch (error) {
    console.error('删除会话失败:', error);
    res.status(500).json({ success: false, error: '删除会话失败' });
  }
});

app.get('/api/stats', (req, res) => {
  try {
    res.json({
      activeSessions: sessionManager.getActiveSessionsCount(),
      connectedClients: clients.size,
      uptime: process.uptime(),
      memory: process.memoryUsage()
    });
  } catch (error) {
    console.error('获取统计信息失败:', error);
    res.status(500).json({ success: false, error: '获取统计信息失败' });
  }
});

// 创建HTTP服务器
const server = app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
});

// WebSocket服务器
const wss = new WebSocketServer({ server });

// 处理控制命令
function handleControlCommand(client, command) {
  try {
    switch (command.action) {
      case 'pause':
        client.isStreaming = false;
        client.ws.send(JSON.stringify({ type: 'status', message: '已暂停' }));
        break;
        
      case 'resume':
        client.isStreaming = true;
        client.ws.send(JSON.stringify({ type: 'status', message: '已恢复' }));
        break;
        
      case 'clear':
        client.audioBuffer = [];
        client.ws.send(JSON.stringify({ type: 'status', message: '缓冲区已清空' }));
        break;
        
      default:
        client.ws.send(JSON.stringify({ 
          type: 'error', 
          message: `未知命令: ${command.action}` 
        }));
    }
  } catch (error) {
    console.error('处理控制命令失败:', error);
    client.ws.send(JSON.stringify({ 
      type: 'error', 
      message: '处理控制命令失败' 
    }));
  }
}

// WebSocket连接处理
wss.on('connection', (ws, req) => {
  const clientId = uuidv4();
  
  // 安全的URL解析和API密钥验证
  let apiKey;
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    apiKey = url.searchParams.get('api_key');
  } catch (error) {
    console.error('URL解析失败:', error);
    ws.send(JSON.stringify({ type: 'error', message: 'URL格式错误' }));
    ws.close();
    return;
  }
  
  if (!apiKey || apiKey.length < 10) {
    ws.send(JSON.stringify({ type: 'error', message: 'API Key无效或未提供' }));
    ws.close();
    return;
  }

  console.log(`新客户端连接: ${clientId}`);

  // 安全的WebSocket URL构建
  const minimaxUrl = new URL(MINIMAX_WS_BASE);
  minimaxUrl.searchParams.set('api_key', apiKey);
  const minimaxWs = new WebSocket(minimaxUrl.toString());
  
  // 客户端信息
  const client = {
    id: clientId,
    ws: ws,
    minimaxWs: minimaxWs,
    audioBuffer: [],
    isStreaming: false,
    config: null,
    lastActivity: Date.now()
  };
  
  clients.set(clientId, client);

  // 处理MiniMax WebSocket事件
  minimaxWs.on('open', () => {
    console.log(`MiniMax连接已建立: ${clientId}`);
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'status', message: 'MiniMax连接已建立' }));
    }
  });

  minimaxWs.on('message', (data) => {
    try {
      client.lastActivity = Date.now();
      
      if (ws.readyState !== WebSocket.OPEN) {
        return;
      }

      // 转发MiniMax的响应到客户端
      if (data instanceof Buffer) {
        // 音频数据
        ws.send(data);
      } else {
        // 文本数据
        try {
          const message = JSON.parse(data.toString());
          ws.send(JSON.stringify(message));
        } catch (parseError) {
          console.error('解析MiniMax消息失败:', parseError);
        }
      }
    } catch (error) {
      console.error('处理MiniMax消息失败:', error);
    }
  });

  minimaxWs.on('error', (error) => {
    console.error(`MiniMax连接错误: ${clientId}`, error);
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'error', message: 'MiniMax连接错误' }));
    }
  });

  minimaxWs.on('close', (code, reason) => {
    console.log(`MiniMax连接关闭: ${clientId}, 代码: ${code}, 原因: ${reason}`);
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'status', message: 'MiniMax连接已关闭' }));
      ws.close();
    }
  });

  // 处理客户端消息
  ws.on('message', async (message) => {
    try {
      client.lastActivity = Date.now();
      
      if (message instanceof Buffer) {
        // 音频数据 - 添加缓冲区大小限制
        const MAX_BUFFER_SIZE = 1024 * 1024; // 1MB限制
        if (client.audioBuffer.length > MAX_BUFFER_SIZE) {
          client.audioBuffer = client.audioBuffer.slice(-MAX_BUFFER_SIZE / 2);
        }
        
        client.audioBuffer.push(message);
        
        // 转发到MiniMax
        if (minimaxWs.readyState === WebSocket.OPEN) {
          minimaxWs.send(message);
        }
      } else {
        // 文本消息
        const data = JSON.parse(message.toString());
        
        switch (data.type) {
          case 'init':
            // 初始化配置
            client.config = data.config;
            
            // 发送初始化消息到MiniMax
            if (minimaxWs.readyState === WebSocket.OPEN) {
              minimaxWs.send(JSON.stringify({
                type: 'init',
                config: {
                  model: data.config.model || 'speech-01',
                  voice: data.config.voice || 'zh-CN-XiaoxiaoNeural',
                  audio: {
                    sampleRate: data.config.audio?.sampleRate || 16000,
                    channels: data.config.audio?.channels || 1,
                    encoding: data.config.audio?.encoding || 'pcm16'
                  },
                  session: {
                    id: clientId,
                    maxDuration: 3600 // 最大通话时长1小时
                  }
                }
              }));
            }
            break;

          case 'audio':
            // 音频数据
            if (minimaxWs.readyState === WebSocket.OPEN && data.data) {
              minimaxWs.send(Buffer.from(data.data, 'base64'));
            }
            break;

          case 'control':
            // 控制命令
            if (data.command) {
              handleControlCommand(client, data.command);
            }
            break;

          default:
            // 其他消息类型直接转发
            if (minimaxWs.readyState === WebSocket.OPEN) {
              minimaxWs.send(JSON.stringify(data));
            }
        }
      }
    } catch (error) {
      console.error('处理客户端消息失败:', error);
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'error', message: '消息处理失败' }));
      }
    }
  });

  // 客户端断开连接
  ws.on('close', (code, reason) => {
    console.log(`客户端断开连接: ${clientId}, 代码: ${code}, 原因: ${reason}`);
    
    // 关闭MiniMax连接
    if (minimaxWs.readyState === WebSocket.OPEN) {
      minimaxWs.close();
    }
    
    // 清理客户端信息
    clients.delete(clientId);
  });

  ws.on('error', (error) => {
    console.error(`客户端连接错误: ${clientId}`, error);
  });
});

// 定期清理过期会话和非活跃连接
let cleanupInterval = setInterval(() => {
  // 清理过期会话
  sessionManager.cleanupExpiredSessions();
  
  // 清理非活跃连接 (30分钟无活动)
  const now = Date.now();
  const INACTIVE_TIMEOUT = 30 * 60 * 1000; // 30分钟
  
  clients.forEach((client, clientId) => {
    if (now - client.lastActivity > INACTIVE_TIMEOUT) {
      console.log(`清理非活跃连接: ${clientId}`);
      if (client.ws.readyState === WebSocket.OPEN) {
        client.ws.close();
      }
      if (client.minimaxWs.readyState === WebSocket.OPEN) {
        client.minimaxWs.close();
      }
      clients.delete(clientId);
    }
  });
}, 60000); // 每分钟清理一次

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error('服务器错误:', err);
  res.status(500).json({
    success: false,
    error: '服务器内部错误',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('收到SIGTERM信号，开始优雅关闭...');
  
  // 清理定时器
  if (cleanupInterval) {
    clearInterval(cleanupInterval);
  }
  
  // 关闭所有客户端连接
  clients.forEach((client) => {
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.close();
    }
    if (client.minimaxWs.readyState === WebSocket.OPEN) {
      client.minimaxWs.close();
    }
  });
  
  // 关闭WebSocket服务器
  wss.close(() => {
    console.log('WebSocket服务器已关闭');
    
    // 关闭HTTP服务器
    server.close(() => {
      console.log('HTTP服务器已关闭');
      process.exit(0);
    });
  });
});

process.on('SIGINT', () => {
  console.log('收到SIGINT信号，开始优雅关闭...');
  process.emit('SIGTERM');
});

// 导出模块 (修复为ES模块语法)
export {
  app,
  server,
  wss,
  sessionManager,
  audioProcessor
};
