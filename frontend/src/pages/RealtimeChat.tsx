import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Phone, PhoneOff, Camera, MessageSquare, X, Volume2, VolumeX, ChevronLeft, Square, Loader2, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Message {
  id: string;
  type: 'user' | 'avatar';
  text: string;
  timestamp: Date;
  isTranslated?: boolean;
}

const RealtimeChat: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showConversation, setShowConversation] = useState(false);
  const [currentText, setCurrentText] = useState('원을 터치하여 시작');
  const [messages, setMessages] = useState<Message[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [minimaxConnected, setMinimaxConnected] = useState(false);
  const [audioBuffer, setAudioBuffer] = useState<ArrayBuffer[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const webSocketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const currentAiResponseIdRef = useRef<string | null>(null);
  const audioBufferRef = useRef<ArrayBuffer[]>([]);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
        webSocketRef.current.close(1000, 'Component unmounting');
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const addMessageToChat = (id: string, type: 'user' | 'avatar', text: string, isDelta: boolean = false) => {
    setMessages(prevMessages => {
      if (isDelta) {
        const existingMessageIndex = prevMessages.findIndex(msg => msg.id === id);
        if (existingMessageIndex > -1) {
          const updatedMessages = [...prevMessages];
          updatedMessages[existingMessageIndex] = {
            ...updatedMessages[existingMessageIndex],
            text: updatedMessages[existingMessageIndex].text + text,
            timestamp: new Date(),
          };
          return updatedMessages;
        }
      }
      const existingMessage = prevMessages.find(msg => msg.id === id);
      if (existingMessage && !isDelta) {
        return prevMessages.map(msg => 
          msg.id === id ? { ...msg, text, timestamp: new Date() } : msg
        );
      }
      return [...prevMessages, { id, type, text, timestamp: new Date() }];
    });
  };

  const playAudioResponse = async (base64Audio: string) => {
    try {
      // 创建音频元素并播放
      const audio = new Audio(`data:audio/pcm;base64,${base64Audio}`);
      
      audio.onplay = () => {
        setIsSpeaking(true);
      };
      
      audio.onended = () => {
        setIsSpeaking(false);
        setCurrentText('원을 터치하여 시작');
      };
      
      audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        setIsSpeaking(false);
        
        // 尝试使用 Web Audio API 播放 PCM 数据
        try {
          const audioData = atob(base64Audio);
          const arrayBuffer = new ArrayBuffer(audioData.length);
          const uint8Array = new Uint8Array(arrayBuffer);
          
          for (let i = 0; i < audioData.length; i++) {
            uint8Array[i] = audioData.charCodeAt(i);
          }
          
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
            sampleRate: 24000
          });
          
          const pcm16Data = new Int16Array(arrayBuffer);
          const audioBuffer = audioContext.createBuffer(1, pcm16Data.length, 24000);
          const channelData = audioBuffer.getChannelData(0);
          
          for (let i = 0; i < pcm16Data.length; i++) {
            channelData[i] = pcm16Data[i] / 32768.0;
          }
          
          const source = audioContext.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioContext.destination);
          source.onended = () => {
            setIsSpeaking(false);
            setCurrentText('원을 터치하여 시작');
          };
          source.start();
          setIsSpeaking(true);
        } catch (fallbackError) {
          console.error('Web Audio API fallback also failed:', fallbackError);
          setConnectionError('음성 재생에 실패했습니다.');
        }
      };
      
      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      setConnectionError('AI 오디오 재생에 실패했습니다.');
      setIsSpeaking(false);
    }
  };

  const playAccumulatedAudio = async () => {
    try {
      console.log('Starting to play accumulated audio, buffer count:', audioBufferRef.current.length);
      
      // 合并所有音频缓冲区
      const totalLength = audioBufferRef.current.reduce((sum, buffer) => sum + buffer.byteLength, 0);
      const combinedBuffer = new ArrayBuffer(totalLength);
      const combinedUint8 = new Uint8Array(combinedBuffer);
      
      let offset = 0;
      for (const buffer of audioBufferRef.current) {
        combinedUint8.set(new Uint8Array(buffer), offset);
        offset += buffer.byteLength;
      }
      
      // 清空缓冲区
      audioBufferRef.current = [];
      
      // 使用 Web Audio API 播放 PCM 数据
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 24000
      });
      
      const pcm16Data = new Int16Array(combinedBuffer);
      const audioBuffer = audioContext.createBuffer(1, pcm16Data.length, 24000);
      const channelData = audioBuffer.getChannelData(0);
      
      for (let i = 0; i < pcm16Data.length; i++) {
        channelData[i] = pcm16Data[i] / 32768.0;
      }
      
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      
      source.onended = () => {
        console.log('Audio playback finished');
        setIsSpeaking(false);
        setCurrentText('원을 터치하여 시작');
      };
      
      setIsSpeaking(true);
      source.start();
      
    } catch (error) {
      console.error('Error playing accumulated audio:', error);
      setConnectionError('音频播放失败');
      setIsSpeaking(false);
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setIsConnected(false);
    setMinimaxConnected(false);
    
    // 停止录音器
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    
    // 关闭WebSocket连接
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      webSocketRef.current.close(1000, 'User stopped recording');
    }
    
    // 清空音频缓冲区
    audioBufferRef.current = [];
    
    setCurrentText('원을 터치하여 시작');
    setConnectionError(null);
  };

  const handleMainButtonClick = async () => {
    if (isRecording) {
      // Stop recording
      stopRecording();
      return;
    } else {
      // Start new recording session
      setIsRecording(true);
      setConnectionError(null);
      setCurrentText('Node.js 프록시 연결 중...');
      currentAiResponseIdRef.current = null;
      setIsConnected(false);
      setMinimaxConnected(false);

      const clientId = `user-${Date.now()}`;
      const wsUrl = `ws://localhost:3003/ws/realtime-chat?client_id=${clientId}`;
      console.log('Attempting to connect to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      webSocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected to Node.js proxy');
        setIsConnected(true);
      };

      ws.onmessage = async (event) => {
        let messageData;
        try {
          messageData = JSON.parse(event.data as string);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', event.data, e);
          setConnectionError('잘못된 형식의 메시지를 받았습니다.');
          return;
        }
        
        console.log('Received from Node.js proxy:', messageData);

        switch (messageData.type) {
          case 'connection_status':
            if (messageData.connected) {
              setMinimaxConnected(true);
              setCurrentText('Minimax 연결됨. 말씀하세요...'); // Default message
              // If minimax_session_initiated is true, Minimax is likely ready or will be soon
              if (messageData.minimax_session_initiated) {
                setCurrentText('Minimax 세션 준비됨. 말씀하세요...');
              }
              
              try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorderOptions: MediaRecorderOptions = {};
                
                if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                  recorderOptions.mimeType = 'audio/webm;codecs=opus';
                } else if (MediaRecorder.isTypeSupported('audio/webm')) {
                  recorderOptions.mimeType = 'audio/webm';
                }
                
                const recorder = new MediaRecorder(stream, recorderOptions);
                mediaRecorderRef.current = recorder;

                recorder.ondataavailable = (event) => {
                  if (event.data.size > 0 && webSocketRef.current?.readyState === WebSocket.OPEN) {
                    const reader = new FileReader();
                    reader.onloadend = () => {
                      const base64Audio = reader.result as string;
                      webSocketRef.current?.send(JSON.stringify({
                        type: 'input_audio_buffer.append',
                        audio: base64Audio.split(',')[1]
                      }));
                    };
                    reader.readAsDataURL(event.data);
                  }
                };

                recorder.onstop = () => {
                  if (webSocketRef.current?.readyState === WebSocket.OPEN) {
                    webSocketRef.current?.send(JSON.stringify({ 
                      type: 'input_audio_buffer.commit' 
                    }));
                  }
                  stream.getTracks().forEach(track => track.stop());
                };
                
                recorder.start(100);
              } catch (err) {
                console.error('Error accessing microphone:', err);
                setConnectionError('마이크 접근 또는 녹음 시작에 실패했습니다.');
                setIsRecording(false);
                setCurrentText('마이크 오류');
              }
            } else {
              setCurrentText('Minimax 연결 실패');
              setConnectionError(messageData.message || 'Minimax 연결에 실패했습니다.');
              setIsRecording(false);
              if (ws.readyState === WebSocket.OPEN) ws.close();
            }
            break;

          case 'session.created': // Handle session.created from Minimax (via proxy)
            console.log('Session created with Minimax:', messageData.session);
            setCurrentText('Minimax 세션 생성됨. 준비 중...');
            // Further actions can be triggered here if needed, e.g., enabling UI elements
            break;

          case 'response.audio_transcript.delta':
            if (messageData.delta) {
              if (!currentAiResponseIdRef.current) {
                currentAiResponseIdRef.current = `ai-${Date.now()}`;
              }
              addMessageToChat(currentAiResponseIdRef.current, 'avatar', messageData.delta, true);
            }
            break;

          case 'response.audio.delta':
            // 音频数据累积
            if (messageData.delta) {
              console.log('Received audio delta');
              try {
                const audioData = atob(messageData.delta);
                const arrayBuffer = new ArrayBuffer(audioData.length);
                const uint8Array = new Uint8Array(arrayBuffer);
                
                for (let i = 0; i < audioData.length; i++) {
                  uint8Array[i] = audioData.charCodeAt(i);
                }
                
                audioBufferRef.current.push(arrayBuffer);
              } catch (error) {
                console.error('Error processing audio delta:', error);
              }
            }
            break;

          case 'response.text.delta':
            if (messageData.delta) {
              if (!currentAiResponseIdRef.current) {
                currentAiResponseIdRef.current = `ai-${Date.now()}`;
              }
              addMessageToChat(currentAiResponseIdRef.current, 'avatar', messageData.delta, true);
            }
            break;

          case 'response.text.done':
            if (messageData.text) {
              const responseId = currentAiResponseIdRef.current || `ai-${Date.now()}`;
              addMessageToChat(responseId, 'avatar', messageData.text, false);
            }
            setCurrentText('원을 터치하여 시작');
            break;

          case 'response.audio_transcript.done':
            if (messageData.transcript) {
              const responseId = currentAiResponseIdRef.current || `ai-${Date.now()}`;
              addMessageToChat(responseId, 'avatar', messageData.transcript, false);
            }
            break;

          case 'response.audio.done':
            // 播放累积的音频数据
            if (audioBufferRef.current.length > 0) {
              console.log('Playing accumulated audio data');
              await playAccumulatedAudio();
            }
            break;

          case 'response.created':
            console.log('Response created:', messageData.response);
            setCurrentText('AI 응답 생성 중...');
            break;

          case 'response.output_item.added':
            console.log('Output item added:', messageData.item);
            break;

          case 'response.output_item.done':
            console.log('Output item done:', messageData.item);
            break;

          case 'response.done':
            console.log('Response complete:', messageData);
            if (messageData.response && messageData.response.output) {
              const output = messageData.response.output[0];
              if (output) {
                if (output.type === 'message' && output.content) {
                  // 텍스트 응답 처리
                  const textContent = output.content.find((c: any) => c.type === 'text');
                  if (textContent && textContent.text) {
                    const responseId = currentAiResponseIdRef.current || `ai-${Date.now()}`;
                    addMessageToChat(responseId, 'avatar', textContent.text, false);
                  }
                  
                  // 오디오 응답 처리
                  const audioContent = output.content.find((c: any) => c.type === 'audio');
                  if (audioContent && audioContent.audio) {
                    await playAudioResponse(audioContent.audio);
                  }
                }
              }
            }
            setCurrentText('원을 터치하여 시작');
            break;

          case 'error':
            console.error('Error from proxy/Minimax:', messageData);
            setConnectionError(`오류: ${messageData.message || messageData.error || '알 수 없는 오류가 발생했습니다.'}`);
            setCurrentText('오류 발생');
            setIsRecording(false);
            if (ws.readyState === WebSocket.OPEN) ws.close();
            break;

          default:
            console.log('Unknown message type:', messageData.type);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket 연결 오류가 발생했습니다.');
        setIsRecording(false);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setMinimaxConnected(false);
        if (isRecording) {
          setIsRecording(false);
          setCurrentText('연결이 끊어졌습니다');
        }
      };
    }
  };

  return (
    <div className="relative w-full max-w-md mx-auto h-screen bg-gradient-to-br from-pink-200 via-purple-200 to-blue-200 overflow-hidden">
      {/* 오류 메시지 표시 */}
      {connectionError && (
        <div className="absolute top-16 left-4 right-4 z-30">
          <div className="bg-red-500/20 backdrop-blur-sm border border-red-400/40 rounded-2xl p-4">
            <div className="flex items-center justify-between">
              <span className="text-red-800 text-sm">{connectionError}</span>
              <button
                onClick={() => setConnectionError(null)}
                className="text-red-600 hover:text-red-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 상단 네비게이션 바 */}
      <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between p-4">
        {/* 채팅으로 돌아가는 버튼 */}
        <button
          onClick={() => navigate('/chat')}
          className="bg-white/40 backdrop-blur-sm px-4 py-2 rounded-full flex items-center space-x-1 shadow-md hover:bg-white/60 transition-all hover:scale-105"
          title="채팅으로 돌아가기"
        >
          <ChevronLeft className="w-5 h-5 text-gray-700" />
          <span className="text-sm font-medium text-gray-800">채팅</span>
        </button>

        {/* 우측 버튼들 */}
        <div className="flex items-center space-x-2">

          {/* 대화 내용 버튼 */}
          <button
            onClick={() => setShowConversation(true)}
            className="flex items-center space-x-1 bg-white/40 backdrop-blur-sm rounded-full px-4 py-2 text-gray-700 hover:bg-white/60 transition-all hover:scale-105 shadow-md"
          >
            <MessageSquare className="w-4 h-4" />
            <span className="text-sm font-medium">대화 내용</span>
            {messages.length > 0 && (
              <span className="ml-1 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {messages.length}
              </span>
            )}
          </button>
        </div>
      </div>
      
      {/* 클릭 가능한 원형 통화 버튼 */}
      <button
        onClick={handleMainButtonClick}
        className="absolute top-24 left-1/2 transform -translate-x-1/2 w-48 h-48 rounded-full focus:outline-none focus:ring-4 focus:ring-cyan-300 transition-all duration-300 hover:scale-105 group"
      >
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-300 via-purple-300 to-purple-400 p-1">
          <div className="w-full h-full rounded-full bg-gradient-to-br from-purple-200 via-pink-200 to-purple-300 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-transparent rounded-full"></div>
            
            <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg
              ${isRecording ? 'bg-red-500/90 backdrop-blur-sm' :
                minimaxConnected ? 'bg-green-500/80 backdrop-blur-sm' :
                'bg-white/40 backdrop-blur-sm group-hover:bg-white/50'
              }
            `}>
              {isRecording ? (
                <Square className="w-8 h-8 text-white" />
              ) : minimaxConnected ? (
                <Mic className="w-8 h-8 text-white" />
              ) : (
                <Play className="w-8 h-8 text-gray-700 group-hover:text-gray-800" />
              )}
            </div>
            
            {isConnected && (
              <>
                <div className="absolute inset-4 rounded-full border-2 border-white/30 animate-ping"></div>
                <div className="absolute inset-8 rounded-full border border-white/20 animate-pulse"></div>
              </>
            )}
          </div>
        </div>
      </button>

      {/* 중앙 상태 표시기 */}
      <div className="absolute top-80 left-1/2 transform -translate-x-1/2 z-10">
        <div className={`w-3 h-3 rounded-full ${
          isConnected && minimaxConnected ? 'bg-green-500' : 
          isConnected ? 'bg-yellow-500' : 'bg-gray-400'
        } mx-auto mb-2`}></div>
        <div className="text-center text-gray-600 text-sm font-medium">
          {isConnected && minimaxConnected ? '대화 중' : 
           isConnected ? 'MiniMax 연결 중' : '원을 터치하여 시작'}
        </div>
      </div>

      {/* 실시간 텍스트 표시 */}
      <div className="absolute bottom-40 left-4 right-4 z-10">
        <div className="bg-white/30 backdrop-blur-sm rounded-2xl p-4 min-h-[100px] flex flex-col items-center justify-center">
          {messages.length > 0 ? (
            <>
              <div className="flex items-center mb-2">
                <span className={`text-xs font-semibold mr-2 ${messages[messages.length-1].type === 'user' ? 'text-blue-500' : 'text-purple-600'}`}>{messages[messages.length-1].type === 'user' ? '나' : 'AI 친구'}</span>
                <span className="text-xs text-gray-500">{messages[messages.length-1].timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <p className="text-gray-800 text-center leading-relaxed text-base break-words">
                {messages[messages.length-1].text}
              </p>
            </>
          ) : (
            <p className="text-gray-800 text-center leading-relaxed">{currentText}</p>
          )}
        </div>
        {isSpeaking && (
          <div className="flex justify-center mt-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span className="ml-2 text-sm text-gray-600">AI 응답 중...</span>
          </div>
        )}
      </div>

      {/* 하단 컨트롤 버튼 */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex items-center space-x-6 z-10">
        <button
          className="w-14 h-14 rounded-full bg-white/30 backdrop-blur-sm flex items-center justify-center text-gray-700 hover:bg-white/40 transition-all"
          disabled
        >
          <Mic className="w-6 h-6" />
        </button>
        <button
          className="w-14 h-14 rounded-full bg-white/30 backdrop-blur-sm flex items-center justify-center text-gray-700 hover:bg-white/40 transition-all"
          disabled
        >
          <Camera className="w-6 h-6" />
        </button>
        <button
          className="w-14 h-14 rounded-full bg-white/30 backdrop-blur-sm flex items-center justify-center text-gray-700 hover:bg-white/40 transition-all"
          disabled
        >
          <Volume2 className="w-6 h-6" />
        </button>
      </div>

      {/* 대화 내용 사이드바 */}
      {showConversation && (
        <div className="absolute inset-0 z-50 flex">
          {/* 반투명 배경 (클릭하면 닫기) */}
          <div 
            className="flex-1 bg-black/20 backdrop-blur-sm"
            onClick={() => setShowConversation(false)}
          />
          
          {/* 사이드바 */}
          <div className="w-80 h-full bg-gradient-to-br from-purple-200/90 via-pink-100/90 to-purple-100/80 backdrop-blur-2xl flex flex-col shadow-2xl animate-slide-in-right rounded-l-3xl">
            {/* 헤더 */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-800">대화 내용</h2>
              <button
                onClick={() => setShowConversation(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
            
            {/* 메시지 목록 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-8">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>아직 대화 내용이 없습니다</p>
                  <p className="text-sm mt-2">음성 대화를 시작해보세요</p>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] px-4 py-3 rounded-3xl shadow-md ${
                        message.type === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-white/80 text-gray-900'
                      }`}
                      style={{ boxShadow: '0 2px 12px 0 rgba(80, 80, 160, 0.10)' }}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-semibold ${message.type === 'user' ? 'text-white/80' : 'text-purple-600/80'}`}>{message.type === 'user' ? '나' : 'AI 친구'}</span>
                        <span className={`text-xs ml-2 ${message.type === 'user' ? 'text-white/60' : 'text-gray-500/80'}`}>{message.timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <div className="text-sm leading-relaxed break-words">
                        {message.text}
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {/* 실시간 상태 표시 */}
              {isRecording && (
                <div className="flex justify-end">
                  <div className="bg-red-50 border border-red-200 px-4 py-3 rounded-2xl max-w-[85%] shadow-sm">
                    <div className="flex items-center space-x-3">
                      <div className="flex space-x-1">
                        <div className="w-1.5 h-4 bg-red-500 rounded-sm animate-pulse"></div>
                        <div className="w-1.5 h-6 bg-red-500 rounded-sm animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-1.5 h-5 bg-red-500 rounded-sm animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-xs text-red-600 font-medium">녹음 중...</span>
                    </div>
                  </div>
                </div>
              )}
              
              {isSpeaking && (
                <div className="flex justify-start">
                  <div className="bg-blue-50 border border-blue-200 px-4 py-3 rounded-2xl max-w-[85%] shadow-sm">
                    <div className="flex items-center space-x-3">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-xs text-blue-600 font-medium">AI가 말하고 있습니다...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* 하단 정보 */}
            <div className="p-4 bg-gray-50/70 border-t border-gray-200 rounded-b-3xl">
              <div className="text-sm text-gray-600 text-center">
                <div className="flex items-center justify-center space-x-4">
                  <span>메시지: {messages.length}개</span>
                  <span className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-1 ${
                      isConnected && minimaxConnected ? 'bg-green-500' : 
                      isConnected ? 'bg-yellow-500' : 'bg-gray-400'
                    }`}></div>
                    {isConnected && minimaxConnected ? '연결됨' : 
                     isConnected ? '연결 중' : '연결 끊김'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 애니메이션 스타일 */}
      <style>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
        
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default RealtimeChat;