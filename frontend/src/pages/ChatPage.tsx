import { useState, useRef, useEffect, useCallback } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Home, Image as ImageIcon, Heart, User, Send, Phone, Settings, Mic, Camera, Volume2 } from "lucide-react";
import { toast } from "sonner";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  time: string;
  image?: string;
  voice?: string;
}

interface ChatState {
  userMbti: string;
  relationshipType: string;
  aiName: string;
  currentEmotion: string;
}

const ChatPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // 상태 통합
  const [chatState, setChatState] = useState<ChatState>({
    userMbti: "",
    relationshipType: "",
    aiName: "",
    currentEmotion: "neutral"
  });
  
  const [messages, setMessages] = useState<Message[]>([{
    id: "1",
    sender: "ai",
    text: "안녕, 만나서 반가워! 나는 너의 AI 친구야. 어떻게 지내고 있어?",
    time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
  }]);
  
  const [inputMessage, setInputMessage] = useState("");
  const [isCapturing, setIsCapturing] = useState(false);
  const [showCameraPreview, setShowCameraPreview] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // URL 파라미터 처리
  useEffect(() => {
    const params = {
      userMbti: searchParams.get('user_mbti') || "ENFP", // 기본값 추가
      relationshipType: searchParams.get('relationship_type') || "동질적 관계", // 기본값 추가
      aiName: searchParams.get('ai_name') || "AI 친구",
      currentEmotion: "neutral"
    };
    
    // 검증 로직 제거하고 기본값으로 설정
    setChatState(params);
  }, [searchParams]);
  // useEffect(() => {
  //   const params = {
  //     userMbti: searchParams.get('user_mbti') || "",
  //     relationshipType: searchParams.get('relationship_type') || "",
  //     aiName: searchParams.get('ai_name') || "AI 친구",
  //     currentEmotion: "neutral"
  //   };
    
  //   if (!params.userMbti || !params.relationshipType) {
  //     toast.error("MBTI 정보가 필요합니다.");
  //     navigate('/select-mbti');
  //     return;
  //   }
    
  //   setChatState(params);
  // }, [searchParams, navigate]);

  // 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // API 호출 헬퍼 함수
  const apiCall = useCallback(async (endpoint: string, data?: any) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        ...(data && { body: JSON.stringify(data) })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `요청 실패: ${endpoint}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API 호출 실패 (${endpoint}):`, error);
      throw error;
    }
  }, []);

  // 메시지 추가 헬퍼
  const addMessage = useCallback((text: string, sender: "user" | "ai", extra?: Partial<Message>) => {
    const message: Message = {
      id: Date.now().toString(),
      sender,
      text,
      time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
      ...extra
    };
    setMessages(prev => [...prev, message]);
    return message;
  }, []);

  const addSplitMessages = useCallback((response: string, sender: "user" | "ai", delay: number = 1000) => {
    const parts = response.split('[분할]').map(part => part.trim()).filter(part => part.length > 0);
  
    parts.forEach((part, index) => {
      setTimeout(() => {
        addMessage(part, sender);
      }, index * delay);
    });
  }, [addMessage]);

  // 카메라 제어
  const toggleCamera = useCallback(async () => {
    if (isCapturing) {
      await apiCall('/api/camera/stop');
      setShowCameraPreview(false);
      setIsCapturing(false);
    } else {
      setIsCapturing(true);
      toast.info('카메라 준비 중...');
      await apiCall('/api/camera/start');
      setShowCameraPreview(true);
    }
  }, [isCapturing, apiCall]);

  // 사진 촬영
  const capturePhoto = useCallback(async () => {
    try {
      const data = await apiCall('/api/camera/capture');
      
      if (data.success) {
        addMessage("[사진을 전송했습니다]", "user", { image: data.image });
        
        if (data.emotion) {
          setChatState(prev => ({ ...prev, currentEmotion: data.emotion }));
        }
        
        // AI 응답 요청
        const chatData = await apiCall('/api/chat', {
          messages: [
            {
              role: "user",
              content: `[사진 전송 - 감정: ${data.emotion}]`,
              timestamp: Date.now() / 1000
            }
          ],
          user_id: "user123",
          ai_id: "ai_friend_001",
          user_mbti: chatState.userMbti,
          relationship_type: chatState.relationshipType,
          ai_name: chatState.aiName,
          context: { emotion: data.emotion }
        });
        
        // [분할] 처리
        if (chatData.response && chatData.response.includes('[분할]')) {
          addSplitMessages(chatData.response, "ai");
        } else {
          addMessage(chatData.response || "응답을 받지 못했습니다.", "ai");
        }
        
        await toggleCamera();
      }
    } catch (error) {
      toast.error('사진 촬영에 실패했습니다.');
    }
  }, [apiCall, addMessage, chatState, toggleCamera, addSplitMessages]);

  // 메시지 전송
  const handleSendMessage = useCallback(async () => {
    const message = inputMessage.trim();
    if (!message) return;
    
    addMessage(message, "user");
    setInputMessage("");
    
    try {
      // ✅ chat.py의 ChatRequest 구조에 맞춤
      const data = await apiCall('/api/chat', {
        messages: [
          {
            role: "user",
            content: message,
            timestamp: Date.now() / 1000
          }
        ],
        user_id: "user123",
        ai_id: "ai_friend_001",
        user_mbti: chatState.userMbti,
        relationship_type: chatState.relationshipType,
        ai_name: chatState.aiName,
        context: { emotion: chatState.currentEmotion }
      });
      
      // [분할]로 나누어서 순차적으로 메시지 추가
      if (data.response && data.response.includes('[분할]')) {
        addSplitMessages(data.response, "ai");
      } else {
        addMessage(data.response || "응답을 받지 못했습니다.", "ai");
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      toast.error('메시지 전송에 실패했습니다.');
    }
  }, [inputMessage, apiCall, chatState, addMessage, addSplitMessages]);

  // TTS 재생
  const playTTS = useCallback(async (text: string) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/tts`, {
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

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="p-4 border-b bg-white flex items-center justify-between">
          <div className="flex items-center">
            <Avatar className="h-10 w-10">
              <img src="/example_avatar_profile.png" alt="AI Avatar" />
            </Avatar>
            <div className="ml-3">
              <h2 className="font-medium">{chatState.aiName}</h2>
              <p className="text-xs text-gray-500">활동중 상태</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {[Phone, Settings].map((Icon, idx) => (
              <button key={idx} className="p-2 rounded-full hover:bg-gray-100">
                <Icon className="h-5 w-5 text-gray-500" />
              </button>
            ))}
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(({ id, sender, text, time, image }) => (
            <div key={id} className={`flex ${sender === "user" ? "justify-end" : "justify-start"}`}>
              {sender === "ai" && (
                <Avatar className="h-8 w-8 mr-2 mt-1">
                  <img src="/example_avatar_profile.png" alt="AI Avatar" />
                </Avatar>
              )}
              <div className={`max-w-[70%] ${sender === "user" ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-800"} rounded-2xl p-3 ${sender === "user" ? "rounded-tr-none" : "rounded-tl-none"}`}>
                {image && <img src={image} alt="Captured" className="rounded-lg max-w-full mb-2" />}
                <p>{text}</p>
                <span className="flex items-center justify-between mt-1 text-xs opacity-70">
                  {time}
                  {sender === "ai" && (
                    <button 
                      className="ml-2 p-1 hover:bg-gray-300 rounded-full"
                      onClick={() => playTTS(text)}
                      aria-label="음성 듣기"
                    >
                      <Volume2 className="h-4 w-4 text-gray-500" />
                    </button>
                  )}
                </span>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Camera Preview */}
        {showCameraPreview && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white p-4 rounded-lg max-w-md w-full">
              <div className="text-center mb-4">
                <h3 className="text-lg font-medium">카메라 미리보기</h3>
                <p className="text-sm text-gray-500">원하는 각도에서 사진을 촬영하세요</p>
              </div>
              <img 
                src={`${import.meta.env.VITE_API_URL}/api/camera/stream`} 
                alt="카메라 미리보기" 
                className="w-full h-auto rounded-lg mb-4"
              />
              <div className="flex justify-between">
                <Button onClick={toggleCamera} className="bg-gray-500 hover:bg-gray-600">
                  취소
                </Button>
                <Button onClick={capturePhoto} className="bg-blue-500 hover:bg-blue-600">
                  사진 촬영
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="p-4 bg-white border-t">
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center bg-gray-100 rounded-full pr-2">
              <Textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="메시지를 입력하세요..."
                className="resize-none min-h-[40px] max-h-24 bg-transparent flex-1 py-2 pl-4 pr-20 focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <div className="flex items-center gap-1">
                <button className="p-1 hover:bg-gray-200 rounded-full">
                  <Mic className="h-5 w-5 text-gray-500" />
                </button>
                <button 
                  className="p-1 hover:bg-gray-200 rounded-full" 
                  onClick={toggleCamera}
                  disabled={isCapturing}
                >
                  <Camera className="h-5 w-5 text-gray-500" />
                </button>
              </div>
            </div>
            <Button 
              onClick={handleSendMessage} 
              className="shrink-0 h-10 w-10 rounded-full bg-blue-500 hover:bg-blue-600"
              disabled={!inputMessage.trim()}
            >
              <Send className="h-5 w-5 text-white" />
            </Button>
          </div>
        </div>

        {/* Bottom Navigation */}
        <nav className="py-2 grid grid-cols-4 border-t bg-white">
          {[
            { to: "/signup", icon: Home, label: "홈", active: true },
            { to: "#", icon: ImageIcon, label: "앨범" },
            { to: "#", icon: Heart, label: "추억" },
            { to: "/profile", icon: User, label: "프로필" }
          ].map(({ to, icon: Icon, label, active }) => (
            <Link key={label} to={to} className="flex flex-col items-center justify-center">
              <Icon className={`h-6 w-6 ${active ? "text-blue-500" : "text-gray-400"}`} />
              <span className={`text-[11px] mt-1 ${active ? "text-blue-500" : "text-gray-400"}`}>{label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
};

export default ChatPage;