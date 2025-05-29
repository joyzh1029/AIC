// src/pages/ChatPage.tsx

import React, { useState, useRef, useEffect } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Home, Image as ImageIcon, Heart, Send, Phone, Settings, Mic, Camera, Volume2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  time: string;
  image?: string;
}

const useVoiceRecorder = () => {
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);
    audioChunks.current = [];
    mediaRecorder.current.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.current.push(event.data);
      }
    };
    mediaRecorder.current.onstop = () => {
      const audioBlob = new Blob(audioChunks.current, { type: "audio/wav" });
      setAudioUrl(URL.createObjectURL(audioBlob));
    };
    mediaRecorder.current.start();
    setRecording(true);
  };

  const stopRecording = async () => {
    if (mediaRecorder.current) {
      mediaRecorder.current.stop();
      setRecording(false);
      return new Promise<Blob>((resolve) => {
        mediaRecorder.current!.onstop = () => {
          const audioBlob = new Blob(audioChunks.current, { type: "audio/wav" });
          setAudioUrl(URL.createObjectURL(audioBlob));
          resolve(audioBlob);
        };
      });
    }
  };

  return { recording, audioUrl, startRecording, stopRecording, setAudioUrl };
};

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
  const [isListening, setIsListening] = useState(false);
  const [loadingSTT, setLoadingSTT] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { recording, startRecording, stopRecording } = useVoiceRecorder();
  const navigate = useNavigate();

  // 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 일반 텍스트 메시지 전송
  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;
    const newMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: inputMessage,
      time: new Date().toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true }),
    };
    setMessages((prev) => [...prev, newMessage]);
    setInputMessage("");
    // AI 응답
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: "네 메시지 잘 받았어! 더 이야기해줘.",
        time: new Date().toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true }),
      };
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  // STT 플로우
  const handleMicClick = async () => {
    if (!isListening) {
      // 녹음 시작
      setIsListening(true);
      await startRecording();
    } else {
      // 녹음 종료
      setIsListening(false);
      setLoadingSTT(true);
      const audioBlob = await stopRecording();
      // --- STT 서버에 전송 (예시) ---
      // 실제 사용시 아래 fetch 부분을 본인 서버에 맞게 바꿔주세요
      // const formData = new FormData();
      // formData.append("audio", audioBlob, "voice.wav");
      // const res = await fetch("/api/stt", { method: "POST", body: formData });
      // const { text } = await res.json();
      // 임시 STT 결과
      const text = "음성 입력 예시(STT 결과 텍스트)";
      // 내 메시지로 추가
      const userMsg: Message = {
        id: Date.now().toString(),
        sender: "user",
        text,
        time: new Date().toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true }),
      };
      setMessages((prev) => [...prev, userMsg]);
      // AI 응답
      setTimeout(() => {
        const aiMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          text: "STT로 받은 메시지에 대한 AI 응답 예시입니다.",
          time: new Date().toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true }),
        };
        setMessages((prev) => [...prev, aiMsg]);
        setLoadingSTT(false);
      }, 1000);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* ... 생략(사이드바 등) ... */}
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full border-x">
        {/* Header */}
        <header className="py-3 px-4 bg-white border-b flex justify-between items-center">
          {/* ... */}
          <div className="flex gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 hover:bg-gray-100"
              onClick={() => navigate("/chat/voicechat")}
            >
              <Phone className="h-5 w-5" />
            </Button>
            <Link to="/settings">
              <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-gray-100">
                <Settings className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </header>
        {/* Messages Container */}
        <div className="flex-grow overflow-auto px-4 py-2 bg-gray-50">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              {message.sender === "ai" && (
                <Avatar className="h-8 w-8 shrink-0">
                  <img src="/example_avatar_profile.png" alt="AI Friend" className="w-full h-full object-cover" />
                </Avatar>
              )}
              <div className="flex flex-col max-w-[70%] mx-2">
                <div
                  className={`rounded-2xl p-3 ${message.sender === "user"
                    ? "bg-blue-100 rounded-tr-none"
                    : "bg-gray-100 rounded-tl-none"}`}
                >
                  <p className="text-sm text-gray-800">{message.text}</p>
                  {message.image && (
                    <div className="mt-2 rounded-lg overflow-hidden">
                      <img src={message.image} alt="Shared image" className="w-full h-auto" />
                    </div>
                  )}
                </div>
                <span className="text-[11px] text-gray-500 mt-1 mx-1">
                  {message.time}
                  {message.sender === "ai" && (
                    <button
                      className="ml-1 p-1 hover:bg-gray-200 rounded-full"
                      onClick={async () => {
                        // ...TTS 코드...
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
        {/* Input Section */}
        <div className="p-4 bg-white border-t">
          <div className="flex items-center gap-2 relative">
            <div className="flex-1 flex items-center bg-gray-100 rounded-full pr-2">
              <Textarea
                value={isListening ? "사용자 음성을 듣는 중입니다..." : inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isListening ? "사용자 음성을 듣는 중입니다..." : "메시지를 입력하세요..."}
                className="resize-none min-h-[40px] max-h-24 bg-transparent flex-1 py-2 pl-4 pr-20 focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey && !isListening) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                disabled={isListening || loadingSTT}
                readOnly={isListening}
              />
              <div className="flex items-center gap-1">
                <button
                  className={`p-1 hover:bg-gray-200 rounded-full ${isListening ? "bg-blue-200" : ""}`}
                  onClick={handleMicClick}
                  disabled={loadingSTT}
                  aria-label={isListening ? "음성 입력 종료" : "음성 입력 시작"}
                >
                  <Mic className="h-5 w-5 text-gray-500" />
                </button>
                <button className="p-1 hover:bg-gray-200 rounded-full" disabled={isListening || loadingSTT}>
                  <Camera className="h-5 w-5 text-gray-500" />
                </button>
              </div>
            </div>
            <Button
              onClick={handleSendMessage}
              className="shrink-0 h-10 w-10 rounded-full bg-blue-500 hover:bg-blue-600"
              disabled={!inputMessage.trim() || isListening || loadingSTT}
            >
              <Send className="h-5 w-5 text-white" />
            </Button>
          </div>
        </div>
        {/* ...하단 네비게이션 등... */}
      </div>
      {/* ...사이드바 등... */}
    </div>
  );
};

export default ChatPage;
