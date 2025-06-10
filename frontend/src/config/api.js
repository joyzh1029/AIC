// EventSource polyfill for better browser compatibility
let EventSourcePolyfill;
try {
  // 원생 EventSource 사용 
  if (typeof EventSource !== 'undefined') {
    EventSourcePolyfill = EventSource;
    console.log('✅ 원생 EventSource 사용');
  } else {
    //  원생 EventSource를 사용할 수 없습니다
    console.warn('⚠️  원생 EventSource를 사용할 수 없습니다');
    EventSourcePolyfill = null;
  }
} catch (error) {
  console.warn('EventSource 초기화 오류:', error);
  EventSourcePolyfill = typeof EventSource !== 'undefined' ? EventSource : null;
}

const API_BASE_URL = import.meta.env.VITE_REACT_APP_API_URL || 'http://localhost:3001';

export const todoistAPI = {
  // Todoist 연결
  connect: async (apiToken) => {
    try {
      console.log('Todoist MCP 연결 시도 중...');
      
      const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_token: apiToken || import.meta.env.VITE_REACT_APP_TODOIST_API_TOKEN
        }),
      });
      
      if (!response.ok) {
        let errorMessage = 'Connection failed';
        try {
          const error = await response.json();
          errorMessage = error.error || error.message || errorMessage;
        } catch (parseError) {
          console.error('응답 파싱 오류:', parseError);
          errorMessage = `서버 오류 (${response.status}): ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      console.log('Todoist MCP 연결 성공:', result);
      return result;
    } catch (error) {
      console.error('Todoist 연결 오류:', error);
      throw error;
    }
  },

  // 프로젝트 목록 가져오기
  getProjects: async () => {
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/projects`);
    if (!response.ok) {
      throw new Error('프로젝트 목록 가져오기 실패');
    }
    return response.json();
  },

  // 작업 목록 가져오기
  getTasks: async (projectId, filter) => {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (filter) params.append('filter', filter);
    
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/tasks?${params}`);
    if (!response.ok) {
      throw new Error('작업 목록 가져오기 실패');
    }
    return response.json();
  },

  // 작업 생성
  createTask: async (taskData) => {
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(taskData),
    });
    
    if (!response.ok) {
      throw new Error('작업 생성 실패');
    }
    return response.json();
  },

  // 작업 완료
  completeTask: async (taskId) => {
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/tasks/${taskId}/complete`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error('작업 완료 실패');
    }
    return response.json();
  },

  // 작업 업데이트
  updateTask: async (taskId, updates) => {
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/tasks/${taskId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    
    if (!response.ok) {
      throw new Error('작업 업데이트 실패');
    }
    return response.json();
  },

  // 작업 삭제
  deleteTask: async (taskId) => {
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/tasks/${taskId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error('작업 삭제 실패');
    }
    return response.json();
  },

  // 오늘의 작업 리소스 가져오기
  getTodayTasks: async () => {
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/resources/today`);
    if (!response.ok) {
      throw new Error('Failed to fetch today tasks');
    }
    return response.json();
  },

  // 프로젝트 작업 리소스 가져오기
  getProjectTasks: async (projectName) => {
    const response = await fetch(`${API_BASE_URL}/api/mcp/todoist/resources/projects/${encodeURIComponent(projectName)}`);
    if (!response.ok) {
      throw new Error('프로젝트 작업 리소스 가져오기 실패');
    }
    return response.json();
  }
};

export default todoistAPI;
