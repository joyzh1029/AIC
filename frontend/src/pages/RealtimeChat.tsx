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

// 연결 디버그 정보 컴포넌트
const ConnectionDebugInfo: React.FC<{
  isVisible: boolean;
  onClose: () => void;
}> = ({ isVisible, onClose }) => {
  if (!isVisible) return null;

  const debugInfo = {
    hostname: window.location.hostname,
    port: window.location.port,
    protocol: window.location.protocol,
    environment: process.env.NODE_ENV || 'development',
    wsProtocol: window.location.protocol === 'https:' ? 'wss:' : 'ws:',
    recommendedPort: process.env.NODE_ENV === 'development' ? '8000' : window.location.port,
  };

  const wsUrl = `${debugInfo.wsProtocol}//${debugInfo.hostname}${debugInfo.recommendedPort ? ':' + debugInfo.recommendedPort : ''}/ws/realtime-chat`;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white/90 backdrop-blur-md rounded-3xl p-6 max-w-md w-full shadow-2xl border border-white/30">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-800">연결 정보</h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-700" />
          </button>
        </div>
        
        <div className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <span className="font-medium text-gray-600">호스트:</span>
            <span className="text-gray-800">{debugInfo.hostname}</span>
            
            <span className="font-medium text-gray-600">포트:</span>
            <span className="text-gray-800">{debugInfo.port || '기본'}</span>
            
            <span className="font-medium text-gray-600">프로토콜:</span>
            <span className="text-gray-800">{debugInfo.protocol}</span>
            
            <span className="font-medium text-gray-600">환경:</span>
            <span className="text-gray-800">{debugInfo.environment}</span>
            
            <span className="font-medium text-gray-600">WS 프로토콜:</span>
            <span className="text-gray-800">{debugInfo.wsProtocol}</span>
          </div>
          
          <div className="mt-4 p-3 bg-gray-100 rounded-xl">
            <span className="font-medium text-gray-600 block mb-1">WebSocket URL:</span>
            <code className="text-xs text-blue-600 break-all">{wsUrl}</code>
          </div>
          
          <div className="mt-4 p-3 bg-yellow-100 rounded-xl">
            <span className="font-medium text-yellow-800 block mb-1">백엔드 설정 확인:</span>
            <ul className="text-xs text-yellow-700 space-y-1">
              <li>• FastAPI 서버가 포트 8000에서 실행 중인지 확인</li>
              <li>• config.py의 설정이 올바른지 확인</li>
              <li>• MINIMAX_API_KEY가 .env에 설정되었는지 확인</li>
              <li>• CORS 설정이 올바른지 확인</li>
            </ul>
          </div>
        </div>
        
        <button
          onClick={onClose}
          className="w-full mt-4 bg-blue-500 text-white py-2 rounded-xl hover:bg-blue-600 transition-colors"
        >
          확인
        </button>
      </div>
    </div>
  );
};

