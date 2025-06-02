import { useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Mic, MicOff, PhoneOff, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

interface VoiceChatProps {
  avatarUrl?: string;
}

// 음성 채팅 상태 타입
type VoiceChatState = 'IDLE' | 'LISTENING' | 'AI_SPEAKING';

// API 응답 타입
interface STTResponse {
  result?: string;      // STT 결과
  aiResponse?: string;  // AI 답변
  ttsUrl?: string;      // TTS 오디오 파일 URL
}

const VoiceChat: React.FC<VoiceChatProps> = ({ avatarUrl }) => {
  const navigate = useNavigate();

  const {
    recording,
    audioBlob,
    error: recordingError,
    startRecording,
    stopRecording,
    reset,
  } = useVoiceRecorder();

  // 상태 관리
  const [sttResult, setSttResult] = useState("");
  const [aiResult, setAiResult] = useState("");
  const [ttsUrl, setTtsUrl] = useState("");
  const [voiceChatState, setVoiceChatState] = useState<VoiceChatState>('IDLE');
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [dotsCount, setDotsCount] = useState(1); // 점 개수 상태
  
  const audioRef = useRef<HTMLAudioElement>(null);

  // 초기 로드 애니메이션 제어
  useEffect(() => {
    // CSS 키프레임을 head에 추가
    const style = document.createElement('style');
    style.textContent = `
      @keyframes wave {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
      }
    `;
    document.head.appendChild(style);

    const timer = setTimeout(() => {
      setIsInitialLoad(false);
    }, 2000); // 2초 후 애니메이션 종료

    return () => {
      clearTimeout(timer);
      if (document.head.contains(style)) {
        document.head.removeChild(style);
      }
    };
  }, []);

  // 녹음 상태에 따른 상태 업데이트
  useEffect(() => {
    if (recording) {
      setVoiceChatState('LISTENING');
      setApiError(null); // 새 녹음 시작 시 에러 초기화
    } else if (voiceChatState === 'LISTENING' && !isProcessing) {
      setVoiceChatState('IDLE');
    }
  }, [recording, voiceChatState, isProcessing]);

  // AI 답변 중 점 애니메이션
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (voiceChatState === 'AI_SPEAKING') {
      interval = setInterval(() => {
        setDotsCount((prev) => (prev >= 3 ? 1 : prev + 1));
      }, 500); // 0.5초마다 점 개수 변경
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [voiceChatState]);

  // 마이크 on/off 토글
  const handleMicClick = async () => {
    if (recording) {
      stopRecording();
    } else {
      // 이전 결과 초기화 후 녹음 시작
      setSttResult("");
      setAiResult("");
      setTtsUrl("");
      setApiError(null);
      
      await startRecording();
    }
  };

  // 통화 종료 (나가기)
  const handleEndCall = () => {
    if (recording) {
      stopRecording();
    }
    navigate(-1);
  };

  // 서버 전송 & 결과 반영
  useEffect(() => {
    const uploadAudio = async (blob: Blob) => {
      setIsProcessing(true);
      
      try {
        // AI 처리 중 상태로 변경
        setVoiceChatState('AI_SPEAKING');
        
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");

        const response = await fetch("http://localhost:8181/api/stt", {
          method: "POST",
          body: formData,
        });

        if (response.ok) {
          const data: STTResponse = await response.json();
          setSttResult(data.result || "");
          setAiResult(data.aiResponse || "");
          setTtsUrl(data.ttsUrl || "");
          setApiError(null);
        } else {
          const errorText = await response.text();
          console.error("음성 업로드 실패:", response.status, errorText);
          setApiError(`서버 오류 (${response.status}): 다시 시도해주세요.`);
          setVoiceChatState('IDLE');
        }
      } catch (err) {
        console.error("네트워크 오류:", err);
        setApiError("네트워크 연결을 확인해주세요.");
        setVoiceChatState('IDLE');
      } finally {
        setIsProcessing(false);
      }
    };

    if (audioBlob) {
      uploadAudio(audioBlob);
      reset(); // 사용 후 초기화
    }
  }, [audioBlob, reset]);

  // TTS URL이 생기면 자동 재생
  useEffect(() => {
    if (ttsUrl && audioRef.current) {
      // 절대 URL로 변환 (상대 경로인 경우)
      const fullTtsUrl = ttsUrl.startsWith('http') 
        ? ttsUrl 
        : `http://localhost:8181${ttsUrl}`;
      
      audioRef.current.src = fullTtsUrl;
      audioRef.current.play().catch(error => {
        console.error('TTS 재생 실패:', error);
        setApiError("음성 재생에 실패했습니다.");
        setVoiceChatState('IDLE');
      });
    }
  }, [ttsUrl]);

  // 오디오 재생 완료 시 IDLE 상태로 복귀
  const handleAudioEnded = () => {
    setVoiceChatState('IDLE');
    setDotsCount(1); // 점 개수 초기화
  };

  // 오디오 재생 오류 처리
  const handleAudioError = () => {
    console.error('TTS 오디오 재생 오류');
    setApiError("음성 재생 중 오류가 발생했습니다.");
    setVoiceChatState('IDLE');
    setDotsCount(1); // 점 개수 초기화
  };

  // 상태별 UI 스타일 및 텍스트
  const getStateConfig = () => {
    if (recordingError) {
      return {
        bgColor: 'bg-red-500',
        pulseClass: '',
        statusText: recordingError,
        statusColor: 'text-red-600'
      };
    }

    switch (voiceChatState) {
      case 'LISTENING':
        return {
          bgColor: 'bg-blue-500',
          pulseClass: 'animate-pulse',
          statusText: '듣고 있어요...',
          statusColor: 'text-blue-600'
        };
      case 'AI_SPEAKING':
        return {
          bgColor: 'bg-green-500',
          pulseClass: '', // bounce 애니메이션 제거
          statusText: `AI가 답변중${'.'.repeat(dotsCount)}`, // 점 개수에 따라 동적 생성
          statusColor: 'text-green-600'
        };
      default: // IDLE
        return {
          bgColor: 'bg-gray-800',
          pulseClass: '',
          statusText: '대화를 시작해보세요',
          statusColor: 'text-gray-600'
        };
    }
  };

  // 텍스트를 글자별로 나누어 웨이브 효과 생성
  const renderWaveText = (text: string) => {
    if (!isInitialLoad) return text;
    
    return text.split('').map((char, index) => (
      <span
        key={index}
        style={{
          display: 'inline-block',
          animation: `wave 0.6s ease-in-out 2`,
          animationDelay: `${index * 0.08}s`,
          animationFillMode: 'forwards'
        }}
      >
        {char === ' ' ? '\u00A0' : char}
      </span>
    ));
  };

  const stateConfig = getStateConfig();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-full px-4 py-8">
      {/* 메인 컨테이너 - 중앙 정렬 및 반응형 */}
      <div className="flex flex-col items-center justify-center max-w-md w-full space-y-8">
        
        {/* 캐릭터 영역 (IMG 원) */}
        <div className="relative">
          {/* 상태 표시 원 */}
          <div 
            className={`w-60 h-60 rounded-full flex items-center justify-center ${stateConfig.bgColor} ${stateConfig.pulseClass} shadow-xl transition-all duration-300`}
          >
            {/* IMG 텍스트 또는 캐릭터 이미지 */}
            <div className="text-white text-lg sm:text-xl font-semibold">IMG</div>
          </div>
        </div>

        {/* 상태 텍스트 */}
        <div 
          className={`text-center font-medium text-sm sm:text-base ${stateConfig.statusColor} transition-all duration-300 ${
            isInitialLoad ? 'opacity-80' : 'opacity-100'
          }`}
        >
          {renderWaveText(stateConfig.statusText)}
        </div>

        {/* 에러 메시지 표시 */}
        {(recordingError || apiError) && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center space-x-2 max-w-full">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <div className="text-red-700 text-sm">
              {recordingError || apiError}
            </div>
          </div>
        )}

        {/* 대화 내용 표시 */}
        {(sttResult || aiResult) && (
          <div className="w-full space-y-3 max-h-40 overflow-y-auto">
            {/* 사용자 음성 인식 결과 */}
            {sttResult && (
              <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-400">
                <div className="text-blue-800 text-sm">
                  <span className="font-semibold">나:</span> {sttResult}
                </div>
              </div>
            )}

            {/* AI 챗봇 응답 */}
            {aiResult && (
              <div className="bg-green-50 p-3 rounded-lg border-l-4 border-green-400">
                <div className="text-green-800 text-sm">
                  <span className="font-semibold">AI:</span> {aiResult}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 버튼 그룹 - 마이크와 통화 종료 나란히 */}
        <div className="flex items-center space-x-6">
          {/* 마이크 버튼 */}
          <Button
            onClick={handleMicClick}
            disabled={voiceChatState === 'AI_SPEAKING' || isProcessing}
            className={`w-16 h-16 sm:w-15 sm:h-15 rounded-full flex items-center justify-center shadow-lg transition-all duration-300
              ${recording 
                ? "bg-red-500 hover:bg-red-600 scale-110" 
                : (voiceChatState === 'AI_SPEAKING' || isProcessing)
                  ? "bg-gray-400 cursor-not-allowed"
                  : recordingError
                    ? "bg-red-500 hover:bg-red-600"
                    : "bg-blue-500 hover:bg-blue-600"
              }
            `}
            variant="default"
            size="icon"
          >
            {recording ? (
              <MicOff className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            ) : (
              <Mic className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            )}
          </Button>

          {/* 통화 종료 버튼 */}
          <Button
            onClick={handleEndCall}
            className="w-16 h-16 sm:w-15 sm:h-15 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center shadow-lg transition-all duration-300"
            variant="default"
            size="icon"
          >
            <PhoneOff className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
          </Button>
        </div>

        {/* 상태 인디케이터 (하단) */}
        <div className="flex space-x-2">
          <div className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full transition-all duration-300 ${voiceChatState === 'IDLE' ? 'bg-gray-400' : 'bg-gray-200'}`} />
          <div className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full transition-all duration-300 ${voiceChatState === 'LISTENING' ? 'bg-blue-400' : 'bg-gray-200'}`} />
          <div className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full transition-all duration-300 ${voiceChatState === 'AI_SPEAKING' ? 'bg-green-400' : 'bg-gray-200'}`} />
        </div>

      </div>

      {/* TTS 음성 자동 재생용 audio 태그 */}
      <audio 
        ref={audioRef} 
        onEnded={handleAudioEnded}
        onError={handleAudioError}
        preload="metadata"
      />
    </div>
  );
};

export default VoiceChat;