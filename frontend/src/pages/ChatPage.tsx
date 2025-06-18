import { useState, useRef, useEffect, useCallback } from "react";
import { 
  Home, Image, Heart, User, Send, Phone, Settings, Mic, Camera, Volume2, 
  Search, Calendar, CheckSquare, Plus, X, Clock, Tag, Flag, ChevronDown, 
  ChevronRight, Loader2, RefreshCw 
} from "lucide-react";
import todoistAPI from '../config/api';
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  time: string;
  image?: string;
  voice?: string;
  messageType?: "chat" | "search" | "schedule" | "todoist";
}

interface TodoistTask {
  id: string;
  content: string;
  description?: string;
  project_id?: string;
  section_id?: string;
  parent_id?: string;
  order: number;
  priority: number;
  due?: {
    date: string;
    datetime?: string;
    string: string;
    timezone?: string;
  };
  labels: string[];
  created_at: string;
  completed_at?: string;
  url: string;
}

interface TodoistProject {
  id: string;
  name: string;
  color: string;
  parent_id?: string;
  order: number;
  is_favorite: boolean;
  is_inbox_project: boolean;
  view_style: string;
}

interface ProcessedEvent {
  title: string;
  data: string;
}

interface SearchStreamMessage {
  type: "human" | "ai";
  content: string;
  id: string;
}

interface ChatState {
  userMbti: string;
  relationshipType: string;
  aiName: string;
  currentEmotion: string;
  aiPersona?: string;
  aiMbti?: string;
}