const RealtimeChat: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [minimaxConnected, setMinimaxConnected] = useState(false);
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
      text: '안녕하세요! 저는 당신의 AI 친구입니다. 무엇을 도와드릴까요?',
      timestamp: new Date(Date.now() - 60000),
      isTranslated: false
    }
  ]);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const webSocketRef = useRef<WebSocket | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [audioProcessing, setAudioProcessing] = useState(false);
  const [showDebugInfo, setShowDebugInfo] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recordedAudioChunks, setRecordedAudioChunks] = useState<Blob[]>([]);
  
  // 音频增量数据累积 - 使用 useRef 避免状态更新延迟
  const audioBufferRef = useRef<string>('');
  
  // 音频分块接收状态
  const [welcomeAudioChunks, setWelcomeAudioChunks] = useState<{[key: number]: string}>({});
  const [expectedChunks, setExpectedChunks] = useState<number>(0);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 组件卸载时清理WebSocket连接和摄像头
  useEffect(() => {
    return () => {
      if (webSocketRef.current) {
        if (webSocketRef.current.readyState === WebSocket.OPEN) {
          webSocketRef.current.send(JSON.stringify({type: 'disconnect_minimax'}));
          webSocketRef.current.close();
        }
        webSocketRef.current = null;
      }
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  const handleConnect = () => {
    const nextConnectionState = !isConnected;
    
    if (nextConnectionState) {
      // 연결 시작
      setIsConnected(true);
      setCurrentText('연결 중...');
      setConnectionError(null);
      
      // 새 WebSocket 연결 생성
      const clientId = `user-${Date.now()}`;
      // 개발환경에서는 8181 포트, 프로덕션에서는 현재 포트 사용
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsPort = process.env.NODE_ENV === 'development' ? '8181' : window.location.port;
      const wsUrl = `${wsProtocol}//${window.location.hostname}${wsPort ? ':' + wsPort : ''}/ws/realtime-chat?client_id=${clientId}`;
      
      console.log('WebSocket 연결 시도:', wsUrl);
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket 연결 성공');
        setCurrentText('서버에 연결됨. MiniMax 연결 중...');
        
        // MiniMax 연결 요청 메시지 전송 - config.py의 기본 모델 사용
        ws.send(JSON.stringify({
          type: 'connect_minimax',
          model: 'abab6.5s-chat' // config.py에서 설정한 기본 모델과 일치
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket 메시지 수신:', data);
          
          switch (data.type) {
            case 'ping':
              // 심박수 메시지 처리 - 연결 유지를 위한 것이므로 무시
              break;
              
            case 'connection_status':
              setMinimaxConnected(data.connected);
              if (data.connected) {
                setCurrentText('MiniMax에 연결되었습니다! 환영 메시지를 준비하고 있습니다...');
                setIsListening(true);
                setAudioProcessing(true);
                // 이제 환영 메시지는 서버에서 자동으로 생성됨
              } else {
                setCurrentText('MiniMax 연결이 끊어졌습니다.');
                setIsListening(false);
                if (data.message) {
                  setConnectionError(data.message);
                }
              }
              break;
              
            case 'welcome_generating':
              setCurrentText(data.message);
              setAudioProcessing(true);
              break;
              
            case 'welcome_text_complete':
              // 환영 메시지 텍스트 표시
              addAvatarMessage(data.text);
              setCurrentText(data.text);
              break;
              
            case 'welcome_audio_chunk':
              // 환영 메시지 음성 청크 수신
              const chunkIndex = data.chunk_index;
              const totalChunks = data.total_chunks;
              const audioChunk = data.audio;
              
              console.log(`음성 청크 수신: ${chunkIndex + 1}/${totalChunks}, 길이: ${audioChunk.length}`);
              
              // 청크 저장
              setWelcomeAudioChunks(prev => ({
                ...prev,
                [chunkIndex]: audioChunk
              }));
              setExpectedChunks(totalChunks);
              
              // 모든 청크를 받았는지 확인
              setWelcomeAudioChunks(currentChunks => {
                const updatedChunks = { ...currentChunks, [chunkIndex]: audioChunk };
                const receivedCount = Object.keys(updatedChunks).length;
                
                if (receivedCount === totalChunks) {
                  // 모든 청크 수신 완료, 결합하여 재생
                  let completeAudio = '';
                  for (let i = 0; i < totalChunks; i++) {
                    completeAudio += updatedChunks[i] || '';
                  }
                  
                  console.log(`모든 음성 청크 수신 완료! 총 길이: ${completeAudio.length}`);
                  
                  // Base64 데이터 정리 및 검증
                  const cleanedAudio = completeAudio.replace(/[^A-Za-z0-9+/=]/g, '');
                  let paddedAudio = cleanedAudio;
                  const padding = paddedAudio.length % 4;
                  if (padding > 0) {
                    paddedAudio += '='.repeat(4 - padding);
                  }
                  
                  // Base64 디코딩 테스트
                  try {
                    const testDecode = atob(paddedAudio);
                    console.log(`✅ 결합된 음성 Base64 디코딩 성공: ${testDecode.length}바이트`);
                    playAudioResponse(paddedAudio);
                    setCurrentText('MiniMax AI가 준비되었습니다! 대화를 시작하세요.');
                  } catch (error) {
                    console.error(`❌ 결합된 음성 Base64 디코딩 실패:`, error);
                    console.error(`처리된 데이터 길이: ${paddedAudio.length}, 샘플: ${paddedAudio.substring(0, 100)}...`);
                    setConnectionError('음성 재생에 실패했습니다.');
                  }
                  
                  // 청크 데이터 정리
                  setWelcomeAudioChunks({});
                  setExpectedChunks(0);
                }
                
                return updatedChunks;
              });
              break;
              
            case 'welcome_audio_complete':
              // 환영 메시지 음성 완료 (분할 전송이 아닌 경우 또는 완료 신호)
              setAudioProcessing(false);
              if (data.audio) {
                console.log('환영 메시지 음성 재생 시작 (단일 메시지) - 길이:', data.audio.length);
                playAudioResponse(data.audio);
              }
              setCurrentText('MiniMax AI가 준비되었습니다! 대화를 시작하세요.');
              break;
              
            case 'minimax_response':
              console.log('MiniMax 응답:', data.data);
              
              // 处理不同类型的MiniMax响应
              if (data.data) {
                const responseType = data.data.type;
                
                if (responseType === 'session.created') {
                  console.log('MiniMax 세션이 생성되었습니다');
                  // 会话创建成功，不需要特别处理
                  
                } else if (responseType === 'text_delta') {
                  // 处理文本增量更新（实时显示）
                  const deltaText = data.data.text || '';
                  if (deltaText) {
                    setCurrentText(prev => prev + deltaText);
                  }
                  
                } else if (responseType === 'text_complete') {
                  // 处理完整文本响应
                  const completeText = data.data.text || '';
                  if (completeText && completeText.trim()) {
                    setAudioProcessing(false);
                    addAvatarMessage(completeText);
                  }
                  
                } else if (responseType === 'response_complete') {
                  // 处理响应完成
                  const responseText = data.data.text || '';
                  if (responseText && responseText.trim()) {
                    setAudioProcessing(false);
                    addAvatarMessage(responseText);
                  }
                  
                } else if (responseType === 'audio_delta') {
                  // 累积音频増量数据
                  const deltaAudio = data.data.audio || '';
                  if (deltaAudio) {
                    audioBufferRef.current += deltaAudio;
                    // 샘플 데이터 출력 (처음 50자, 마지막 50자)
                    const sample = deltaAudio.length > 100 ? 
                      deltaAudio.substring(0, 50) + '...' + deltaAudio.substring(deltaAudio.length - 50) : 
                      deltaAudio;
                    console.log('수신된 음성 증분 데이터 - 길이:', deltaAudio.length, '총 길이:', audioBufferRef.current.length, '샘플:', sample);
                  }
                  
                } else if (responseType === 'audio_complete') {
                  // 处理完整音频响应 - 使用累积的音频数据
                  if (audioBufferRef.current) {
                    console.log('음성 재생 시작 - 전체 길이:', audioBufferRef.current.length);
                    setAudioProcessing(false);
                    playAudioResponse(audioBufferRef.current);
                    // 清空音频缓冲区
                    audioBufferRef.current = '';
                  } else {
                    console.log('빈 음성 데이터 - 텍스트 응답만 표시');
                    setAudioProcessing(false);
                  }
                  
                } else if (responseType === 'response.audio_transcript.done') {
                  // 处理音频转录完成事件
                  const transcript = data.data.transcript || '';
                  if (transcript && transcript.trim()) {
                    console.log('음성 전사 완료:', transcript);
                    addAvatarMessage(transcript);
                  }
                  
                } else if (responseType === 'response.output_item.done') {
                  // 处理输出项完成事件
                  console.log('응답 항목 완료');
                  // 这个事件通常标志着响应的结束，不需要特别处理
                  
                } else {
                  // 处理其他类型的响应（兼容性处理）
                  let responseText = '';
                  
                  if (data.data.type === 'response.text.done') {
                    responseText = data.data.text || '';
                  } else if (data.data.type === 'response.done') {
                    // 从response.done事件中提取文本
                    const response = data.data.response;
                    if (response && response.output) {
                      for (const item of response.output) {
                        if (item.type === 'message' && item.role === 'assistant') {
                          for (const content of item.content || []) {
                            if (content.type === 'text') {
                              responseText = content.text || '';
                              break;
                            }
                          }
                        }
                      }
                    }
                  } else if (data.data.text) {
                    responseText = data.data.text;
                  } else if (data.data.message) {
                    responseText = data.data.message;
                  }
                  
                  if (responseText && responseText.trim()) {
                    setAudioProcessing(false);
                    addAvatarMessage(responseText);
                  } else {
                    console.log('빈 응답 또는 인식할 수 없는 응답 형태:', data.data);
                  }
                }
              }
              break;
              
            case 'error':
              setConnectionError(data.message);
              setAudioProcessing(false);
              console.error('WebSocket 오류:', data.message);
              addAvatarMessage(`오류가 발생했습니다: ${data.message}`);
              break;
              
            default:
              console.log('알 수 없는 메시지 타입:', data);
          }
        } catch (error) {
          console.error('WebSocket 메시지 파싱 오류:', error);
          setConnectionError('메시지 처리 중 오류가 발생했습니다.');
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket 연결 종료');
        setIsConnected(false);
        setMinimaxConnected(false);
        setIsListening(false);
        setAudioProcessing(false);
        setCurrentText('연결이 종료되었습니다.');
        if (isConnected) {
          setConnectionError('서버와의 연결이 종료되었습니다.');
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket 오류:', error);
        setConnectionError('서버 연결에 오류가 발생했습니다.');
        setAudioProcessing(false);
      };
      
      webSocketRef.current = ws;
    } else {
      // 연결 종료
      if (webSocketRef.current) {
        if (webSocketRef.current.readyState === WebSocket.OPEN) {
          webSocketRef.current.send(JSON.stringify({type: 'disconnect_minimax'}));
          webSocketRef.current.close();
        }
        webSocketRef.current = null;
      }
      
      setIsConnected(false);
      setMinimaxConnected(false);
      setCurrentText('안녕하세요');
      setIsListening(false);
      setIsRecording(false);
      setIsSpeaking(false);
      setAudioProcessing(false);
      setConnectionError(null);
      
      // 清空音频缓冲区
      audioBufferRef.current = '';
    }
  };

  const handleMicToggle = async () => {
    if (isConnected && minimaxConnected) {
      if (!isRecording) {
        // 녹음 시작
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              sampleRate: 24000, // MiniMax API 요구사항: 24kHz
              channelCount: 1     // MiniMax API 요구사항: 모노 오디오
            } 
          });
          
          // AudioContext를 사용하여 PCM16 데이터 처리
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
            sampleRate: 24000
          });
          
          const source = audioContext.createMediaStreamSource(stream);
          const processor = audioContext.createScriptProcessor(4096, 1, 1);
          
          const audioChunks: Float32Array[] = [];
          
          processor.onaudioprocess = (event) => {
            const inputData = event.inputBuffer.getChannelData(0);
            // Float32Array 복사
            const chunk = new Float32Array(inputData.length);
            chunk.set(inputData);
            audioChunks.push(chunk);
          };
          
          source.connect(processor);
          processor.connect(audioContext.destination);
          
          // 녹음 시작
          setIsRecording(true);
          setCurrentText('🎤 말씀해 주세요... (다시 클릭하여 중지)');
          
          // 오디오 컨텍스트와 스트림을 상태로 저장
          setMediaRecorder({ audioContext, processor, source, stream, audioChunks } as any);
          
          console.log('음성 녹음 시작 (PCM16 형식)');
          
        } catch (error) {
          console.error('마이크 접근 실패:', error);
          setConnectionError('마이크에 접근할 수 없습니다. 브라우저 설정을 확인해주세요.');
        }
      } else {
        // 녹음 중지
        if (mediaRecorder) {
          const { audioContext, processor, source, stream, audioChunks } = mediaRecorder as any;
          
          // 오디오 처리 중지
          processor.disconnect();
          source.disconnect();
          audioContext.close();
          
          // 스트림 정리
          stream.getTracks().forEach((track: MediaStreamTrack) => track.stop());
          
          // 오디오 데이터 처리 및 전송
          if (audioChunks.length > 0) {
            await processAndSendAudio(audioChunks);
          }
          
          setMediaRecorder(null);
        }
        
        setIsRecording(false);
        setCurrentText('🔄 음성을 처리하고 있습니다...');
        setAudioProcessing(true);
      }
    }
     };

   // Float32Array를 PCM16으로 변환하는 함수 (MiniMax API 규격)
   const floatTo16BitPCM = (float32Array: Float32Array): ArrayBuffer => {
     const buffer = new ArrayBuffer(float32Array.length * 2);
     const view = new DataView(buffer);
     let offset = 0;
     for (let i = 0; i < float32Array.length; i++, offset += 2) {
       let s = Math.max(-1, Math.min(1, float32Array[i]));
       view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
     }
     return buffer;
   };

   // Float32Array를 base64로 인코딩하는 함수
   const base64EncodeAudio = (float32Array: Float32Array): string => {
     const arrayBuffer = floatTo16BitPCM(float32Array);
     let binary = '';
     let bytes = new Uint8Array(arrayBuffer);
     const chunkSize = 0x8000; // 32KB chunk size
     for (let i = 0; i < bytes.length; i += chunkSize) {
       let chunk = bytes.subarray(i, i + chunkSize);
       binary += String.fromCharCode.apply(null, Array.from(chunk));
     }
     return btoa(binary);
   };

   // 오디오 데이터를 처리하고 서버로 전송하는 함수
   const processAndSendAudio = async (audioChunks: Float32Array[]) => {
     try {
       // 모든 오디오 청크를 하나로 합치기
       let totalLength = 0;
       for (const chunk of audioChunks) {
         totalLength += chunk.length;
       }
       
       const combinedAudio = new Float32Array(totalLength);
       let offset = 0;
       for (const chunk of audioChunks) {
         combinedAudio.set(chunk, offset);
         offset += chunk.length;
       }
       
       // PCM16 및 base64로 변환
       const base64Audio = base64EncodeAudio(combinedAudio);
       
       if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
         // MiniMax API 형식에 맞게 전송
         webSocketRef.current.send(JSON.stringify({
           type: 'audio_message',
           audio_data: base64Audio,
           format: 'pcm16',
           sample_rate: 24000,
           channels: 1
         }));
         
         console.log('PCM16 오디오 데이터 전송 완료, 샘플 수:', combinedAudio.length);
         
         // 사용자 메시지로 표시
         addUserMessage('🎵 음성 메시지가 전송되었습니다.');
       } else {
         throw new Error('WebSocket 연결이 끊어졌습니다.');
       }
       
     } catch (error) {
       console.error('오디오 처리 및 전송 실패:', error);
       setConnectionError('음성 메시지 처리에 실패했습니다.');
       setAudioProcessing(false);
     }
   };

   // 오디오 데이터를 서버로 전송하는 함수 (구버전 - 호환성용)
   const sendAudioToServer = async (audioBlob: Blob) => {
    try {
      // Blob을 Base64로 변환
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64Audio = reader.result as string;
        const base64Data = base64Audio.split(',')[1]; // data:audio/webm;base64, 부분 제거
        
        if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
          // 오디오 데이터를 WebSocket으로 전송
          webSocketRef.current.send(JSON.stringify({
            type: 'audio_message',
            audio_data: base64Data,
            format: 'webm',
            encoding: 'opus'
          }));
          
          console.log('오디오 데이터 전송 완료, 크기:', audioBlob.size, 'bytes');
          
          // 사용자 메시지로 표시
          addUserMessage('🎵 음성 메시지가 전송되었습니다.');
        } else {
          throw new Error('WebSocket 연결이 끊어졌습니다.');
        }
      };
      
      reader.onerror = () => {
        throw new Error('오디오 데이터 변환 실패');
      };
      
      reader.readAsDataURL(audioBlob);
      
         } catch (error) {
       console.error('오디오 전송 실패:', error);
       setConnectionError('음성 메시지 전송에 실패했습니다.');
       setAudioProcessing(false);
     }
   };

   // AI 음성 응답을 재생하는 함수
   const playAudioResponse = async (base64Audio: string) => {
     try {
       // Base64 데이터 정리 - 공백 및 잘못된 문자 제거
       const cleanedBase64 = base64Audio.replace(/[^A-Za-z0-9+/=]/g, '');
       
       // Base64 패딩 확인 및 수정
       let paddedBase64 = cleanedBase64;
       const padding = paddedBase64.length % 4;
       if (padding > 0) {
         paddedBase64 += '='.repeat(4 - padding);
       }
       
       console.log('원본 길이:', base64Audio.length, '정리된 길이:', paddedBase64.length);
       
       // Base64 PCM16 데이터를 ArrayBuffer로 변환
       const audioData = atob(paddedBase64);
       const arrayBuffer = new ArrayBuffer(audioData.length);
       const uint8Array = new Uint8Array(arrayBuffer);
       
       for (let i = 0; i < audioData.length; i++) {
         uint8Array[i] = audioData.charCodeAt(i);
       }
       
       // PCM16 데이터를 AudioContext로 재생
       const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
         sampleRate: 24000
       });
       
       // PCM16 데이터를 Float32Array로 변환
       const pcm16Data = new Int16Array(arrayBuffer);
       const audioBuffer = audioContext.createBuffer(1, pcm16Data.length, 24000);
       const channelData = audioBuffer.getChannelData(0);
       
       // Int16을 Float32로 변환 (-1.0 to 1.0 범위)
       for (let i = 0; i < pcm16Data.length; i++) {
         channelData[i] = pcm16Data[i] / 32768.0;
       }
       
       // 오디오 재생
       const source = audioContext.createBufferSource();
       source.buffer = audioBuffer;
       source.connect(audioContext.destination);
       source.start();
       
       console.log('AI 음성 응답 재생 시작 (PCM16)');
       
     } catch (error) {
       console.error('음성 재생 실패:', error);
       setConnectionError('음성 재생에 실패했습니다.');
       
       // 대체 방법: 브라우저 호환성 문제 시 WAV 형식으로 시도
       try {
         console.log('대체 오디오 재생 방법 시도...');
         
         // 여기서도 동일한 Base64 정리 과정 적용
         const cleanedBase64 = base64Audio.replace(/[^A-Za-z0-9+/=]/g, '');
         let paddedBase64 = cleanedBase64;
         const padding = paddedBase64.length % 4;
         if (padding > 0) {
           paddedBase64 += '='.repeat(4 - padding);
         }
         
         const audioData = atob(paddedBase64);
         const arrayBuffer = new ArrayBuffer(audioData.length);
         const uint8Array = new Uint8Array(arrayBuffer);
         
         for (let i = 0; i < audioData.length; i++) {
           uint8Array[i] = audioData.charCodeAt(i);
         }
         
         // WAV 헤더 추가하여 브라우저가 인식할 수 있도록 함
         const audioBlob = new Blob([arrayBuffer], { type: 'audio/wav' });
         const audioUrl = URL.createObjectURL(audioBlob);
         
         const audio = new Audio(audioUrl);
         audio.onended = () => {
           URL.revokeObjectURL(audioUrl);
         };
         
         await audio.play();
         console.log('대체 방법으로 오디오 재생 성공');
         
       } catch (fallbackError) {
         console.error('대체 오디오 재생도 실패:', fallbackError);
       }
     }
   };

  const handleSpeakerToggle = () => {
    if (isConnected && minimaxConnected) {
      setIsSpeaking(!isSpeaking);
    }
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
      console.log('업로드된 사진:', file);
      addUserMessage(`📷 사진이 업로드되었습니다: ${file.name}`);
      
      // TODO: 향후 이미지를 base64로 변환하여 MiniMax로 전송하는 기능 구현
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
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN && minimaxConnected) {
      try {
        setAudioProcessing(true);
        setCurrentText('AI가 응답을 준비하고 있습니다...');
        
        // 수정된 메시지 형태로 전송 - 후端 API에 맞게
        webSocketRef.current.send(JSON.stringify({
          type: 'user_message',
          text: text
        }));
      } catch (error) {
        console.error('메시지 전송 실패:', error);
        setConnectionError('메시지 전송에 실패했습니다.');
        setAudioProcessing(false);
      }
    } else {
      console.warn('WebSocket이 연결되어 있지 않거나 MiniMax가 연결되지 않았습니다.');
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

      {/* 채팅으로 돌아가는 화살표 버튼 */}
      <button
        onClick={() => navigate('/chat')}
        className="absolute top-12 left-4 bg-white/40 backdrop-blur-sm px-4 py-2 rounded-full flex items-center space-x-1 shadow-md hover:bg-white/60 transition-all z-20 hover:scale-105"
        title="채팅으로 돌아가기"
      >
        <ChevronLeft className="w-5 h-5 text-gray-700" />
        <span className="text-sm font-medium text-gray-800">채팅</span>
      </button>
      
      {/* 클릭 가능한 원형 통화 버튼 */}
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

      {/* 사진 업로드 선택 창 */}
      {showPhotoUpload && (
        <div className="absolute top-20 left-4 right-4 z-20">
          <div className="bg-white/20 backdrop-blur-md rounded-3xl p-6 shadow-2xl border border-white/30">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-800">사진 업로드</h3>
              <button
                onClick={() => setShowPhotoUpload(false)}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-700" />
              </button>
            </div>
            
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
      
      <div className="absolute top-12 right-4 flex justify-end items-center space-x-2 z-10">
        {/* 디버그 버튼 (개발 모드에서만 표시) */}
        {process.env.NODE_ENV === 'development' && (
          <button
            onClick={() => setShowDebugInfo(true)}
            className="bg-white/20 backdrop-blur-sm rounded-full px-3 py-1 text-xs text-gray-700 hover:bg-white/30 transition-colors"
          >
            🔧 디버그
          </button>
        )}
        
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
        <div className="bg-white/30 backdrop-blur-sm rounded-2xl p-4 min-h-[100px] flex items-center justify-center">
          <p className="text-gray-800 text-center leading-relaxed">
            {currentText}
          </p>
        </div>
        {(isListening || audioProcessing) && (
          <div className="flex justify-center mt-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span className="ml-2 text-sm text-gray-600">
              {audioProcessing ? 'AI 응답 중...' : '처리 중...'}
            </span>
          </div>
        )}
      </div>

      {/* 하단 컨트롤 버튼 */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex items-center space-x-6 z-10">
        {/* 마이크 버튼 */}
        <button
          onClick={handleMicToggle}
          disabled={!isConnected || !minimaxConnected}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            isRecording 
              ? 'bg-red-500 text-white shadow-lg' 
              : (isConnected && minimaxConnected)
                ? 'bg-white/30 backdrop-blur-sm text-gray-700 hover:bg-white/40' 
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isRecording ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
        </button>

        {/* 사진 촬영 버튼 */}
        <button
          onClick={() => setShowPhotoUpload(true)}
          disabled={!isConnected || !minimaxConnected}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            (isConnected && minimaxConnected)
              ? 'bg-white/30 backdrop-blur-sm text-gray-700 hover:bg-white/40' 
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          <Camera className="w-6 h-6" />
        </button>

        {/* 스피커 버튼 */}
        <button
          onClick={handleSpeakerToggle}
          disabled={!isConnected || !minimaxConnected}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            isSpeaking && isConnected && minimaxConnected
              ? 'bg-blue-500 text-white shadow-lg' 
              : (isConnected && minimaxConnected)
                ? 'bg-white/30 backdrop-blur-sm text-gray-700 hover:bg-white/40' 
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isSpeaking ? <Volume2 className="w-6 h-6" /> : <VolumeX className="w-6 h-6" />}
        </button>
      </div>

      {/* 대화 내용 사이드바 */}
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
            {isConnected && minimaxConnected && isListening && !audioProcessing && (
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
            
            {/* AI 응답 처리 중 표시 */}
            {audioProcessing && (
              <div className="flex justify-start">
                <div className="bg-blue-400/30 backdrop-blur-sm border border-blue-300/40 px-4 py-3 rounded-3xl max-w-[85%] shadow-lg">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs text-blue-800 font-medium">AI 친구</span>
                    <span className="text-xs text-blue-700">응답 중</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-xs text-blue-700">AI가 응답을 준비하고 있습니다...</span>
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

          {/* 수동 메시지 입력 */}
          <div className="p-4 bg-white/10 backdrop-blur-sm border-t border-white/20">
            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="메시지를 입력하세요..."
                className="flex-1 px-3 py-2 bg-white/20 backdrop-blur-sm border border-white/30 rounded-full text-gray-800 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
                disabled={!isConnected || !minimaxConnected}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                    addUserMessage(e.currentTarget.value.trim());
                    e.currentTarget.value = '';
                  }
                }}
              />
              <button
                onClick={() => {
                  const input = document.querySelector('input[type="text"]') as HTMLInputElement;
                  if (input && input.value.trim()) {
                    addUserMessage(input.value.trim());
                    input.value = '';
                  }
                }}
                disabled={!isConnected || !minimaxConnected}
                className={`px-4 py-2 rounded-full transition-all duration-300 ${
                  (isConnected && minimaxConnected)
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                전송
              </button>
            </div>
          </div>

          {/* 통계 정보 */}
          <div className="p-4 bg-white/10 backdrop-blur-sm border-t border-white/20">
            <div className="text-sm text-gray-700 text-center space-y-2">
              <div className="flex items-center justify-center space-x-4">
                <span>📊 메시지: {messages.length}개</span>
                <span>
                  {isConnected && minimaxConnected ? '✅ 연결됨' : 
                   isConnected ? '🔄 연결 중' : '❌ 연결 끊김'}
                </span>
              </div>
              {audioProcessing && (
                <div className="text-xs text-blue-600">
                  AI가 응답을 처리하고 있습니다...
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 연결 디버그 정보 모달 */}
      <ConnectionDebugInfo 
        isVisible={showDebugInfo} 
        onClose={() => setShowDebugInfo(false)} 
      />
    </div>
  );
};

export default RealtimeChat;