//원본 chatpage.tsx (수정전)
import React, { useState, useRef, useEffect } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Link, useNavigate } from "react-router-dom";
import { Image as  Send, Phone, Settings, Mic, Camera, Volume2 } from "lucide-react";

// 메시지 타입
interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  time: string;
  image?: string;
}

// 음성 녹음 훅 (간단 예시)
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
      return new Promise<Blob>((resolve) => {
        mediaRecorder.current!.onstop = () => {
          const audioBlob = new Blob(audioChunks.current, { type: "audio/wav" });
          setAudioUrl(URL.createObjectURL(audioBlob));
          setRecording(false);
          resolve(audioBlob);
        };
        mediaRecorder.current.stop();
      });
    }
  };

  return { recording, audioUrl, startRecording, stopRecording, setAudioUrl };
};

// STT 서버 전송 함수 (키 이름만 통일)
async function sendAudioToSTT(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append("audio", audioBlob, "voice.wav");

  const res = await fetch("http://localhost:8181/api/stt", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("STT 서버 오류");
  }

  const data = await res.json();
  return data.result || data.text; // 키 중 하나만 있어도 자동 대응
}

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "ai",
      text: "안녕, 만나서 반가워! 나는 너의 AI 친구 미나야. 어떻게 지내고 있어?",
      time: "오전 10:23",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [loadingSTT, setLoadingSTT] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { recording, startRecording, stopRecording } = useVoiceRecorder();
  const navigate = useNavigate();

  // 메시지 스크롤 항상 하단 고정
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 텍스트 메시지 전송
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

  // STT(음성) 메시지 전송
const handleMicClick = async () => {
  if (!isListening) {
    setIsListening(true);
    await startRecording();
    // 음성 안내 메시지는 Textarea에만 노출
  } else {
    setIsListening(false);
    setLoadingSTT(true);
    const audioBlob = await stopRecording();
    try {
      // === ① Whisper STT 결과 수신 ===
      const sttText = await sendAudioToSTT(audioBlob!);

      // === ② 사용자 메시지로 추가 ===
      const userMsg: Message = {
        id: Date.now().toString(),
        sender: "user",
        text: sttText,
        time: new Date().toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true }),
      };
      setMessages((prev) => [...prev, userMsg]);

      // === ③ AI 응답 추가(모의) ===
      setTimeout(() => {
        const aiMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          text: `STT로 받은 메시지에 대한 AI 응답 예시입니다.`,
          time: new Date().toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true }),
        };
        setMessages((prev) => [...prev, aiMsg]);
        setLoadingSTT(false);
      }, 1000);
    } catch (error) {
      alert("음성 인식(STT)에 실패했습니다.");
      setLoadingSTT(false);
    }
  }
};

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full border-x">
        {/* Header */}
        <header className="py-3 px-4 bg-white border-b flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <img src="/example_avatar_profile.png" alt="AI Friend" className="w-full h-full object-cover" />
            </Avatar>
            <div>
              <h1 className="text-sm">미나</h1>
              <p className="text-[11px] text-green-600">활동중 상태</p>
            </div>
          </div>
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
        {/* Messages */}
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
                        // TTS (ai가 생성한 음성 듣기)필요시 구현
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
        {/* (하단 네비게이션, 사이드바 등 필요하면 추가) */}
      </div>
    </div>
  );
};

export default ChatPage;
