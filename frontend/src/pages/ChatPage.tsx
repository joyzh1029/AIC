import { useState, useRef, useEffect } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Link } from "react-router-dom";
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

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "ai",
      text: "안녕, 오늘 만나서 반가워! 나는 너의 AI 친구미나야, 어떻게지내고있어?",
      time: "오전 10:23",
    },
  ]);
  
  const [inputMessage, setInputMessage] = useState("");
  const [isCapturing, setIsCapturing] = useState(false);
  const [showCameraPreview, setShowCameraPreview] = useState(false);
  const [cameraStreamUrl, setCameraStreamUrl] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 카메라 캡처 시작 함수
  const startCamera = async () => {
    try {
      setIsCapturing(true);
      toast.info('카메라 준비 중...');
      
      // 백엔드에 카메라 시작 요청
      const response = await fetch(`http://localhost:8182/api/camera/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('카메라 시작 요청 실패');
      }
      
      // 카메라 스트림 URL 설정
      setCameraStreamUrl(`http://localhost:8182/api/camera/stream`);
      setShowCameraPreview(true);
      
    } catch (error) {
      console.error('카메라 접근 오류:', error);
      toast.error('카메라에 접근할 수 없습니다.');
      setIsCapturing(false);
      setShowCameraPreview(false);
    }
  };
  
  // 카메라 중지 함수
  const stopCamera = async () => {
    try {
      // 백엔드에 카메라 중지 요청
      await fetch(`http://localhost:8182/api/camera/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      setShowCameraPreview(false);
      setCameraStreamUrl("");
      setIsCapturing(false);
      
    } catch (error) {
      console.error('카메라 중지 오류:', error);
      toast.error('카메라를 중지할 수 없습니다.');
    }
  };
  
  // 사진 촬영 함수
  const capturePhoto = async () => {
    try {
      // 백엔드에 캡처 요청
      const response = await fetch(`http://localhost:8182/api/camera/capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('사진 촬영 요청 실패');
      }
      
      const data = await response.json();
      
      if (data.success) {
        // 사용자 메시지 추가
        const userMessage: Message = {
          id: Date.now().toString(),
          sender: 'user',
          text: "[사진을 전송했습니다]",
          time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
          image: data.image
        };
        
        setMessages(prev => [...prev, userMessage]);
        
        // AI 응답 메시지 추가
        setTimeout(() => {
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            sender: 'ai',
            text: `사진 분석 결과: ${data.emotion} 감정이 감지되었습니다.`,
            time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
          };
          setMessages(prev => [...prev, aiMessage]);
        }, 1000);
        
        // 카메라 중지
        await stopCamera();
      } else {
        toast.error(data.message || '사진 촬영에 실패했습니다.');
      }
    } catch (error) {
      console.error('사진 촬영 오류:', error);
      toast.error('사진 촬영에 실패했습니다.');
    }
  };
  
  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;
    
    // 사용자 메시지 추가
    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: inputMessage,
      time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");
    
    // 서버로 메시지 전송 및 응답 처리 (간단한 구현)
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: `"${inputMessage}"에 대한 응답입니다. 저는 AI 친구 미나입니다.`,
        time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
      };
      
      setMessages(prev => [...prev, aiMessage]);
    }, 1000);
  };
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Sidebar */}
      <div className="w-72 border-r bg-white hidden lg:block">
        {/* Add left sidebar content here */}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="p-4 border-b bg-white flex items-center justify-between">
          <div className="flex items-center">
            <Avatar className="h-10 w-10">
              <img src="/example_avatar_profile.png" alt="AI Avatar" />
            </Avatar>
            <div className="ml-3">
              <h2 className="font-medium">미나</h2>
              <p className="text-xs text-gray-500">활동중 상태</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 rounded-full hover:bg-gray-100">
              <Phone className="h-5 w-5 text-gray-500" />
            </button>
            <button className="p-2 rounded-full hover:bg-gray-100">
              <Settings className="h-5 w-5 text-gray-500" />
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(message => (
            <div key={message.id} className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
              {message.sender === "ai" && (
                <Avatar className="h-8 w-8 mr-2 mt-1">
                  <img src="/example_avatar_profile.png" alt="AI Avatar" />
                </Avatar>
              )}
              <div className={`max-w-[70%] ${message.sender === "user" ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-800"} rounded-2xl p-3 ${message.sender === "user" ? "rounded-tr-none" : "rounded-tl-none"}`}>
                {message.image && (
                  <div className="mb-2">
                    <img 
                      src={message.image} 
                      alt="Captured" 
                      className="rounded-lg max-w-full" 
                    />
                  </div>
                )}
                <p>{message.text}</p>
                <span className="flex items-center justify-between mt-1 text-xs opacity-70">
                  {message.time}
                  {message.sender === "ai" && (
                  <button 
                    className="ml-2 p-1 hover:bg-gray-300 rounded-full"
                    onClick={async () => {
                    try {
                      // 음성 변환 요청
                      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/tts`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ text: message.text })
                      });

                      if (!response.ok) {
                        throw new Error('음성 변환 요청 실패');
                      }

                      // Create and play audio
                      const audioBlob = await response.blob();
                      const audioUrl = URL.createObjectURL(audioBlob);
                      const audio = new Audio(audioUrl);
                      
                      // Cleanup after playback
                      audio.onended = () => {
                        URL.revokeObjectURL(audioUrl);
                      };

                      await audio.play();
                    } catch (error) {
                      console.error('음성 재생 실패:', error);
                    }
                  }}
                  aria-label="음성 듣기"
                  tabIndex={0}
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
            
            <div className="relative overflow-hidden rounded-lg mb-4">
              <img 
                src={cameraStreamUrl} 
                alt="카메라 미리보기" 
                className="w-full h-auto" 
              />
            </div>
            
            <div className="flex justify-between">
              <Button 
                onClick={stopCamera}
                className="bg-gray-500 hover:bg-gray-600"
              >
                취소
              </Button>
              <Button 
                onClick={capturePhoto}
                className="bg-blue-500 hover:bg-blue-600"
              >
                사진 촬영
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Input Section */}
      <div className="p-4 bg-white border-t">
        <div className="flex items-center gap-2 relative">
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
                onClick={startCamera}
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
        <Link to="/signup" className="flex flex-col items-center justify-center">
          <Home className="h-6 w-6 text-blue-500" />
          <span className="text-[11px] text-blue-500 mt-1">홈</span>
        </Link>
        <button className="flex flex-col items-center justify-center">
          <ImageIcon className="h-6 w-6 text-gray-400" />
          <span className="text-[11px] text-gray-400 mt-1">앨범</span>
        </button>
        <button className="flex flex-col items-center justify-center">
          <Heart className="h-6 w-6 text-gray-400" />
          <span className="text-[11px] text-gray-400 mt-1">추억</span>
        </button>
        <Link to="/profile" className="flex flex-col items-center justify-center">
          <User className="h-6 w-6 text-gray-400" />
          <span className="text-[11px] text-gray-400 mt-1">프로필</span>
        </Link>
      </nav>
      </div>

      {/* Right Sidebar */}
      <div className="w-72 border-l bg-white hidden lg:block">
        {/* Add right sidebar content here */}
      </div>
    </div>
  );
};

export default ChatPage;
