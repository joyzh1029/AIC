// schedule_service.js - 스마트 일정 에이전트 서비스

class ScheduleAgentService {
  constructor(mcpClient = null) {
    this.mcpClient = mcpClient;  // 외부 MCP 클라이언트 수락
    this.isConnected = false;
  }

  // MCP 클라이언트 설정
  setMcpClient(mcpClient) {
    this.mcpClient = mcpClient;
  }

  // MCP 연결 보장
  async ensureConnection() {
    if (!this.mcpClient) {
      throw new Error('MCP 클라이언트가 설정되지 않았습니다');
    }

    if (!this.isConnected) {
      try {
        // 클라이언트가 아직 연결되지 않은 경우 연결 시도
        if (!this.mcpClient.isConnected()) {
          await this.mcpClient.connect();
        }
        this.isConnected = true;
        console.log('✅ MCP 연결 확인됨');
      } catch (error) {
        console.error('❌ MCP 연결 실패:', error.message);
        throw new Error('FastMCP 서버가 준비되지 않았습니다');
      }
    }
  }

  // 메시지 처리
  async processMessage(message) {
    console.log('🤖 일정 메시지 처리:', message);
    
    try {
      await this.ensureConnection();
      
      // 메시지 분석 및 작업 결정
      const analysis = this.analyzeMessage(message);
      console.log('📋 메시지 분석 결과:', analysis);
      
      let result = {};
      
      // 작업 유형에 따라 처리
      switch (analysis.type) {
        case 'create_task':
          result = await this.createTask(analysis);
          break;
        case 'list_tasks':
          result = await this.listTasks(analysis);
          break;
        case 'get_projects':
          result = await this.getProjects();
          break;
        case 'connection_test':
          result = await this.testConnection();
          break;
        default:
          result = {
            type: 'response',
            message: `메시지를 이해했습니다: "${message}". 구체적인 작업을 요청해주세요.`
          };
      }
      
      return result;
    } catch (error) {
      console.error('❌ 메시지 처리 오류:', error);
      return {
        type: 'error',
        message: `처리 중 오류가 발생했습니다: ${error.message}`
      };
    }
  }

  // 메시지 분석
  analyzeMessage(message) {
    const lowerMessage = message.toLowerCase();
    
    // 작업 생성 관련 키워드
    if (lowerMessage.includes('할일') || lowerMessage.includes('task') || 
        lowerMessage.includes('추가') || lowerMessage.includes('만들') ||
        lowerMessage.includes('생성')) {
      return {
        type: 'create_task',
        content: message,
        title: this.extractTaskTitle(message)
      };
    }
    
    // 목록 조회 관련 키워드
    if (lowerMessage.includes('목록') || lowerMessage.includes('리스트') ||
        lowerMessage.includes('list') || lowerMessage.includes('보여')) {
      return {
        type: 'list_tasks'
      };
    }
    
    // 프로젝트 조회
    if (lowerMessage.includes('프로젝트') || lowerMessage.includes('project')) {
      return {
        type: 'get_projects'
      };
    }
    
    // 연결 테스트
    if (lowerMessage.includes('연결') || lowerMessage.includes('connection') ||
        lowerMessage.includes('테스트') || lowerMessage.includes('test')) {
      return {
        type: 'connection_test'
      };
    }
    
    return {
      type: 'unknown',
      content: message
    };
  }

  // 작업 제목 추출
  extractTaskTitle(message) {
    // 간단한 작업 제목 추출 로직
    let title = message;
    
    // 불필요한 단어 제거
    const wordsToRemove = ['할일', '작업', '추가', '만들어', '생성', '해줘', '주세요'];
    wordsToRemove.forEach(word => {
      title = title.replace(new RegExp(word, 'gi'), '');
    });
    
    return title.trim() || '새 작업';
  }

  // 작업 생성
  async createTask(analysis) {
    try {
      const result = await this.mcpClient.callTool('create_task', {
        content: analysis.title,
        description: `생성된 작업: ${analysis.content}`
      });
      
      return {
        type: 'task_created',
        message: `✅ 작업이 생성되었습니다: "${analysis.title}"`,
        result: result
      };
    } catch (error) {
      throw new Error(`작업 생성 실패: ${error.message}`);
    }
  }

  // 작업 목록 조회
  async listTasks(analysis) {
    try {
      const result = await this.mcpClient.callTool('get_today_tasks');
      
      return {
        type: 'task_list',
        message: '📋 오늘의 할일 목록',
        result: result
      };
    } catch (error) {
      throw new Error(`작업 목록 조회 실패: ${error.message}`);
    }
  }

  // 프로젝트 조회
  async getProjects() {
    try {
      const result = await this.mcpClient.callTool('get_projects');
      
      return {
        type: 'project_list',
        message: '📁 프로젝트 목록',
        result: result
      };
    } catch (error) {
      throw new Error(`프로젝트 조회 실패: ${error.message}`);
    }
  }

  // 연결 테스트
  async testConnection() {
    try {
      // 간단한 도구 목록 호출로 연결 테스트
      const result = await this.mcpClient.listTools();
      
      return {
        type: 'connection_test',
        message: '🔗 연결 테스트 성공',
        result: { message: 'MCP 서버와 성공적으로 연결되었습니다', tools: result }
      };
    } catch (error) {
      throw new Error(`연결 테스트 실패: ${error.message}`);
    }
  }

  // 연결 해제
  disconnect() {
    // 공유된 클라이언트이므로 여기서 연결을 끊지 않음
    this.isConnected = false;
  }
}

module.exports = { ScheduleAgentService }; 