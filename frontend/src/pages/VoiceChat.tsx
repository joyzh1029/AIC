import { useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Mic, MicOff, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

interface VoiceChatProps {
  avatarUrl?: string;
}

const VoiceChat: React.FC<VoiceChatProps> = ({ avatarUrl }) => {
  const defaultAvatar = "/default-avatar.png";
  const src = avatarUrl && avatarUrl.trim() !== "" ? avatarUrl : defaultAvatar;
  const navigate = useNavigate();

  const {
    recording,
    audioBlob,
    startRecording,
    stopRecording,
    reset,
  } = useVoiceRecorder();

  // 추가: 상태 선언
  const [sttResult, setSttResult] = useState("");   // 음성 인식 결과
  const [aiResult, setAiResult] = useState("");     // AI 응답 결과
  const [ttsUrl, setTtsUrl] = useState("");         // TTS 파일 URL
  const audioRef = useRef<HTMLAudioElement>(null);

  // 마이크 on/off 토글
  const handleMicClick = () => {
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // 서버 전송 & 결과 반영
  useEffect(() => {
    const uploadAudio = async (blob: Blob) => {
      const formData = new FormData();
      formData.append("audio", blob, "recording.webm");

      try {
        const response = await fetch("http://localhost:8181/api/stt", {
          method: "POST",
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          // 서버 응답에 맞게 필드명 확인!
          // 예: { result: "...", aiResponse: "...", ttsUrl: "..." }
          setSttResult(data.result || "");
          setAiResult(data.aiResponse || "");
          setTtsUrl(data.ttsUrl || "");
        } else {
          console.error("음성 업로드 실패:", response.status);
        }
      } catch (err) {
        console.error("네트워크 오류:", err);
      }
    };

    if (audioBlob) {
      uploadAudio(audioBlob);
      reset();
    }
  }, [audioBlob, reset]);

  // TTS URL이 생기면 자동 재생
  useEffect(() => {
    if (ttsUrl && audioRef.current) {
      audioRef.current.src = ttsUrl;
      audioRef.current.play();
    }
  }, [ttsUrl]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] w-full relative">
      {/* 아바타 이미지 */}
      <img
        src={src}
        alt="User Avatar"
        className="w-48 h-60 object-cover rounded-2xl shadow-xl mb-8"
        style={{ background: "#f3f4f6" }}
      />

      {/* (추가) 사용자 음성 인식 결과 */}
      {sttResult && (
        <div className="mb-2 text-gray-700">
          <b>나:</b> {sttResult}
        </div>
      )}

      {/* (추가) AI 챗봇 응답 */}
      {aiResult && (
        <div className="mb-4 text-blue-700">
          <b>AI:</b> {aiResult}
        </div>
      )}

      {/* 마이크 버튼 */}
      <Button
        onClick={handleMicClick}
        className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl mb-8 shadow-lg transition
          ${recording ? "bg-green-500 hover:bg-green-600" : "bg-red-500 hover:bg-red-600"}
        `}
        variant="default"
        size="icon"
      >
        {recording ? <Mic className="w-8 h-8 text-white" /> : <MicOff className="w-8 h-8 text-white" />}
      </Button>

      {/* X(나가기) 버튼 */}
      <Button
        onClick={() => navigate(-1)}
        className="absolute right-6 bottom-6 w-12 h-12 rounded-full bg-gray-200 hover:bg-gray-300"
        size="icon"
        variant="ghost"
      >
        <X className="w-7 h-7 text-gray-700" />
      </Button>

      {/* (추가) TTS 음성 자동 재생용 audio 태그 */}
      <audio ref={audioRef} />
    </div>
  );
};

export default VoiceChat;
