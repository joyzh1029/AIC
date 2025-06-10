// streamable-http-client.js - MCP StreamableHTTP 프로토콜 클라이언트
const fetch = require('node-fetch');

class StreamableHttpClient {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.connected = false;
    this.sessionId = null;
    this.initialized = false;
    
    // URL이 올바른 MCP 엔드포인트를 가리키도록 보장
    if (!this.serverUrl.endsWith('/mcp')) {
      this.serverUrl = this.serverUrl.replace(/\/$/, '') + '/mcp';
    }
  }

  // MCP StreamableHTTP 초기화
  async connect() {
    try {
      console.log('🔄 MCP StreamableHTTP 연결 초기화...');
      
      // MCP StreamableHTTP 초기화 요청
      const initResponse = await fetch(this.serverUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream'  // FastMCP는 두 가지 타입을 동시에 요구
        },
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": 1,
          "method": "initialize",
          "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
              "roots": {
                "listChanged": true
              },
              "sampling": {}
            },
            "clientInfo": {
              "name": "nodejs-streamable-http-client",
              "version": "1.0.0"
            }
          }
        }),
        timeout: 15000
      });
      
      console.log('📊 초기화 응답 상태:', initResponse.status, initResponse.statusText);
      
      if (!initResponse.ok) {
        const errorText = await initResponse.text();
        throw new Error(`초기화 실패: ${initResponse.status} ${initResponse.statusText}\n${errorText}`);
      }
      
      // 세션 ID 가져오기
      this.sessionId = initResponse.headers.get('mcp-session-id') || initResponse.headers.get('x-session-id');
      console.log('🔑 Session ID:', this.sessionId);
      
      // 응답 타입 확인 및 적절한 처리
      const contentType = initResponse.headers.get('content-type');
      let initResult;
      
      if (contentType && contentType.includes('text/event-stream')) {
        // SSE 형식 응답
        const responseText = await initResponse.text();
        console.log('📡 SSE 응답:', responseText.substring(0, 300) + '...');
        
        // SSE 형식 파싱
        const lines = responseText.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              initResult = JSON.parse(line.substring(6));
              break;
            } catch (e) {
              // 다음 라인 시도 계속
            }
          }
        }
      } else {
        // 표준 JSON 응답
        initResult = await initResponse.json();
      }
      
      console.log('✅ MCP StreamableHTTP 초기화 응답:', initResult);
      
      // 응답 포맷 확인
      if (initResult && initResult.result) {
        this.initialized = true;
        this.connected = true;
        console.log('🎉 StreamableHTTP 연결 설정 성공');
        return initResult.result;
      } else if (initResult && initResult.error) {
        throw new Error(`MCP 초기화 오류: ${initResult.error.message}`);
      } else {
        throw new Error('유효하지 않은 초기화 응답 형식');
      }
      
    } catch (error) {
      console.error('❌ StreamableHTTP 연결 실패:', error);
      this.connected = false;
      this.initialized = false;
      throw error;
    }
  }

  // MCP 도구 호출 - StreamableHTTP 방식
  async callTool(toolName, params = {}) {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }
    
    try {
      console.log(`🔧 도구 호출: ${toolName}`, params);
      
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'  // FastMCP 요구사항
      };
      
      // 세션 ID 추가 (있는 경우)
      if (this.sessionId) {
        headers['mcp-session-id'] = this.sessionId;
      }
      
      const response = await fetch(this.serverUrl, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": Date.now(),
          "method": "tools/call",
          "params": {
            "name": toolName,
            "arguments": params
          }
        }),
        timeout: 60000
      });
      
      console.log('🛠️ 도구 호출 응답 상태:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`도구 호출 실패: ${response.status} ${response.statusText}\n${errorText}`);
      }
      
      // 응답 처리 (JSON 또는 SSE 형식 가능)
      const contentType = response.headers.get('content-type');
      let result;
      
      if (contentType && contentType.includes('text/event-stream')) {
        // SSE 형식 응답
        const responseText = await response.text();
        console.log('📡 도구 호출 SSE 응답:', responseText.substring(0, 300) + '...');
        
        // SSE 형식 파싱
        const lines = responseText.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.substring(6));
              if (jsonData.id && (jsonData.result !== undefined || jsonData.error)) {
                result = jsonData;
                break;
              }
            } catch (e) {
              // 다음 라인 시도 계속
            }
          }
        }
      } else {
        // 표준 JSON 응답
        result = await response.json();
      }
      
      console.log('📋 도구 호출 파싱 결과:', JSON.stringify(result, null, 2));
      
      if (result && result.error) {
        throw new Error(`MCP 도구 오류: ${result.error.message}`);
      }
      
      return result ? result.result : null;
    } catch (error) {
      console.error(`❌ 도구 ${toolName} 호출 실패:`, error);
      throw error;
    }
  }

  // MCP 리소스 읽기 - StreamableHTTP 방식
  async getResource(resourceUri) {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }
    
    try {
      const response = await fetch(this.serverUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": Date.now(),
          "method": "resources/read",
          "params": {
            "uri": resourceUri
          }
        }),
        timeout: 30000
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`리소스 읽기 실패: ${response.status} ${response.statusText}\n${errorText}`);
      }
      
      const result = await response.json();
      
      if (result.error) {
        throw new Error(`MCP 리소스 오류: ${result.error.message}`);
      }
      
      return result.result || result;
    } catch (error) {
      console.error(`❌ 리소스 ${resourceUri} 읽기 실패:`, error);
      throw error;
    }
  }

  // 사용 가능한 도구 목록 가져오기
  async listTools() {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }
    
    try {
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
      };
      
      // 세션 ID 추가 (있는 경우)
      if (this.sessionId) {
        headers['mcp-session-id'] = this.sessionId;
      }
      
      const response = await fetch(this.serverUrl, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": Date.now(),
          "method": "tools/list"
        }),
        timeout: 10000
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`도구 목록 조회 실패: ${response.status} ${response.statusText}\n${errorText}`);
      }
      
      // 응답 처리 (JSON 또는 SSE 형식 가능)
      const contentType = response.headers.get('content-type');
      let result;
      
      if (contentType && contentType.includes('text/event-stream')) {
        // SSE 형식 응답
        const responseText = await response.text();
        const lines = responseText.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.substring(6));
              if (jsonData.id && (jsonData.result !== undefined || jsonData.error)) {
                result = jsonData;
                break;
              }
            } catch (e) {
              // 다음 라인 시도 계속
            }
          }
        }
      } else {
        // 표준 JSON 응답
        result = await response.json();
      }
      
      if (result && result.error) {
        throw new Error(`MCP 도구 목록 오류: ${result.error.message}`);
      }
      
      return result ? result.result : null;
    } catch (error) {
      console.error('❌ 도구 목록 조회 실패:', error);
      throw error;
    }
  }

  // Ping 테스트
  async ping() {
    try {
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
      };
      
      // 세션 ID 추가 (있는 경우)
      if (this.sessionId) {
        headers['mcp-session-id'] = this.sessionId;
      }
      
      const response = await fetch(this.serverUrl, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": Date.now(),
          "method": "ping"
        }),
        timeout: 5000
      });
      
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  // 연결 해제
  disconnect() {
    this.connected = false;
    this.initialized = false;
    this.sessionId = null;
    console.log('🔌 StreamableHTTP 연결이 해제되었습니다');
  }

  // 연결 상태 확인
  isConnected() {
    return this.connected && this.initialized;
  }
}

module.exports = { StreamableHttpClient }; 