import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { Mic, MicOff, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface VoiceChatProps {
  avatarUrl?: string; // 선택적!
}

const VoiceChat: React.FC<VoiceChatProps> = ({ avatarUrl }) => {
  const defaultAvatar = "/default-avatar.png"; // public 기준 절대경로
  const [micOn, setMicOn] = useState(false);
  const navigate = useNavigate();

  // src 경로: avatarUrl이 없으면 디폴트로 대체
  const src = avatarUrl && avatarUrl.trim() !== "" ? avatarUrl : defaultAvatar;

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] w-full relative">
      {/* 중앙 아바타 이미지 */}
      <img
        src={src}
        alt="User Avatar"
        className="w-48 h-60 object-cover rounded-2xl shadow-xl mb-8"
        style={{ background: "#f3f4f6" }}
      />

      {/* 마이크 on/off 버튼 */}
      <Button
        onClick={() => setMicOn((on) => !on)}
        className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl mb-8 shadow-lg transition
          ${micOn ? "bg-green-500 hover:bg-green-600" : "bg-red-500 hover:bg-red-600"}
        `}
        variant="default"
        size="icon"
      >
        {micOn ? <Mic className="w-8 h-8 text-white" /> : <MicOff className="w-8 h-8 text-white" />}
      </Button>

      {/* X 버튼: 채팅 메인화면으로 페이지 이동 */}
      <Button
        onClick={() => navigate(-1)}
        className="absolute right-6 bottom-6 w-12 h-12 rounded-full bg-gray-200 hover:bg-gray-300"
        size="icon"
        variant="ghost"
      >
        <X className="w-7 h-7 text-gray-700" />
      </Button>
    </div>
  );
};

export default VoiceChat;
