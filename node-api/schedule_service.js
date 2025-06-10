// schedule_service.js - Smart Schedule Agent Service

class ScheduleAgentService {
  constructor(mcpClient = null) {
    this.mcpClient = mcpClient;  // Accept external MCP client
    this.isConnected = false;
  }

  // Set MCP client
  setMcpClient(mcpClient) {
    this.mcpClient = mcpClient;
  }

  // Ensure MCP connection
  async ensureConnection() {
    if (!this.mcpClient) {
      throw new Error('MCP client is not configured');
    }

    if (!this.isConnected) {
      try {
        // Attempt connection if client is not yet connected
        if (!this.mcpClient.isConnected()) {
          await this.mcpClient.connect();
        }
        this.isConnected = true;
        console.log('MCP connection confirmed');
      } catch (error) {
        console.error('MCP connection failed:', error.message);
        throw new Error('FastMCP server is not ready');
      }
    }
  }

  // Process message
  async processMessage(message) {
    console.log('Processing schedule message:', message);
    
    try {
      await this.ensureConnection();
      
      // Analyze message and determine action
      const analysis = this.analyzeMessage(message);
      console.log('Message analysis result:', analysis);
      
      let result = {};
      
      // Process based on action type
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
            message: `I understood your message: "${message}". Please request specific actions.`
          };
      }
      
      return result;
    } catch (error) {
      console.error('Message processing error:', error);
      return {
        type: 'error',
        message: `An error occurred during processing: ${error.message}`
      };
    }
  }

  // Analyze message
  analyzeMessage(message) {
    const lowerMessage = message.toLowerCase();
    
    // Task creation related keywords
    if (lowerMessage.includes('할일') || lowerMessage.includes('task') || 
        lowerMessage.includes('추가') || lowerMessage.includes('만들') ||
        lowerMessage.includes('생성') || lowerMessage.includes('create') ||
        lowerMessage.includes('add')) {
      return {
        type: 'create_task',
        content: message,
        title: this.extractTaskTitle(message)
      };
    }
    
    // List query related keywords
    if (lowerMessage.includes('목록') || lowerMessage.includes('리스트') ||
        lowerMessage.includes('list') || lowerMessage.includes('보여') ||
        lowerMessage.includes('show')) {
      return {
        type: 'list_tasks'
      };
    }
    
    // Project query
    if (lowerMessage.includes('프로젝트') || lowerMessage.includes('project')) {
      return {
        type: 'get_projects'
      };
    }
    
    // Connection test
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

  // Extract task title
  extractTaskTitle(message) {
    // Simple task title extraction logic
    let title = message;
    
    // Remove unnecessary words
    const wordsToRemove = ['할일', '작업', '추가', '만들어', '생성', '해줘', '주세요', 'task', 'create', 'add'];
    wordsToRemove.forEach(word => {
      title = title.replace(new RegExp(word, 'gi'), '');
    });
    
    return title.trim() || 'New task';
  }

  // Create task
  async createTask(analysis) {
    try {
      const result = await this.mcpClient.callTool('create_task', {
        content: analysis.title,
        description: `Created task: ${analysis.content}`
      });
      
      return {
        type: 'task_created',
        message: `Task created: "${analysis.title}"`,
        result: result
      };
    } catch (error) {
      throw new Error(`Task creation failed: ${error.message}`);
    }
  }

  // List tasks
  async listTasks(analysis) {
    try {
      const result = await this.mcpClient.callTool('get_today_tasks');
      
      return {
        type: 'task_list',
        message: 'Today\'s task list',
        result: result
      };
    } catch (error) {
      throw new Error(`Task list query failed: ${error.message}`);
    }
  }

  // Get projects
  async getProjects() {
    try {
      const result = await this.mcpClient.callTool('get_projects');
      
      return {
        type: 'project_list',
        message: 'Project list',
        result: result
      };
    } catch (error) {
      throw new Error(`Project query failed: ${error.message}`);
    }
  }

  // Test connection
  async testConnection() {
    try {
      // Test connection with simple tool list call
      const result = await this.mcpClient.listTools();
      
      return {
        type: 'connection_test',
        message: 'Connection test successful',
        result: { message: 'Successfully connected to MCP server', tools: result }
      };
    } catch (error) {
      throw new Error(`Connection test failed: ${error.message}`);
    }
  }

  // Disconnect
  disconnect() {
    if (this.mcpClient) {
      this.mcpClient.disconnect();
    }
    this.isConnected = false;
  }
}

module.exports = { ScheduleAgentService }; 