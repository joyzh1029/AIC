// sse-client.js
const EventSource = require('eventsource');

class SSEClient {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.eventSource = null;
    this.messageHandlers = new Map();
    this.connected = false;
  }

  // MCP 서버에 연결
  connect() {
    return new Promise((resolve, reject) => {
      this.eventSource = new EventSource(`${this.serverUrl}/sse`);
      
      this.eventSource.onopen = () => {
        this.connected = true;
        console.log('MCP 서버에 연결되었습니다');
        resolve();
      };
      
      this.eventSource.onerror = (error) => {
        console.error('SSE 연결 오류:', error);
        this.connected = false;
        reject(error);
      };
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('메시지 파싱 오류:', error);
        }
      };
    });
  }

  // 수신된 메시지 처리
  handleMessage(message) {
    const { id, result, error } = message;
    
    if (this.messageHandlers.has(id)) {
      const handler = this.messageHandlers.get(id);
      
      if (error) {
        handler.reject(new Error(error));
      } else {
        handler.resolve(result);
      }
      
      this.messageHandlers.delete(id);
    }
  }

  // MCP 도구 호출
  async callTool(toolName, params = {}) {
    if (!this.connected) {
      await this.connect();
    }
    
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // 메시지 처리기 저장
      this.messageHandlers.set(messageId, { resolve, reject });
      
      // MCP 서버에 요청 보내기
      fetch(`${this.serverUrl}/tools/${toolName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: messageId,
          params: params
        })
      }).catch(error => {
        this.messageHandlers.delete(messageId);
        reject(error);
      });
      
      // 설정된 시간 초과
      setTimeout(() => {
        if (this.messageHandlers.has(messageId)) {
          this.messageHandlers.delete(messageId);
          reject(new Error('요청 시간 초과'));
        }
      }, 30000); // 30초 초과
    });
  }

  // 리소스 가져오기
  async getResource(resourceUri) {
    if (!this.connected) {
      await this.connect();
    }
    
    const response = await fetch(`${this.serverUrl}/resources/${encodeURIComponent(resourceUri)}`);
    
    if (!response.ok) {
      throw new Error(`리소스 가져오기 실패: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.content;
  }

  // 연결 끊기
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.connected = false;
    }
  }
}

module.exports = { SSEClient };