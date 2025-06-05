import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Phone, PhoneOff, Camera, MessageSquare, X, Volume2, VolumeX, ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Message {
  id: string;
  type: 'user' | 'avatar';
  text: string;
  timestamp: Date;
  isTranslated?: boolean;
}

const RealtimeChat: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showConversation, setShowConversation] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [showPhotoUpload, setShowPhotoUpload] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [currentText, setCurrentText] = useState('안녕하세요');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'avatar',
      text: '삶은 무거울 수 있습니다, 특히 모든 것을 한 번에 짊어지려고 하면 말이죠.',
      timestamp: new Date(Date.now() - 180000),
      isTranslated: false
    },
    {
      id: '2',
      type: 'user',
      text: '오늘 기분이 좀 안 좋아요.',
      timestamp: new Date(),
      isTranslated: false
    },
    {
      id: '3',
      type: 'avatar',
      text: '힘든 하루셨군요. 무엇이 당신을 괴롭게 하는지 말씀해 주시겠어요?',
      timestamp: new Date(),
      isTranslated: false
    }
  ]);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const webSocketRef = useRef<WebSocket | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // 실시간 텍스트 업데이트 시뮬레이션
  useEffect(() => {
    if (isConnected && isListening) {
      const texts = [
        '안녕하세요',
        '오늘 어떻게 지내세요?',
        '무엇을 도와드릴까요?',
        '당신의 이야기를 들려주세요',
        '함께 해결책을 찾아보겠습니다'
      ];
      
      let index = 0;
      const interval = setInterval(() => {
        setCurrentText(texts[index % texts.length]);
        index++;
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [isConnected, isListening]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 组件卸载时清理WebSocket连接
  useEffect(() => {
    return () => {
      if (webSocketRef.current) {
        // 先发送断开连接请求再关闭WebSocket
        if (webSocketRef.current.readyState === WebSocket.OPEN) {
          webSocketRef.current.send(JSON.stringify({type: 'disconnect_minimax'}));
          webSocketRef.current.close();
        }
        webSocketRef.current = null;
      }
    };
  }, []);

  const handleConnect = () => {
    // 현재 연결 상태의 반대로 설정
    const nextConnectionState = !isConnected;
    setIsConnected(nextConnectionState);
    
    if (nextConnectionState) {
      // 연결 시작
      setCurrentText('연결 중...');
      setConnectionError(null);
      
      // 새 WebSocket 연결 생성
      const clientId = `user-${Date.now()}`; // 고유 클라이언트 ID 생성
      const ws = new WebSocket(`ws://${window.location.hostname}:8181/ws/realtime-chat?client_id=${clientId}`);
      
      ws.onopen = () => {
        console.log('WebSocket 연결 성공');
        setCurrentText('안녕하세요! 저는 당신의 AI 친구입니다.');
        setIsListening(true);
        
        // MiniMax 연결 요청 메시지 전송
        ws.send(JSON.stringify({
          type: 'connect_minimax',
          model: 'minimax-pro' // 원하는 모델 명시
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket 메시지 수신:', data);
          
          if (data.type === 'minimax_response') {
            // MiniMax로부터의 응답 처리
            if (data.data && data.data.text) {
              // 새 AI 메시지 추가
              addAvatarMessage(data.data.text);
            }
          } else if (data.type === 'error') {
            setConnectionError(data.message);
            console.error('WebSocket 오류:', data.message);
          } else if (data.type === 'connection_status') {
            if (!data.connected) {
              setConnectionError('MiniMax 연결 실패');
            }
          }
        } catch (error) {
          console.error('WebSocket 메시지 파싱 오류:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket 연결 종료');
        if (isConnected) {
          setConnectionError('서버와의 연결이 종료되었습니다.');
          setIsConnected(false);
          setIsListening(false);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket 오류:', error);
        setConnectionError('서버 연결에 오류가 발생했습니다.');
      };
      
      webSocketRef.current = ws;
    } else {
      // 연결 종료
      if (webSocketRef.current) {
        // MiniMax 연결 종료 요청
        if (webSocketRef.current.readyState === WebSocket.OPEN) {
          webSocketRef.current.send(JSON.stringify({type: 'disconnect_minimax'}));
          webSocketRef.current.close();
        }
        webSocketRef.current = null;
      }
      
      setCurrentText('안녕하세요');
      setIsListening(false);
      setIsRecording(false);
      setIsSpeaking(false);
    }
  };

  const handleMicToggle = () => {
    if (isConnected) {
      setIsRecording(!isRecording);
      if (!isRecording) {
        // 녹음 시작 시뮬레이션
        setCurrentText('듣고 있습니다...');
        setTimeout(() => {
          addUserMessage('스트레스를 많이 받고 있어요.');
          setTimeout(() => {
            addAvatarMessage('스트레스가 많으시군요. 어떤 일 때문인지 자세히 말씀해 주시겠어요?');
          }, 1500);
        }, 2000);
      } else {
        setCurrentText('처리 중...');
      }
    }
  };

  const handleSpeakerToggle = () => {
    setIsSpeaking(!isSpeaking);
  };

  const handleCameraToggle = async () => {
    if (showCamera) {
      // 카메라 끄기
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        setCameraStream(null);
      }
      setShowCamera(false);
    } else {
      // 카메라 켜기
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: 320, height: 240 } 
        });
        setCameraStream(stream);
        setShowCamera(true);
        
        // 비디오 스트림 설정
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error('카메라에 접근할 수 없습니다:', error);
        // 카메라 접근 실패 시 사진 업로드 옵션 표시
        setShowPhotoUpload(true);
      }
    }
  };

  const handlePhotoUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // 업로드된 사진 처리 가능
      console.log('업로드된 사진:', file);
      addUserMessage(`📷 사진이 업로드되었습니다: ${file.name}`);
      
      // AI 답변 시뮬레이션
      setTimeout(() => {
        addAvatarMessage('사진을 업로드하신 것을 확인했습니다. 이 사진에 대해 궁금한 점이 있으시면 말씀해 주세요. 함께 분석하거나 이야기 나눌 수 있습니다.');
      }, 1000);
    }
  };

  const addUserMessage = (text: string) => {
    const newMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      text,
      timestamp: new Date(),
      isTranslated: false
    };
    setMessages(prev => [...prev, newMessage]);
    
    // 메시지를 WebSocket을 통해 서버로 전송
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      try {
        webSocketRef.current.send(JSON.stringify({
          type: 'send_to_minimax',
          message: {
            type: 'text',
            text: text
          }
        }));
      } catch (error) {
        console.error('메시지 전송 실패:', error);
        setConnectionError('메시지 전송에 실패했습니다.');
      }
    } else {
      console.warn('WebSocket이 연결되어 있지 않아 메시지를 전송할 수 없습니다.');
      setConnectionError('서버와 연결되어 있지 않습니다. 연결 버튼을 눌러 다시 시도해주세요.');
    }
  };

  const addAvatarMessage = (text: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type: 'avatar',
      text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
    setCurrentText(text);
  };

  const navigate = useNavigate();

  return (
    <div className="relative w-full max-w-md mx-auto h-screen bg-gradient-to-br from-pink-200 via-purple-200 to-blue-200 overflow-hidden">
      {/* 채팅으로 돌아가는 화살표 버튼 */}
      <button
        onClick={() => navigate('/chat')}
        className="absolute top-12 left-4 bg-white/40 backdrop-blur-sm px-4 py-2 rounded-full flex items-center space-x-1 shadow-md hover:bg-white/60 transition-all z-20 hover:scale-105"
        title="채팅으로 돌아가기"
      >
        <ChevronLeft className="w-5 h-5 text-gray-700" />
        <span className="text-sm font-medium text-gray-800">채팅</span>
      </button>
      
      {/* 클릭 가능한 원형 통화 버튼 - 사진 업로드 디자인 참고 */}
      <button
        onClick={handleConnect}
        className="absolute top-24 left-1/2 transform -translate-x-1/2 w-48 h-48 rounded-full focus:outline-none focus:ring-4 focus:ring-cyan-300 transition-all duration-300 hover:scale-105 group"
      >
        {/* 바깥쪽 빛나는 테두리 */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-300 via-purple-300 to-purple-400 p-1">
          {/* 중간 그라데이션 배경 */}
          <div className="w-full h-full rounded-full bg-gradient-to-br from-purple-200 via-pink-200 to-purple-300 relative overflow-hidden">
            {/* 유리 광택 효과 */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-transparent rounded-full"></div>
            <div className="absolute top-4 left-8 w-16 h-8 bg-white/20 rounded-full blur-md transform rotate-12"></div>
            <div className="absolute bottom-8 right-12 w-12 h-6 bg-white/15 rounded-full blur-sm transform -rotate-12"></div>
            
            {/* 중앙 오디오 파형 아이콘 컨테이너 */}
            <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
              isConnected 
                ? 'bg-red-500/90 backdrop-blur-sm shadow-lg' 
                : 'bg-white/40 backdrop-blur-sm shadow-lg group-hover:bg-white/50'
            }`}>
              {isConnected ? (
                <PhoneOff className="w-8 h-8 text-white" />
              ) : (
                /* 오디오 파형 아이콘 */
                <div className="flex items-center justify-center space-x-1">
                  <div className="w-1 h-4 bg-white rounded-full"></div>
                  <div className="w-1 h-6 bg-white rounded-full"></div>
                  <div className="w-1 h-8 bg-white rounded-full"></div>
                  <div className="w-1 h-6 bg-white rounded-full"></div>
                  <div className="w-1 h-4 bg-white rounded-full"></div>
                </div>
              )}
            </div>
            
            {/* 연결 상태 시 동적 파동 효과 */}
            {isConnected && (
              <>
                <div className="absolute inset-4 rounded-full border-2 border-white/30 animate-ping"></div>
                <div className="absolute inset-8 rounded-full border border-white/20 animate-pulse"></div>
              </>
            )}
          </div>
        </div>
      </button>
      
      {/* 카메라 영역 */}
      {showCamera && (
        <div className="absolute top-20 left-4 right-4 z-20">
          <div className="bg-black/20 backdrop-blur-md rounded-3xl p-2 shadow-2xl border border-white/30 relative">
            <video
              ref={videoRef}
              autoPlay
              muted
              className="w-full h-48 object-cover rounded-2xl"
            ></video>
            <div className="absolute bottom-3 right-3">
              <button
                className="bg-white/30 backdrop-blur-sm border border-white/40 rounded-full p-3 hover:bg-white/40 transition-all duration-300 shadow-lg"
                onClick={() => {
                  // 사진 촬영 기능
                  const canvas = document.createElement('canvas');
                  const video = videoRef.current;
                  if (video) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const ctx = canvas.getContext('2d');
                    ctx?.drawImage(video, 0, 0);
                    
                    // 사진 촬영 메시지 추가
                    addUserMessage('📸 사진을 촬영했습니다.');
                    
                    // AI 답변 시뮬레이션
                    setTimeout(() => {
                      addAvatarMessage('사진을 잘 촬영하셨네요! 이 사진에 대해 무엇을 알고 싶으신가요?');
                    }, 1000);
                  }
                }}
              >
                <Camera className="w-6 h-6 text-white" />
              </button>
            </div>
            {/* 카메라 장식 테두리 */}
            <div className="absolute inset-2 border-2 border-white/20 rounded-xl pointer-events-none"></div>
          </div>
        </div>
      )}

      {/* 사진 업로드 선택 창 - 리디자인 */}
      {showPhotoUpload && (
        <div className="absolute top-20 left-4 right-4 z-20">
          <div className="bg-white/20 backdrop-blur-md rounded-3xl p-6 shadow-2xl border border-white/30">
            {/* 헤더 */}
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-800">사진 업로드</h3>
              <button
                onClick={() => setShowPhotoUpload(false)}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-700" />
              </button>
            </div>
            
            {/* 옵션 버튼 */}
            <div className="space-y-4">
              <button
                onClick={handleCameraToggle}
                className="w-full bg-white/30 backdrop-blur-sm border border-white/40 text-gray-800 py-4 rounded-2xl hover:bg-white/40 transition-all duration-300 flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                  <Camera className="w-5 h-5 text-white" />
                </div>
                <span className="text-base font-medium">카메라 열기</span>
              </button>
              
              <button
                onClick={handlePhotoUpload}
                className="w-full bg-white/30 backdrop-blur-sm border border-white/40 text-gray-800 py-4 rounded-2xl hover:bg-white/40 transition-all duration-300 flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm1 1v10h12V5H4zm2 2a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm0 3a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm0 3a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <span className="text-base font-medium">갤러리에서 선택</span>
              </button>
            </div>
            
            {/* 하단 안내 */}
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600/80">사진을 통해 AI 친구와 더 풍부한 대화를 나누세요</p>
            </div>
          </div>
        </div>
      )}

      {/* 숨겨진 파일 입력 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />
      <div className="absolute top-12 right-4 flex justify-end items-center z-10">
        <button
          onClick={() => setShowConversation(true)}
          className="flex items-center space-x-1 bg-white/20 backdrop-blur-sm rounded-full px-3 py-2 text-gray-700"
        >
          <MessageSquare className="w-4 h-4" />
          <span className="text-sm font-medium">대화 내용</span>
        </button>
      </div>

      {/* 중앙 상태 표시기 */}
      <div className="absolute top-80 left-1/2 transform -translate-x-1/2 z-10">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'} mx-auto mb-2`}></div>
        <div className="text-center text-gray-600 text-sm font-medium">
          {isConnected ? '대화 중' : '원을 터치하여 시작'}
        </div>
      </div>

      {/* 실시간 텍스트 표시 - 위치 중앙으로 조정 */}
      <div className="absolute bottom-40 left-4 right-4 z-10">
        <div className="bg-white/30 backdrop-blur-sm rounded-2xl p-4 min-h-[100px] flex items-center justify-center">
          <p className="text-gray-800 text-center leading-relaxed">
            {currentText}
          </p>
        </div>
        {isListening && (
          <div className="flex justify-center mt-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span className="ml-2 text-sm text-gray-600">처리 중...</span>
          </div>
        )}
      </div>

      {/* 하단 컨트롤 버튼 */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex items-center space-x-6 z-10">
        {/* 마이크 버튼 */}
        <button
          onClick={handleMicToggle}
          disabled={!isConnected}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            isRecording 
              ? 'bg-red-500 text-white shadow-lg' 
              : isConnected 
                ? 'bg-white/30 backdrop-blur-sm text-gray-700 hover:bg-white/40' 
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isRecording ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
        </button>

        {/* 사진 촬영 버튼 */}
        <button
          onClick={() => setShowPhotoUpload(true)}
          disabled={!isConnected}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            isConnected 
              ? 'bg-white/30 backdrop-blur-sm text-gray-700 hover:bg-white/40' 
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          <Camera className="w-6 h-6" />
        </button>

        {/* 스피커 버튼 */}
        <button
          onClick={handleSpeakerToggle}
          disabled={!isConnected}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            isSpeaking && isConnected
              ? 'bg-blue-500 text-white shadow-lg' 
              : isConnected 
                ? 'bg-white/30 backdrop-blur-sm text-gray-700 hover:bg-white/40' 
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isSpeaking ? <Volume2 className="w-6 h-6" /> : <VolumeX className="w-6 h-6" />}
        </button>
      </div>

      {/* 대화 내용 사이드바 - 리디자인 */}
      {showConversation && (
        <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-br from-pink-200/40 via-purple-200/40 to-blue-200/40 backdrop-blur-xl z-40 flex flex-col shadow-2xl border-l border-white/30">
          {/* 헤더 */}
          <div className="flex items-center justify-between p-6 border-b border-white/20 bg-white/10 backdrop-blur-sm">
            <h2 className="text-xl font-medium text-gray-800">대화 내용</h2>
            <button
              onClick={() => setShowConversation(false)}
              className="p-2 hover:bg-white/20 rounded-full transition-colors"
            >
              <X className="w-6 h-6 text-gray-700" />
            </button>
          </div>
          {/* 메시지 목록 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-3xl shadow-lg backdrop-blur-sm border ${
                    message.type === 'user'
                      ? 'bg-blue-500/80 text-white border-blue-400/30'
                      : 'bg-white/30 text-gray-800 border-white/40'
                  }`}
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-medium opacity-80">
                      {message.type === 'user' ? '나' : 'AI 친구'}
                    </span>
                    <span className="text-xs opacity-70">
                      {message.timestamp.toLocaleTimeString('ko-KR', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                  <div className="text-sm leading-relaxed">
                    {message.text}
                  </div>
                </div>
              </div>
            ))}
            
            {/* 실시간 상태 표시 */}
            {isConnected && isListening && (
              <div className="flex justify-start">
                <div className="bg-green-400/30 backdrop-blur-sm border border-green-300/40 px-4 py-3 rounded-3xl max-w-[85%] shadow-lg">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs text-green-800 font-medium">AI 친구</span>
                    <span className="text-xs text-green-700">실시간</span>
                  </div>
                  <div className="text-gray-800 text-sm leading-relaxed mb-2">
                    {currentText}
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-xs text-green-700">대화 중...</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* 녹음 상태 표시 */}
            {isRecording && (
              <div className="flex justify-end">
                <div className="bg-red-400/30 backdrop-blur-sm border border-red-300/40 px-4 py-3 rounded-3xl max-w-[85%] shadow-lg">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs text-red-800 font-medium">나</span>
                    <span className="text-xs text-red-700">녹음 중</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-5 bg-red-500 rounded-sm animate-pulse"></div>
                      <div className="w-2 h-7 bg-red-500 rounded-sm animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-6 bg-red-500 rounded-sm animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-8 bg-red-500 rounded-sm animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                    </div>
                    <span className="text-xs text-red-700">음성 입력 중...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* 통계 정보 */}
          <div className="p-4 bg-white/10 backdrop-blur-sm border-t border-white/20">
            <div className="text-sm text-gray-700 text-center space-y-2">
              <div className="flex items-center justify-center space-x-4">
                <span>📊 메시지: {messages.length}개</span>
                <span>{isConnected ? '✅ 연결됨' : '❌ 연결 끊김'}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeChat;
