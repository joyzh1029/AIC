import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, Phone, PhoneOff, Volume2, VolumeX, Settings, Loader2 } from 'lucide-react';

const RealtimeCallInterface = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [messages, setMessages] = useState([]);
  const [audioLevel, setAudioLevel] = useState(0);
  const [callDuration, setCallDuration] = useState(0);
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const callStartTimeRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const mediaRecorderRef = useRef(null);

  // 初始化音频上下文
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // 格式化时长
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const addMessage = useCallback((role, text) => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      role,
      text,
      timestamp: new Date().toLocaleTimeString()
    }]);
  }, []);

  // 断开连接
  const disconnect = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
    setCallDuration(0);
    callStartTimeRef.current = null;
    setAudioLevel(0);
  }, []);

  // 获取用户媒体流
  const getUserMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      streamRef.current = stream;
      
      const analyser = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyser);
      
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const checkAudioLevel = () => {
        if (streamRef.current) {
          analyser.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average / 255);
          requestAnimationFrame(checkAudioLevel);
        }
      };
      checkAudioLevel();
      
      return stream;
    } catch (error) {
      console.error('获取麦克风失败:', error);
      addMessage('error', '获取麦克风失败，请检查权限');
      throw error;
    }
  };

  // 播放音频队列
  const playAudioQueue = useCallback(async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    
    isPlayingRef.current = true;
    const audioData = audioQueueRef.current.shift();
    
    try {
      const audioBuffer = await audioContextRef.current.decodeAudioData(audioData);
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      
      if (isSpeakerOn) {
        source.connect(audioContextRef.current.destination);
      }
      
      source.onended = () => {
        isPlayingRef.current = false;
        playAudioQueue();
      };
      
      source.start();
    } catch (error) {
      console.error('音频播放失败:', error);
      isPlayingRef.current = false;
      playAudioQueue();
    }
  }, [isSpeakerOn]);

  // 处理WebSocket消息
  const handleWebSocketMessage = useCallback((event) => {
    if (typeof event.data === 'string') {
      try {
        const msg = JSON.parse(event.data);
        switch(msg.type) {
          case 'transcript':
            addMessage('user', msg.text);
            break;
          case 'status':
            addMessage('status', msg.message);
            break;
          case 'error':
            addMessage('error', msg.message);
            break;
          default:
            console.log('收到未知消息:', msg);
        }
      } catch (error) {
        console.error('解析消息失败:', error);
      }
    } else {
      audioQueueRef.current.push(event.data);
      playAudioQueue();
    }
  }, [addMessage, playAudioQueue]);

  // 开始音频流
  const startAudioStream = () => {
    if (!streamRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const recorder = new MediaRecorder(streamRef.current);
    mediaRecorderRef.current = recorder;
    
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0 && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(event.data);
      }
    };
    
    recorder.start(250);
  };

  // 连接WebSocket
  const connectWebSocket = useCallback(async () => {
    if (wsRef.current) return;

    setIsConnecting(true);
    
    try {
      await getUserMedia();
      
      const wsUrl = `ws://localhost:3001`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket连接成功');
        setIsConnected(true);
        setIsConnecting(false);
        callStartTimeRef.current = Date.now();
        addMessage('status', '连接成功，请开始说话');
        startAudioStream();
      };

      ws.onmessage = handleWebSocketMessage;

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        addMessage('error', 'WebSocket连接出错');
        disconnect();
      };

      ws.onclose = () => {
        addMessage('status', '连接已断开');
        disconnect();
      };

    } catch (error) {
      console.error('连接失败:', error);
      addMessage('error', '无法连接到服务器');
      setIsConnecting(false);
    }
  }, [addMessage, disconnect, handleWebSocketMessage]);

  // 切换静音
  const toggleMute = () => {
    setIsMuted(prev => {
      const isMuted = !prev;
      if (streamRef.current) {
        streamRef.current.getAudioTracks().forEach(track => {
          track.enabled = !isMuted;
        });
      }
      return isMuted;
    });
  };

  // 切换扬声器
  const toggleSpeaker = () => {
    setIsSpeakerOn(!isSpeakerOn);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl overflow-hidden">
          {/* 通话状态 */}
          <div className="p-6">
            <div className="text-center">
              <div className="text-sm text-white/70 mb-2">
                {isConnected ? '通话中' : isConnecting ? '连接中...' : '未连接'}
              </div>
              <div className="text-4xl font-bold text-white">{formatDuration(callDuration)}</div>
              
              {/* 音频电平指示器 */}
              {isConnected && (
                <div className="mt-4 h-2 bg-white/20 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-400 to-blue-400 transition-all duration-100"
                    style={{ width: `${audioLevel * 100}%` }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* 消息区域 */}
          <div className="h-64 overflow-y-auto p-4 space-y-2 border-y border-white/20">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs px-4 py-2 rounded-lg ${ 
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : msg.role === 'assistant'
                      ? 'bg-white/20 text-white'
                      : msg.role === 'error'
                      ? 'bg-red-600/50 text-white'
                      : 'bg-gray-600/50 text-white/70 text-sm'
                  }`}
                >
                  <div>{msg.text}</div>
                  <div className="text-xs opacity-70 mt-1">{msg.timestamp}</div>
                </div>
              </div>
            ))}
          </div>

          {/* 控制按钮 */}
          <div className="p-6">
            <div className="flex justify-center gap-4">
              <button
                onClick={toggleMute}
                disabled={!isConnected}
                className={`p-4 rounded-full transition-all ${ isConnected ? (isMuted ? 'bg-red-600 hover:bg-red-700' : 'bg-white/20 hover:bg-white/30') : 'bg-white/10 cursor-not-allowed' }`}
              >
                {isMuted ? <MicOff className="w-6 h-6 text-white" /> : <Mic className="w-6 h-6 text-white" />}
              </button>

              <button
                onClick={isConnected ? disconnect : connectWebSocket}
                disabled={isConnecting}
                className={`p-6 rounded-full transition-all ${ isConnected ? 'bg-red-600 hover:bg-red-700' : (isConnecting ? 'bg-gray-600 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700') }`}
              >
                {isConnecting ? <Loader2 className="w-8 h-8 text-white animate-spin" /> : (isConnected ? <PhoneOff className="w-8 h-8 text-white" /> : <Phone className="w-8 h-8 text-white" />)}
              </button>

              <button
                onClick={toggleSpeaker}
                disabled={!isConnected}
                className={`p-4 rounded-full transition-all ${ isConnected ? (isSpeakerOn ? 'bg-white/20 hover:bg-white/30' : 'bg-red-600 hover:bg-red-700') : 'bg-white/10 cursor-not-allowed' }`}
              >
                {isSpeakerOn ? <Volume2 className="w-6 h-6 text-white" /> : <VolumeX className="w-6 h-6 text-white" />}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4 text-center text-white/70 text-sm">
          <p>请确保已允许浏览器访问麦克风权限</p>
        </div>
      </div>
    </div>
  );
};

export default RealtimeCallInterface;