import { useState, useRef, useEffect } from "react";
import { Home, Image, Heart, User, Send, Phone, Settings, Mic, Camera, Volume2, Search } from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  time: string;
  image?: string;
  voice?: string;
  messageType?: "chat" | "search" | "schedule";
}

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "ai",
      text: "안녕, 오늘 만나서 반가워! 나는 너의 AI 친구 미나야, 어떻게 지내고 있어?",
      time: "오전 10:23",
      messageType: "chat"
    },
  ]);
  
  const [inputMessage, setInputMessage] = useState("");
  const [isCapturing, setIsCapturing] = useState(false);
  const [showCameraPreview, setShowCameraPreview] = useState(false);
  const [cameraStreamUrl, setCameraStreamUrl] = useState("");
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [toast, setToast] = useState({ show: false, message: "", type: "info" });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Toast notification helper
  const showToast = (message: string, type: "info" | "error" | "success" = "info") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "info" }), 3000);
  };
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 검색 관련 키워드 체크
  const isSearchQuery = (text: string): boolean => {
    const searchKeywords = [
      '검색', '찾아', '알아봐', '정보', '뭐야', '무엇', '어떻게',
      'search', 'find', 'look up', '조사', '확인해', '알려줘',
      '최신', '뉴스', '현재', '트렌드', '동향'
    ];
    
    return searchKeywords.some(keyword => text.toLowerCase().includes(keyword));
  };
  
  // 카메라 관련 함수들
  const startCamera = async () => {
    try {
      setIsCapturing(true);
      showToast('카메라 준비 중...', 'info');
      
      const response = await fetch(`http://localhost:8182/api/camera/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('카메라 시작 요청 실패');
      }
      
      setCameraStreamUrl(`http://localhost:8182/api/camera/stream`);
      setShowCameraPreview(true);
      
    } catch (error) {
      console.error('카메라 접근 오류:', error);
      showToast('카메라에 접근할 수 없습니다.', 'error');
      setIsCapturing(false);
      setShowCameraPreview(false);
    }
  };
  
  const stopCamera = async () => {
    try {
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
      showToast('카메라를 중지할 수 없습니다.', 'error');
    }
  };
  
  const capturePhoto = async () => {
    try {
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
        const userMessage: Message = {
          id: Date.now().toString(),
          sender: 'user',
          text: "[사진을 전송했습니다]",
          time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
          image: data.image,
          messageType: "chat"
        };
        
        setMessages(prev => [...prev, userMessage]);
        
        setTimeout(() => {
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            sender: 'ai',
            text: `사진 분석 결과: ${data.emotion} 감정이 감지되었습니다.`,
            time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
            messageType: "chat"
          };
          setMessages(prev => [...prev, aiMessage]);
        }, 1000);
        
        await stopCamera();
      } else {
        showToast(data.message || '사진 촬영에 실패했습니다.', 'error');
      }
    } catch (error) {
      console.error('사진 촬영 오류:', error);
      showToast('사진 촬영에 실패했습니다.', 'error');
    }
  };
  
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    // 메시지 타입 결정
    let messageType: "chat" | "search" | "schedule" = "chat";
    
    // 일정 관련 키워드 체크
    const scheduleKeywords = [
      '일정', '약속', '미팅', '회의', '언제', '몇시', 
      '스케줄', '만나', '예약', '취소', '팀 회의', '팀회의',
      '일정을', '일정을 잡', '회의 일정', '회의일정',
      '시간과', '시간을', '시간 알려', '시간알려',
      '일정 잡', '일정잡', '일정관리', '일정 관리'
    ];
    
    const isScheduleRelated = scheduleKeywords.some(keyword => inputMessage.includes(keyword));
    const isSearch = isSearchMode || isSearchQuery(inputMessage);
    
    if (isScheduleRelated) {
      messageType = "schedule";
    } else if (isSearch) {
      messageType = "search";
    }
    
    // 사용자 메시지 추가
    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: inputMessage,
      time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
      messageType: messageType
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");
    setIsSearchMode(false);
    
    try {
      let endpoint = "";
      let requestBody = {};
      
      // 메시지 타입에 따라 다른 엔드포인트 사용
      if (messageType === "schedule") {
        console.log('일정 관련 메시지 감지:', inputMessage);
        endpoint = "/api/schedule/chat";
        requestBody = {
          user_id: 'user-1',
          text: inputMessage,
        };
      } else if (messageType === "search") {
        console.log('검색 요청 감지:', inputMessage);
        endpoint = "/app/search";
        requestBody = {
          user_id: 'user-1',
          text: inputMessage,
          search_type: 'web', // 'web', 'academic', 'news' 등으로 확장 가능
        };
        
        // 검색 중 표시
        const searchingMessage: Message = {
          id: (Date.now() + 0.5).toString(),
          sender: "ai",
          text: "🔍 검색 중입니다... 잠시만 기다려주세요.",
          time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
          messageType: "search"
        };
        setMessages(prev => [...prev, searchingMessage]);
        
      } else {
        console.log('일반 채팅 메시지 감지:', inputMessage);
        endpoint = "/api/chat";
        requestBody = {
          messages: [{
            role: 'user',
            content: inputMessage,
            timestamp: Date.now() / 1000
          }],
          user_id: 'user-1',
          ai_id: 'mina',
          context: {
            weather: '맑음',
            sleep: '7시간',
            stress: '중간',
            location_scene: '실내, 책상 앞',
            emotion_history: ['neutral', 'neutral', 'neutral']
          }
        };
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }
      
      const data = await response.json();
      
      // 검색 중 메시지 제거 (검색의 경우)
      if (messageType === "search") {
        setMessages(prev => prev.filter(msg => msg.id !== (Date.now() + 0.5).toString()));
      }
      
      // AI 응답 메시지 추가
      let responseText = '';
      
      if (messageType === "schedule") {
        if (data.success && data.message) {
          if (typeof data.message === 'object' && data.message.text) {
            responseText = data.message.text;
          } else if (typeof data.message === 'string') {
            responseText = data.message;
          } else {
            responseText = JSON.stringify(data.message);
          }
        } else {
          responseText = data.response || data.error || '응답을 받지 못했습니다.';
        }
      } else if (messageType === "search") {
        // 검색 결과 포맷팅
        if (data.success && data.results) {
          responseText = formatSearchResults(data.results);
        } else {
          responseText = data.message?.text || data.response || '검색 결과를 찾을 수 없습니다.';
        }
      } else {
        responseText = data.response || '';
      }
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: responseText || '응답을 받지 못했습니다.',
        time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
        messageType: messageType
      };
      
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      showToast('메시지를 전송할 수 없습니다.', 'error');
      
      // 검색 중 메시지 제거
      if (messageType === "search") {
        setMessages(prev => prev.filter(msg => msg.id !== (Date.now() + 0.5).toString()));
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: "죄송합니다. 현재 서버에 연결할 수 없습니다.",
        time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
        messageType: messageType
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };
  
  // 검색 결과 포맷팅 함수
  const formatSearchResults = (results: any): string => {
    if (!results || results.length === 0) {
      return "검색 결과를 찾을 수 없습니다.";
    }
    
    let formattedText = "🔍 검색 결과:\n\n";
    
    results.slice(0, 5).forEach((result: any, index: number) => {
      formattedText += `${index + 1}. **${result.title}**\n`;
      formattedText += `${result.snippet}\n`;
      if (result.link) {
        formattedText += `[더 보기](${result.link})\n`;
      }
      formattedText += "\n";
    });
    
    return formattedText;
  };
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Toast Notification */}
      {toast.show && (
        <div className={`fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
          toast.type === 'error' ? 'bg-red-500' : 
          toast.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
        } text-white`}>
          {toast.message}
        </div>
      )}

      {/* Left Sidebar */}
      <div className="w-72 border-r bg-white hidden lg:block">
        {/* Add left sidebar content here */}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="p-4 border-b bg-white flex items-center justify-between">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
              <img src="/example_avatar_profile.png" alt="AI Avatar" className="rounded-full" />
            </div>
            <div className="ml-3">
              <h2 className="font-medium">미나</h2>
              <p className="text-xs text-gray-500">
                {isSearchMode ? "검색 모드 🔍" : "활동중 상태"}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setIsSearchMode(!isSearchMode)} 
              className={`p-2 rounded-full transition duration-300 ease-in-out ${
                isSearchMode ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100 text-gray-500'
              }`}
              title="검색 모드 전환"
            >
              <Search className="h-5 w-5" />
            </button>
            <button 
              className="p-2 rounded-full hover:bg-blue-100 transition duration-300 ease-in-out"
              title="실시간 음성 채팅으로 전환"
            >
              <Phone className="h-5 w-5 text-blue-500" />
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
                <div className="h-8 w-8 rounded-full bg-gray-300 mr-2 mt-1 flex items-center justify-center">
                  <img src="/example_avatar_profile.png" alt="AI Avatar" className="rounded-full" />
                </div>
              )}
              <div className={`max-w-[70%] ${
                message.sender === "user" 
                  ? "bg-blue-500 text-white" 
                  : message.messageType === "search" 
                    ? "bg-purple-100 text-gray-800" 
                    : "bg-gray-200 text-gray-800"
              } rounded-2xl p-3 ${message.sender === "user" ? "rounded-tr-none" : "rounded-tl-none"}`}>
                {message.messageType === "search" && message.sender === "user" && (
                  <div className="flex items-center mb-1">
                    <Search className="h-4 w-4 mr-1" />
                    <span className="text-xs font-medium">검색 요청</span>
                  </div>
                )}
                {message.image && (
                  <div className="mb-2">
                    <img 
                      src={message.image} 
                      alt="Captured" 
                      className="rounded-lg max-w-full" 
                    />
                  </div>
                )}
                <div className="whitespace-pre-wrap">{message.text}</div>
                <span className="flex items-center justify-between mt-1 text-xs opacity-70">
                  {message.time}
                  {message.sender === "ai" && (
                    <button 
                      className="ml-2 p-1 hover:bg-gray-300 rounded-full"
                      onClick={async () => {
                        try {
                          const response = await fetch(`/api/tts`, {
                            method: 'POST',
                            headers: {
                              'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ text: message.text })
                          });

                          if (!response.ok) {
                            throw new Error('음성 변환 요청 실패');
                          }

                          const audioBlob = await response.blob();
                          const audioUrl = URL.createObjectURL(audioBlob);
                          const audio = new Audio(audioUrl);
                          
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
              </div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="p-4 bg-white border-t">
          {isSearchMode && (
            <div className="mb-2 px-2 py-1 bg-purple-100 rounded-lg text-sm text-purple-700">
              🔍 검색 모드가 활성화되었습니다. 궁금한 것을 물어보세요!
            </div>
          )}
          <div className="flex items-center gap-2 relative">
            <div className="flex-1 flex items-center bg-gray-100 rounded-full pr-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isSearchMode ? "검색할 내용을 입력하세요..." : "메시지를 입력하세요..."}
                className="resize-none min-h-[40px] max-h-24 bg-transparent flex-1 py-2 pl-4 pr-20 focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <div className="flex items-center gap-1">
                <button 
                  className={`p-1 rounded-full transition-all duration-300 ${
                    isSearchMode 
                      ? 'bg-purple-100 text-purple-600' 
                      : 'hover:bg-gray-200 text-gray-500'
                  }`}
                  onClick={() => setIsSearchMode(!isSearchMode)}
                  title="검색 모드 전환"
                >
                  <Search className="h-5 w-5" />
                </button>
                <button 
                  className="p-1 hover:bg-gray-200 rounded-full transition-all duration-300 hover:bg-blue-100 hover:text-blue-600"
                  title="실시간 음성 채팅으로 전환"
                >
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
            <button 
              onClick={handleSendMessage} 
              className={`shrink-0 h-10 w-10 rounded-full ${
                isSearchMode 
                  ? 'bg-purple-500 hover:bg-purple-600' 
                  : 'bg-blue-500 hover:bg-blue-600'
              } text-white flex items-center justify-center`}
              disabled={!inputMessage.trim()}
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Bottom Navigation */}
        <nav className="py-2 grid grid-cols-4 border-t bg-white">
          <button className="flex flex-col items-center justify-center">
            <Home className="h-6 w-6 text-blue-500" />
            <span className="text-[11px] text-blue-500 mt-1">홈</span>
          </button>
          <button className="flex flex-col items-center justify-center">
            <Image className="h-6 w-6 text-gray-400" />
            <span className="text-[11px] text-gray-400 mt-1">앨범</span>
          </button>
          <button className="flex flex-col items-center justify-center">
            <Heart className="h-6 w-6 text-gray-400" />
            <span className="text-[11px] text-gray-400 mt-1">추억</span>
          </button>
          <button className="flex flex-col items-center justify-center">
            <User className="h-6 w-6 text-gray-400" />
            <span className="text-[11px] text-gray-400 mt-1">프로필</span>
          </button>
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