// Custom hook for search streaming
const useSearchStream = (config: {
  apiUrl: string;
  onUpdateEvent: (event: any) => void;
  onFinish: (event: any) => void;
}) => {
  const [messages, setMessages] = useState<SearchStreamMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const submit = useCallback(async (params: {
    messages: SearchStreamMessage[];
    initial_search_query_count: number;
    max_research_loops: number;
    reasoning_model: string;
  }) => {
    setIsLoading(true);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${config.apiUrl}/api/search/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: params.messages,
          initial_search_query_count: params.initial_search_query_count,
          max_research_loops: params.max_research_loops,
          reasoning_model: params.reasoning_model,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error('Search request failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'update') {
                  config.onUpdateEvent(data.event);
                } else if (data.type === 'message') {
                  const newMessage: SearchStreamMessage = {
                    type: 'ai',
                    content: data.content,
                    id: Date.now().toString(),
                  };
                  setMessages(prev => [...prev, newMessage]);
                } else if (data.type === 'finish') {
                  config.onFinish(data);
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Search stream error:', error);
        
        if (error.message && error.message.includes('429')) {
          const quotaErrorMessage: SearchStreamMessage = {
            type: 'ai',
            content: '⚠️ Google API 할당량이 한도에 도달했습니다. 잠시 후 다시 시도해 주세요. (오류 코드: 429 RESOURCE_EXHAUSTED)',
            id: Date.now().toString(),
          };
          setMessages(prev => [...prev, quotaErrorMessage]);
        } else {
          const errorMessage: SearchStreamMessage = {
            type: 'ai',
            content: `⚠️ 검색 요청 실패: ${error.message || '알 수 없는 오류'}`,
            id: Date.now().toString(),
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [config]);

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  }, []);

  return { messages, isLoading, submit, stop };
};

// Todoist Panel Component
const TodoistPanel = ({ 
  onClose, 
  onSendMessage 
}: { 
  onClose: () => void; 
  onSendMessage: (message: string, type: "todoist") => void 
}) => {
  const [tasks, setTasks] = useState<TodoistTask[]>([]);
  const [projects, setProjects] = useState<TodoistProject[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [newTaskInput, setNewTaskInput] = useState("");
  const [selectedPriority, setSelectedPriority] = useState(4);
  const [selectedDate, setSelectedDate] = useState("");
  const [mcpConnected, setMcpConnected] = useState(false);
  const [connectionError, setConnectionError] = useState("");

  const connectToMCP = async () => {
    setLoading(true);
    setConnectionError("");
    
    try {
      await todoistAPI.connect();
      setMcpConnected(true);
      
      await loadProjects();
      await loadTasks();
    } catch (error) {
      console.error('MCP 연결 오류:', error);
      setConnectionError('Todoist MCP 서버에 연결할 수 없습니다.');
      setMcpConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const data = await todoistAPI.getProjects();
      setProjects(data.projects || []);
    } catch (error) {
      console.error('프로젝트 로드 오류:', error);
    }
  };

  const loadTasks = async (projectId?: string) => {
    setLoading(true);
    try {
      const data = await todoistAPI.getTasks(projectId, undefined);
      setTasks(data.tasks || []);
    } catch (error) {
      console.error('태스크 로드 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const addTask = async () => {
    if (!newTaskInput.trim()) return;

    try {
      const taskData = {
        content: newTaskInput,
        project_id: selectedProject,
        priority: selectedPriority,
        due_date: selectedDate || undefined,
      };

      await todoistAPI.createTask(taskData);
      
      setNewTaskInput("");
      setSelectedPriority(4);
      setSelectedDate("");
      
      await loadTasks(selectedProject || undefined);
      
      onSendMessage(`새 태스크 "${newTaskInput}"를 추가했습니다.`, "todoist");
    } catch (error) {
      console.error('태스크 추가 오류:', error);
    }
  };

  const completeTask = async (taskId: string, taskContent: string) => {
    try {
      await todoistAPI.completeTask(taskId);
      
      setTasks(tasks.filter(task => task.id !== taskId));
      
      onSendMessage(`태스크 "${taskContent}"를 완료했습니다! 🎉`, "todoist");
    } catch (error) {
      console.error('태스크 완료 오류:', error);
    }
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 1: return "text-red-500";
      case 2: return "text-orange-500";
      case 3: return "text-blue-500";
      default: return "text-gray-500";
    }
  };

  useEffect(() => {
    connectToMCP();
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckSquare className="h-6 w-6 text-red-500" />
            <h2 className="text-xl font-semibold">Todoist 일정 관리</h2>
            {mcpConnected && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                MCP 연결됨
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Connection Error */}
        {connectionError && (
          <div className="p-4 bg-red-100 text-red-700 text-sm">
            {connectionError}
            <button
              onClick={connectToMCP}
              className="ml-2 underline hover:no-underline"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar - Projects */}
          <div className="w-64 border-r bg-gray-50 p-4 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">프로젝트</h3>
              <button
                onClick={() => {
                  setSelectedProject(null);
                  loadTasks();
                }}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                  selectedProject === null ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
                }`}
              >
                <span className="flex items-center gap-2">
                  <CheckSquare className="h-4 w-4" />
                  모든 태스크
                </span>
              </button>
            </div>
            
            <div className="space-y-1">
              {projects.map(project => (
                <div key={project.id}>
                  <button
                    onClick={() => {
                      setSelectedProject(project.id);
                      loadTasks(project.id);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between ${
                      selectedProject === project.id ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: project.color }}
                      />
                      {project.name}
                    </span>
                    {project.is_favorite && <Heart className="h-3 w-3 fill-current" />}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Task List */}
          <div className="flex-1 p-6 overflow-y-auto">
            {/* Add Task */}
            <div className="mb-6 bg-gray-50 p-4 rounded-lg">
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={newTaskInput}
                  onChange={(e) => setNewTaskInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      addTask();
                    }
                  }}
                  placeholder="새 태스크 추가..."
                  className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={addTask}
                  disabled={!newTaskInput.trim()}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              
              <div className="flex gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <Flag className={`h-4 w-4 ${getPriorityColor(selectedPriority)}`} />
                  <select
                    value={selectedPriority}
                    onChange={(e) => setSelectedPriority(Number(e.target.value))}
                    className="border rounded px-2 py-1"
                  >
                    <option value={1}>우선순위 1</option>
                    <option value={2}>우선순위 2</option>
                    <option value={3}>우선순위 3</option>
                    <option value={4}>우선순위 4</option>
                  </select>
                </div>
                
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-500" />
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="border rounded px-2 py-1"
                  />
                </div>
              </div>
            </div>

            {/* Task List */}
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : tasks.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckSquare className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>태스크가 없습니다</p>
              </div>
            ) : (
              <div className="space-y-2">
                {tasks.map(task => (
                  <div
                    key={task.id}
                    className="flex items-start gap-3 p-3 bg-white border rounded-lg hover:shadow-sm transition-shadow"
                  >
                    <button
                      onClick={() => completeTask(task.id, task.content)}
                      className="mt-1 w-5 h-5 rounded-full border-2 border-gray-300 hover:border-green-500 flex items-center justify-center group"
                    >
                      <div className="w-3 h-3 rounded-full bg-green-500 scale-0 group-hover:scale-100 transition-transform" />
                    </button>
                    
                    <div className="flex-1">
                      <p className="text-gray-800">{task.content}</p>
                      {task.description && (
                        <p className="text-sm text-gray-500 mt-1">{task.description}</p>
                      )}
                      
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        {task.due && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {task.due.string}
                          </span>
                        )}
                        {task.labels.length > 0 && (
                          <span className="flex items-center gap-1">
                            <Tag className="h-3 w-3" />
                            {task.labels.join(', ')}
                          </span>
                        )}
                        <Flag className={`h-3 w-3 ${getPriorityColor(task.priority)}`} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Refresh Button */}
            <button
              onClick={() => loadTasks(selectedProject || undefined)}
              className="mt-4 flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
            >
              <RefreshCw className="h-4 w-4" />
              새로고침
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Chat Interface Component
const ChatInterface = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioStreamRef = useRef<MediaStream | null>(null);
  
  // 통합된 상태 관리
  const [chatState, setChatState] = useState<ChatState>({
    userMbti: "",
    relationshipType: "",
    aiName: "",
    currentEmotion: "neutral"
  });
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [showTodoistPanel, setShowTodoistPanel] = useState(false);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [showCameraPreview, setShowCameraPreview] = useState(false);
  const [cameraStreamUrl, setCameraStreamUrl] = useState("");
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<ProcessedEvent[]>([]);
  const [searchEffort, setSearchEffort] = useState<"low" | "medium" | "high">("medium");
  const [capturedImageBlob, setCapturedImageBlob] = useState<Blob | null>(null);

  // Custom search stream hook
  const searchStream = useSearchStream({
    apiUrl: "http://localhost:8181",
    onFinish: (event: any) => {
      console.log("Search finished:", event);
    },
    onUpdateEvent: (event: any) => {
      let processedEvent: ProcessedEvent | null = null;
      if (event.generate_query) {
        processedEvent = {
          title: "검색 쿼리 생성 중",
          data: event.generate_query.query_list.join(", "),
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "웹 리서치",
          data: `${numSources}개의 소스 수집. 관련 주제: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "검토 중",
          data: event.reflection.is_sufficient
            ? "검색 성공, 최종 답변 생성 중."
            : `더 많은 정보 필요, 추가 검색: ${event.reflection.follow_up_queries.join(
                ", "
              )}`,
        };
      } else if (event.finalize_answer) {
        processedEvent = {
          title: "답변 완성",
          data: "최종 답변을 작성하고 있습니다.",
        };
      }
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
  });
  
  // URL 파라미터 처리
  useEffect(() => {
    const params = {
      userMbti: searchParams.get('user_mbti') || "ENFP",
      relationshipType: searchParams.get('relationship_type') || "동질적 관계",
      aiName: searchParams.get('ai_name') || "AI 친구",
      currentEmotion: "neutral"
    };
    
    setChatState(params);

    // Fetch MBTI persona from backend API
    const fetchMBTIPersona = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8181'}/api/mbti/persona`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_mbti: params.userMbti,
            relationship_type: params.relationshipType,
            ai_name: params.aiName
          })
        });

        if (!response.ok) {
          throw new Error('MBTI 페르소나를 가져오는데 실패했습니다');
        }

        const mbtiData = await response.json();
        
        setMessages([
          {
            id: "init-ai-message",
            sender: "ai",
            text: mbtiData.initial_message,
            time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
            messageType: "chat"
          }
        ]);

        setChatState(prev => ({
          ...prev,
          aiPersona: mbtiData.ai_persona,
          aiMbti: mbtiData.ai_mbti
        }));

      } catch (error) {
        console.error('MBTI 페르소나 로딩 실패:', error);
        const fallbackMessage = `안녕하세요, ${params.aiName}입니다. 당신의 MBTI가 ${params.userMbti}이고, 우리는 ${params.relationshipType}(으)로 설정되었네요. 만나서 반갑습니다! 앞으로 어떤 이야기를 나눠볼까요?`;
        
        setMessages([
          {
            id: "init-ai-message",
            sender: "ai",
            text: fallbackMessage,
            time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
            messageType: "chat"
          }
        ]);
      }
    };

    fetchMBTIPersona();
  }, [searchParams]);

  // 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 시작 녹음
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
    } catch (err) {
      toast.error("마이크를 사용할 수 없습니다");
    }
  };

  // 녹음 중지
  const stopRecording = (): Promise<Blob> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder) return resolve(new Blob());

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        resolve(audioBlob);
      };

      recorder.stop();

      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track) => track.stop());
        audioStreamRef.current = null;
      }
    });
  };

  // 카메라 스트림 정리 함수
  const cleanupCameraStream = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => {
        track.stop();
      });
      videoRef.current.srcObject = null;
    }
    setIsCapturing(false);
    setShowCameraPreview(false);
  };

  // 시작 카메라 (재시도 로직 포함)
  const startCamera = async (retryCount = 0) => {
    const MAX_RETRIES = 2;
    
    try {
      // Check if we're on HTTP and not localhost
      if (window.location.protocol === 'http:' && !window.location.hostname.match(/localhost|127\.0\.0\.1/)) {
        toast.error("보안 설정으로 인해 카메라에 접근할 수 없습니다. HTTPS를 사용하거나 localhost에서 실행해주세요.");
        return;
      }

      // 기존 스트림 정리
      cleanupCameraStream();
      
      setIsCapturing(true);
      setShowCameraPreview(true);

      let stream;
      const constraints = [
        // 1. Try with ideal settings first
        {
          video: { 
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user'
          } 
        },
        // 2. Try with just facingMode
        {
          video: { facingMode: 'user' }
        },
        // 3. Try with any available camera
        { video: true }
      ];

      let lastError;
      
      // Try each constraint in order until one works
      for (const constraint of constraints) {
        try {
          stream = await navigator.mediaDevices.getUserMedia(constraint);
          if (stream) break;
        } catch (err) {
          console.warn(`Camera access failed with constraints:`, constraint, err);
          lastError = err;
          // Wait a bit before trying the next constraint
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      }
      
      if (!stream) {
        throw lastError || new Error('카메라 스트림을 가져올 수 없습니다.');
      }

      if (!videoRef.current) {
        throw new Error('비디오 요소를 찾을 수 없습니다.');
      }

      // Set the stream and wait for it to be ready
      videoRef.current.srcObject = stream;
      
      // Wait for the video to be ready to play
      await new Promise<void>((resolve, reject) => {
        if (!videoRef.current) return reject(new Error('비디오 요소를 찾을 수 없습니다.'));
        
        const onCanPlay = () => {
          videoRef.current?.removeEventListener('canplay', onCanPlay);
          videoRef.current?.removeEventListener('error', onError);
          resolve();
        };
        
        const onError = (err: Event) => {
          videoRef.current?.removeEventListener('canplay', onCanPlay);
          videoRef.current?.removeEventListener('error', onError);
          reject(new Error(`비디오 재생 오류: ${err}`));
        };
        
        videoRef.current.addEventListener('canplay', onCanPlay, { once: true });
        videoRef.current.addEventListener('error', onError, { once: true });
        
        // Start playing the video
        videoRef.current.play().catch(reject);
      });
      
      // If we get here, video is playing successfully
      return;
      
      // 카메라가 정상적으로 시작되었을 때만 상태 업데이트
      setIsCapturing(true);
      setShowCameraPreview(true);
      
    } catch (err: any) {
      console.error('Camera access error:', err);
      let errorMessage = '카메라에 접근할 수 없습니다';
      let showRecovery = false;
      
      if (err.name === 'NotAllowedError') {
        errorMessage = '카메라 접근 권한이 거부되었습니다. 브라우저 설정에서 카메라 권한을 확인해주세요.';
      } else if (err.name === 'NotFoundError') {
        errorMessage = '사용 가능한 카메라를 찾을 수 없습니다. 카메라가 제대로 연결되어 있는지 확인해주세요.';
        showRecovery = true;
      } else if (err.name === 'NotReadableError' || err.name === 'NotReadableError DOMException') {
        errorMessage = (
          '카메라를 사용할 수 없습니다. 다음을 확인해주세요:\n' +
          '1. 다른 애플리케이션에서 카메라를 사용 중인지 확인\n' +
          '2. 카라를 분리했다가 다시 연결\n' +
          '3. 컴퓨터를 재시작'
        );
        showRecovery = true;
      } else if (err.message.includes('Permission denied')) {
        errorMessage = '카메라 접근이 거부되었습니다. 브라우저 설정에서 권한을 확인해주세요.';
      } else {
        errorMessage = `카메라 오류: ${err.message || '알 수 없는 오류'}`;
      }
      
      // 오류 메시지 표시
      toast.error(errorMessage, {
        duration: 5000,
        style: {
          whiteSpace: 'pre-line', // 줄바꿈 적용
          maxWidth: 'none'
        }
      });
      
      // 복구 안내 버튼 추가
      if (showRecovery) {
        const showTroubleshootingGuide = () => (
          <div style={{ padding: '1rem', maxWidth: '400px' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 'bold' }}>카메라 문제 해결 방법</h3>
            <ol style={{ margin: '0.5rem 0 0 1rem', paddingLeft: '1rem' }}>
              <li style={{ marginBottom: '0.5rem' }}>다른 애플리케이션에서 카메라를 사용 중인지 확인하고 모두 종료하세요.</li>
              <li style={{ marginBottom: '0.5rem' }}>웹 브라우저를 완전히 종료했다가 다시 실행해보세요.</li>
              <li style={{ marginBottom: '0.5rem' }}>컴퓨터를 재시작해보세요.</li>
              <li style={{ marginBottom: '0.5rem' }}>브라우저 설정에서 카메라 권한을 확인하고 다시 시도해보세요.</li>
              <li>다른 카메라를 연결해보세요 (노트북의 경우 외장 카메라).</li>
            </ol>
          </div>
        );

        // 기존 토스트 닫기
        toast.dismiss();
        // 안내 메시지 표시 (React 컴포넌트로 렌더링)
        toast.custom(() => <showTroubleshootingGuide />, { duration: 10000 });
      }
      
      // 상태 초기화
      cleanupCameraStream();
    }
  };

  // 촬영 및 전송
  const capturePhoto = async () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    if (!canvas || !video) {
      toast.error("카메라를 찾을 수 없습니다");
      setIsCapturing(false);
      return;
    }

    try {
      // 캔버스에 현재 비디오 프레임 그리기
      const context = canvas.getContext("2d");
      if (!context) {
        throw new Error("캔버스 컨텍스트를 가져올 수 없습니다");
      }
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // 캔버스에서 이미지 데이터 가져오기
      const imageBlob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error("이미지 변환에 실패했습니다"));
          }
        }, "image/jpeg", 0.9); // JPEG 형식으로 압축
      });

      // 이미지 URL 생성
      const imageUrl = URL.createObjectURL(imageBlob);
      
      // 사용자 메시지 생성 (先创建临时URL用于预览)
      const userMessage: Message = {
        id: Date.now().toString(),
        sender: "user",
        text: "사진을 보냈습니다",
        time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
        image: imageUrl, // 使用本地生成的临时URL
        messageType: "chat"
      };

      // 메시지 목록에 추가
      setMessages(prev => [...prev, userMessage]);
      
      // 서버에 이미지 전송
      try {
        const formData = new FormData();
        formData.append('image', imageBlob, 'photo.jpg');
        
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8181'}/api/chat/upload`, {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          throw new Error('이미지 업로드 실패');
        }
        
        const data = await response.json();
        
        // AI 응답 메시지 추가
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          text: data.analysis || data.message || "사진을 잘 받았어요!",
          time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
          messageType: "chat"
        };
        
        // 이미지 URL이 있는 경우 업데이트
        if (data.image_url) {
          userMessage.image = `${import.meta.env.VITE_API_URL || 'http://localhost:8181'}${data.image_url}`;
          // 메시지 목록 업데이트
          setMessages(prev => {
            const newMessages = [...prev];
            const messageIndex = newMessages.findIndex(m => m.id === userMessage.id);
            if (messageIndex !== -1) {
              newMessages[messageIndex] = { ...userMessage };
            }
            return newMessages;
          });
        }
        
        setMessages(prev => [...prev, aiMessage]);
      } catch (uploadError) {
        console.error("이미지 업로드 오류:", uploadError);
        toast.error("이미지 전송에 실패했습니다");
      }
      
      // 카메라 미리보기 닫기
      stopVideoStream();
      setShowCameraPreview(false);
      
      // 사용자에게 알림
      toast.success("사진이 전송되었습니다");
      
    } catch (error) {
      console.error("사진 촬영 중 오류 발생:", error);
      toast.error(`사진 촬영에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    } finally {
      setIsCapturing(false);
    }
  };

  // 비디오 스트림 중지
  const stopVideoStream = () => {
    const video = videoRef.current;
    if (video && video.srcObject) {
      const stream = video.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      video.srcObject = null;
    }
  };

  // 카메라 중지
  const stopCamera = async () => {
    stopVideoStream();
    setShowCameraPreview(false);
    setCameraStreamUrl("");
    setIsCapturing(false);

    const audioBlob = await stopRecording();
    if (!capturedImageBlob) return;

    // 감정 분석 요청
    const formData = new FormData();
    formData.append("image", capturedImageBlob, "image.png");
    formData.append("audio", audioBlob, "audio.webm");
    formData.append("text", inputMessage);

    try {
      const res = await fetch("http://localhost:8181/api/conversation/respond", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.success) {
        // 사용자 메시지 추가
        const userMessage: Message = {
          id: Date.now().toString(),
          sender: "user",
          text: inputMessage,
          time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
          image: `${import.meta.env.VITE_API_URL || 'http://localhost:8181'}${data.image_url}`, // 拼接完整URL
          messageType: "chat"
        };
        setMessages(prev => [...prev, userMessage]);

        // AI 응답 추가
        const aiMessage: Message = {
          id: Date.now().toString(),
          sender: "ai",
          text: data.response,
          time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
          messageType: "chat"
        };
        setMessages(prev => [...prev, aiMessage]);

        setInputMessage("");
      } else if (data.mode === "search_detected") {
        toast.info("🔎 검색 질문으로 인식되었어요. 정보를 찾아볼게요...");
        await sendSearchQuery(data.text);
      } else {
        toast.error("감정 분석 실패: " + (data.error || "알 수 없는 오류"));
      }
    } catch (err) {
      console.error("감정 분석 API 오류:", err);
      toast.error("서버 통신 실패");
    }
  };

  // 검색 쿼리 전송
  const sendSearchQuery = async (queryText: string) => {
    try {
      const res = await fetch("http://localhost:8181/search/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText }),
      });

      const data = await res.json();

      if (data.success) {
        const aiMessage: Message = {
          id: Date.now().toString(),
          sender: "ai",
          text: data.response,
          time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
          messageType: "search"
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        toast.error("검색 실패: " + (data.message || "결과 없음"));
      }
    } catch (err) {
      console.error("검색 요청 오류:", err);
      toast.error("검색 요청 실패");
    }
  };

  // TTS 재생
  const playTTS = useCallback(async (text: string) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8181'}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      
      if (!response.ok) throw new Error('TTS 변환 실패');
      
      const audioBlob = await response.blob();
      const audio = new Audio(URL.createObjectURL(audioBlob));
      audio.onended = () => URL.revokeObjectURL(audio.src);
      await audio.play();
    } catch (error) {
      console.error('음성 재생 실패:', error);
    }
  }, []);

  // 메시지 전송
  const handleSendMessage = useCallback(async (messageText?: string, messageType: "chat" | "search" | "schedule" | "todoist" = "chat") => {
    const textToSend = messageText || inputMessage.trim();
    if (!textToSend) return;

    // 사용자 메시지 추가
    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: textToSend,
      time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
      messageType
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");

    try {
      if (messageType === "search" || isSearchMode) {
        // 검색 모드 처리
        const searchMessages = [
          ...searchStream.messages,
          { type: "human" as const, content: textToSend, id: Date.now().toString() }
        ];

        await searchStream.submit({
          messages: searchMessages,
          initial_search_query_count: searchEffort === "low" ? 1 : searchEffort === "medium" ? 2 : 3,
          max_research_loops: searchEffort === "low" ? 1 : searchEffort === "medium" ? 2 : 3,
          reasoning_model: "gpt-4o-mini"
        });
      } else if (messageType === "schedule") {
        // 일정 관리 처리
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8181'}/api/schedule/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: "user123",
            text: textToSend
          })
        });

        const data = await response.json();
        if (data?.response) {
          const aiMessage: Message = {
            id: Date.now().toString(),
            sender: "ai",
            text: data.response,
            time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
            messageType: "schedule"
          };
          setMessages(prev => [...prev, aiMessage]);
        } else {
          toast.error("일정 처리 중 오류가 발생했습니다.");
        }
      } else {
        // 일반 채팅 처리
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8181'}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [
              {
                role: "user",
                content: textToSend
              }
            ],
            user_id: "user123",
            ai_id: "ai456",
            ai_persona: chatState.aiPersona,
            ai_mbti: chatState.aiMbti,
            user_mbti: chatState.userMbti,
            relationship_type: chatState.relationshipType
          })
        });

        const data = await response.json();
        if (data?.response) {
          const aiMessage: Message = {
            id: Date.now().toString(),
            sender: "ai",
            text: data.response,
            time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
            messageType: "chat"
          };
          setMessages(prev => [...prev, aiMessage]);
        } else {
          toast.error("응답을 생성하는데 문제가 발생했습니다.");
        }
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      toast.error("메시지 전송 중 오류가 발생했습니다. 다시 시도해주세요.");
    }
  }, [inputMessage, isSearchMode, searchStream, searchEffort, chatState]);

  // 新增：上传已有照片
  const handleUploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('image', file, file.name);

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8181'}/api/chat/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('이미지 업로드 실패');
      }

      const data = await response.json();

      // 用户消息
      const userMessage: Message = {
        id: Date.now().toString(),
        sender: "user",
        text: "사진을 보냈습니다",
        time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
        image: `${import.meta.env.VITE_API_URL || 'http://localhost:8181'}${data.image_url}`, // 拼接完整URL
        messageType: "chat"
      };
      setMessages(prev => [...prev, userMessage]);

      // AI 回复
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: data.response || "사진을 잘 받았어요!",
        time: new Date().toLocaleTimeString("ko-KR", { hour: 'numeric', minute: '2-digit', hour12: true }),
        messageType: "chat"
      };
      setMessages(prev => [...prev, aiMessage]);

      toast.success("사진이 업로드되었습니다");
      setShowCameraPreview(false);
    } catch (error) {
      console.error("이미지 업로드 오류:", error);
      toast.error("이미지 업로드에 실패했습니다");
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Search Activity Panel */}
      {isSearchMode && processedEventsTimeline.length > 0 && (
        <div className="fixed top-16 right-4 w-80 bg-white shadow-lg rounded-lg p-4 z-40 max-h-64 overflow-y-auto">
          <h3 className="font-medium text-sm mb-2">검색 활동</h3>
          <div className="space-y-2">
            {processedEventsTimeline.map((event, index) => (
              <div key={index} className="text-xs">
                <div className="font-medium text-gray-700">{event.title}</div>
                <div className="text-gray-500">{event.data}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Todoist Panel */}
      {showTodoistPanel && (
        <TodoistPanel 
          onClose={() => setShowTodoistPanel(false)}
          onSendMessage={handleSendMessage}
        />
      )}

      {/* Camera Preview */}
      {showCameraPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg max-w-md w-full">
            <div className="text-center mb-4">
              <h3 className="text-lg font-medium">카메라 미리보기</h3>
              <p className="text-sm text-gray-500">원하는 각도에서 사진을 촬영하세요</p>
            </div>
            <video ref={videoRef} autoPlay playsInline className="w-full h-auto rounded-lg mb-4" />
            <canvas ref={canvasRef} style={{ display: "none" }} />
            <div className="flex justify-between">
              <button 
                onClick={stopCamera}
                className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg"
              >
                취소
              </button>
              <button 
                onClick={capturePhoto}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
              >
                사진 촬영
              </button>
              <label className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg cursor-pointer">
                사진 업로드
                <input
                  type="file"
                  accept="image/*"
                  style={{ display: "none" }}
                  onChange={handleUploadPhoto}
                />
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Header */}
        <header className="px-4 py-3 border-b bg-white flex items-center justify-between">
          <div className="flex items-center">
            <Avatar className="h-10 w-10">
              <img src="/example_avatar_profile.png" alt="AI Avatar" className="rounded-full" />
            </Avatar>
            <div className="ml-3">
              <h2 className="font-semibold text-gray-800">{chatState.aiName}</h2>
              <p className="text-xs text-gray-500">
                {isSearchMode ? "검색 모드 🔍" : "활동중 상태"}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setIsSearchMode(!isSearchMode)} 
              className={`p-2 rounded-full transition duration-300 ease-in-out ${
                isSearchMode 
                  ? 'bg-purple-100 text-purple-600' 
                  : 'hover:bg-gray-100 text-gray-500'
              }`}
              title="검색 모드 전환"
            >
              <Search className="h-5 w-5" />
            </button>
            {isSearchMode && (
              <select
                value={searchEffort}
                onChange={(e) => setSearchEffort(e.target.value as "low" | "medium" | "high")}
                className="text-xs px-2 py-1 border rounded-md"
              >
                <option value="low">빠른 검색</option>
                <option value="medium">일반 검색</option>
                <option value="high">심층 검색</option>
              </select>
            )}
            <button 
              onClick={() => setShowTodoistPanel(true)}
              className="p-2 rounded-full hover:bg-green-100 transition duration-300 ease-in-out relative"
              title="일정 관리"
            >
              <Calendar className="h-5 w-5 text-green-600" />
            </button>
            <button 
              className="p-2 rounded-full hover:bg-blue-100 transition duration-300 ease-in-out"
              title="음성 통화"
            >
              <Phone className="h-5 w-5 text-blue-600" />
            </button>
            <button className="p-2 rounded-full hover:bg-gray-100">
              <Settings className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(message => (
            <div key={message.id} className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
              {message.sender === "ai" && (
                <Avatar className="h-8 w-8 mr-2 mt-1">
                  <img src="/example_avatar_profile.png" alt="AI Avatar" className="rounded-full" />
                </Avatar>
              )}
              <div className={`max-w-[70%] ${
                message.sender === "user" 
                  ? "bg-blue-500 text-white" 
                  : message.messageType === "search" 
                    ? "bg-purple-100 text-gray-800" 
                    : message.messageType === "todoist"
                    ? "bg-green-100 text-gray-800"
                    : "bg-gray-100 text-gray-800"
              } rounded-2xl px-4 py-2 ${message.sender === "user" ? "rounded-tr-sm" : "rounded-tl-sm"}`}>
                {message.messageType === "todoist" && message.sender === "user" && (
                  <div className="flex items-center mb-1">
                    <CheckSquare className="h-3 w-3 mr-1" />
                    <span className="text-xs font-medium opacity-75">Todoist</span>
                  </div>
                )}
                {message.messageType === "search" && message.sender === "user" && (
                  <div className="flex items-center mb-1">
                    <Search className="h-3 w-3 mr-1" />
                    <span className="text-xs font-medium opacity-75">검색 요청</span>
                  </div>
                )}
                {message.image && (
                  <div className="mb-2">
                    <img 
                      src={message.image} 
                      alt="사진" 
                      style={{ maxWidth: 200, borderRadius: 8 }} 
                    />
                  </div>
                )}
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</div>
                <div className="flex items-center justify-between mt-1 text-xs opacity-60">
                  {message.time}
                  {message.sender === "ai" && (
                    <button 
                      className="ml-2 p-1 hover:bg-gray-300 rounded-full"
                      onClick={() => playTTS(message.text)}
                      aria-label="음성 듣기"
                    >
                      <Volume2 className="h-4 w-4 text-gray-500" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Section */}
        <div className="p-4 bg-gray-50 border-t">
          {isSearchMode && (
            <div className="mb-2 px-2 py-1 bg-purple-100 rounded-lg text-sm text-purple-700">
              🔍 검색 모드가 활성화되었습니다. 궁금한 것을 물어보세요!
            </div>
          )}
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center bg-white border rounded-full">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isSearchMode ? "검색할 내용을 입력하세요..." : "메시지를 입력하세요..."}
                className="flex-1 px-4 py-2 bg-transparent focus:outline-none text-sm"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <button 
                className={`p-2 rounded-full transition-all duration-300 ${
                  isSearchMode 
                    ? 'bg-purple-100 text-purple-600' 
                    : 'hover:bg-gray-100 text-gray-500'
                }`}
                onClick={() => setIsSearchMode(!isSearchMode)}
                title="검색 모드 전환"
              >
                <Search className="h-5 w-5" />
              </button>
              <button 
                className="p-2 hover:bg-gray-100 rounded-full mr-1"
                title="음성 메시지"
              >
                <Mic className="h-5 w-5 text-gray-500" />
              </button>
              <button 
                className="p-2 hover:bg-gray-100 rounded-full mr-1"
                onClick={(e) => {
                  e.preventDefault();
                  startCamera().catch(err => {
                    console.error('카메라 시작 중 오류 발생:', err);
                    toast.error('카메라를 시작하는 중 오류가 발생했습니다.');
                  });
                }}
                disabled={isCapturing}
                title="사진 전송"
              >
                <Camera className="h-5 w-5 text-gray-500" />
              </button>
            </div>
            <button 
              onClick={() => handleSendMessage()} 
              className={`shrink-0 h-10 w-10 rounded-full ${
                isSearchMode 
                  ? 'bg-purple-500 hover:bg-purple-600' 
                  : 'bg-blue-500 hover:bg-blue-600'
              } text-white flex items-center justify-center transition-colors`}
              disabled={!inputMessage.trim() || (isSearchMode && searchStream.isLoading)}
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Bottom Navigation */}
        <nav className="px-4 py-2 grid grid-cols-4 border-t bg-white">
          <button className="flex flex-col items-center justify-center py-2 text-blue-600">
            <Home className="h-6 w-6" />
            <span className="text-[10px] mt-1">홈</span>
          </button>
          <button className="flex flex-col items-center justify-center py-2 text-gray-400">
            <Image className="h-6 w-6" />
            <span className="text-[10px] mt-1">앨범</span>
          </button>
          <button className="flex flex-col items-center justify-center py-2 text-gray-400">
            <Heart className="h-6 w-6" />
            <span className="text-[10px] mt-1">추억</span>
          </button>
          <button className="flex flex-col items-center justify-center py-2 text-gray-400">
            <User className="h-6 w-6" />
            <span className="text-[10px] mt-1">프로필</span>
          </button>
        </nav>
      </div>
    </div>
  );
};

export default ChatInterface;
