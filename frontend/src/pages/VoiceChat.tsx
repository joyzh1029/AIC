import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

interface VoiceChatProps {
  avatarUrl?: string;
}

interface ConversationMessage {
  type: "user" | "ai";
  text: string;
}

const VoiceChat: React.FC<VoiceChatProps> = ({ avatarUrl }) => {
  const navigate = useNavigate();

  // 상태 관리
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [currentLanguage, setCurrentLanguage] = useState("ko");
  const [error, setError] = useState<string | null>(null);
  const [micPermissionGranted, setMicPermissionGranted] = useState(false);
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const [status, setStatus] = useState("연결되지 않음");

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-full px-4 py-8">
      <div className="flex flex-col items-center justify-center max-w-md w-full space-y-8">
        <div className="relative">
          <div
            className={`
            w-60 h-60 rounded-full flex items-center justify-center shadow-xl transition-all duration-300
            ${
              isRecording
                ? "bg-blue-500 animate-pulse"
                : isConnected
                ? "bg-green-500"
                : "bg-gray-500"
            }
          `}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default VoiceChat;
