import { useState, useRef, useEffect, useCallback } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAiFriend } from "@/contexts/AiFriendContext";
import {
  Home,
  Image as ImageIcon,
  Heart,
  User,
  Send,
  Phone,
  Settings,
  Mic,
  Camera,
  Volume2,
} from "lucide-react";
import { toast } from "sonner";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  time: string;
  image?: string;
  voice?: string;
}

interface ChatState {
  userMbti: string;
  relationshipType: string;
  aiName: string;
  currentEmotion: string;
}

const ChatPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Context에서 AI 친구 정보 가져오기 (ComfyUI)
  const { aiFriendName: contextAiName, aiFriendImage } = useAiFriend();

  // 상태 통합
  const [chatState, setChatState] = useState<ChatState>({
    userMbti: "",
    relationshipType: "",
    aiName: "",
    currentEmotion: "neutral",
  });

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isCapturing, setIsCapturing] = useState(false);
  const [showCameraPreview, setShowCameraPreview] = useState(false);
  const [cameraStreamUrl, setCameraStreamUrl] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // URL 파라미터 처리 및 초기 설정
  useEffect(() => {
    const params = {
      userMbti: searchParams.get("user_mbti") || "",
      relationshipType: searchParams.get("relationship_type") || "",
      aiName: searchParams.get("ai_name") || contextAiName || "AI 친구",
      currentEmotion: "neutral",
    };

    // URL 파라미터가 없고 Context도 없으면 MBTI 선택 페이지로
    if (!params.userMbti && !params.relationshipType && !contextAiName) {
      // Context에 값이 있으면 기본값 사용
      params.userMbti = "ENFP";
      params.relationshipType = "동질적 관계";
    }

    setChatState(params);

    // 초기 메시지 설정
    setMessages([
      {
        id: "1",
        sender: "ai",
        text: `안녕, 만나서 반가워! 나는 너의 AI 친구${
          params.aiName ? " " + params.aiName : ""
        }야. 어떻게 지내고 있어?`,
        time: new Date().toLocaleTimeString("ko-KR", {
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        }),
      },
    ]);
  }, [searchParams, contextAiName]);

  // 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // API 호출 헬퍼 함수 (RAG)
  const apiCall = useCallback(async (endpoint: string, data?: any) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}${endpoint}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          ...(data && { body: JSON.stringify(data) }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `요청 실패: ${endpoint}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API 호출 실패 (${endpoint}):`, error);
      throw error;
    }
  }, []);

  // 메시지 추가 헬퍼
  const addMessage = useCallback(
    (text: string, sender: "user" | "ai", extra?: Partial<Message>) => {
      const message: Message = {
        id: Date.now().toString(),
        sender,
        text,
        time: new Date().toLocaleTimeString("ko-KR", {
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        }),
        ...extra,
      };
      setMessages((prev) => [...prev, message]);
      return message;
    },
    []
  );

  // 분할 메시지 처리 (RAG)
  const addSplitMessages = useCallback(
    (response: string, sender: "user" | "ai", delay: number = 1000) => {
      const parts = response
        .split("[분할]")
        .map((part) => part.trim())
        .filter((part) => part.length > 0);

      parts.forEach((part, index) => {
        setTimeout(() => {
          addMessage(part, sender);
        }, index * delay);
      });
    },
    [addMessage]
  );

  // 카메라 캡처 시작 함수 (ComfyUI)
  const startCamera = async () => {
    try {
      setIsCapturing(true);
      toast.info("카메라 준비 중...");

      // 백엔드에 카메라 시작 요청
      const response = await fetch(`http://localhost:8181/api/camera/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("카메라 시작 요청 실패");
      }

      // 카메라 스트림 URL 설정
      setCameraStreamUrl(`http://localhost:8181/api/camera/stream`);
      setShowCameraPreview(true);
    } catch (error) {
      console.error("카메라 접근 오류:", error);
      toast.error("카메라에 접근할 수 없습니다.");
      setIsCapturing(false);
      setShowCameraPreview(false);
    }
  };

  // 카메라 중지 함수 (ComfyUI)
  const stopCamera = async () => {
    try {
      // 백엔드에 카메라 중지 요청
      await fetch(`http://localhost:8181/api/camera/stop`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      setShowCameraPreview(false);
      setCameraStreamUrl("");
      setIsCapturing(false);
    } catch (error) {
      console.error("카메라 중지 오류:", error);
      toast.error("카메라를 중지할 수 없습니다.");
    }
  };

  // 카메라 제어 (RAG)
  const toggleCamera = useCallback(async () => {
    if (isCapturing) {
      await apiCall("/api/camera/stop");
      setShowCameraPreview(false);
      setIsCapturing(false);
    } else {
      setIsCapturing(true);
      toast.info("카메라 준비 중...");
      await apiCall("/api/camera/start");
      setShowCameraPreview(true);
    }
  }, [isCapturing, apiCall]);

  // 사진 촬영
  const capturePhoto = useCallback(async () => {
    try {
      // 백엔드에 캡처 요청 (두 가지 방식 모두 지원)
      const response = await fetch(`http://localhost:8181/api/camera/capture`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("사진 촬영 요청 실패");
      }

      const data = await response.json();

      if (data.success) {
        // 사용자 메시지 추가
        addMessage("[사진을 전송했습니다]", "user", { image: data.image });

        if (data.emotion) {
          setChatState((prev) => ({ ...prev, currentEmotion: data.emotion }));
        }

        // AI 응답 처리
        if (chatState.userMbti && chatState.relationshipType) {
          // RAG 방식 AI 응답 요청
          const chatData = await apiCall("/api/chat", {
            messages: [
              {
                role: "user",
                content: `[사진 전송 - 감정: ${data.emotion}]`,
                timestamp: Date.now() / 1000,
              },
            ],
            user_id: "user123",
            ai_id: "ai_friend_001",
            user_mbti: chatState.userMbti,
            relationship_type: chatState.relationshipType,
            ai_name: chatState.aiName,
            context: { emotion: data.emotion },
          });

          // [분할] 처리
          if (chatData.response && chatData.response.includes("[분할]")) {
            addSplitMessages(chatData.response, "ai");
          } else {
            addMessage(chatData.response || "응답을 받지 못했습니다.", "ai");
          }
        } else {
          // ComfyUI 방식 간단한 응답
          setTimeout(() => {
            addMessage(
              `사진 분석 결과: ${data.emotion} 감정이 감지되었습니다.`,
              "ai"
            );
          }, 1000);
        }

        // 카메라 중지
        if (cameraStreamUrl) {
          await stopCamera();
        } else {
          await toggleCamera();
        }
      } else {
        toast.error(data.message || "사진 촬영에 실패했습니다.");
      }
    } catch (error) {
      console.error("사진 촬영 오류:", error);
      toast.error("사진 촬영에 실패했습니다.");
    }
  }, [
    apiCall,
    addMessage,
    chatState,
    toggleCamera,
    addSplitMessages,
    cameraStreamUrl,
    stopCamera,
  ]);

  // TTS 재생
  const playTTS = useCallback(async (text: string) => {
    try {
      console.log("TTS 요청 시작:", text); // 디버깅용

      // 음성 변환 요청
      const response = await fetch("http://localhost:8181/api/tts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("서버 응답 에러:", response.status, errorText);
        throw new Error(`음성 변환 요청 실패: ${response.status}`);
      }

      // Create and play audio
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      // Cleanup after playback
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
      console.log("TTS 재생 성공"); // 디버깅용
    } catch (error) {
      console.error("음성 재생 실패:", error);
      alert("음성 재생에 실패했습니다. 콘솔을 확인해주세요.");
    }
  }, []);

  // 메시지 전송
  const handleSendMessage = useCallback(async () => {
    const message = inputMessage.trim();
    if (!message) return;

    addMessage(message, "user");
    setInputMessage("");

    try {
      // RAG API 구조 사용
      const data = await apiCall("/api/chat", {
        messages: [
          {
            role: "user",
            content: message,
            timestamp: Date.now() / 1000,
          },
        ],
        user_id: "user123",
        ai_id: "ai_friend_001",
        user_mbti: chatState.userMbti,
        relationship_type: chatState.relationshipType,
        ai_name: chatState.aiName,
        context: { emotion: chatState.currentEmotion },
      });

      // [분할]로 나누어서 순차적으로 메시지 추가
      if (data.response && data.response.includes("[분할]")) {
        addSplitMessages(data.response, "ai");
      } else {
        addMessage(data.response || "응답을 받지 못했습니다.", "ai");
      }
    } catch (error) {
      console.error("메시지 전송 실패:", error);
      toast.error("메시지 전송에 실패했습니다.");
    }
  }, [inputMessage, apiCall, chatState, addMessage, addSplitMessages]);

  // Voice Recorder Hook (ComfyUI에서 가져옴, 추후 사용 가능)
  const useVoiceRecorder = () => {
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const audioChunks = useRef<Blob[]>([]);
    const [recording, setRecording] = useState(false);
    const mediaRecorder = useRef<MediaRecorder | null>(null);

    const startRecording = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      audioChunks.current = [];
      mediaRecorder.current = new MediaRecorder(stream);
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };
      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, {
          type: "audio/wav",
        });
        setAudioUrl(URL.createObjectURL(audioBlob));
      };
      mediaRecorder.current.start();
      setRecording(true);
    };

    const stopRecording = async () => {
      if (mediaRecorder.current) {
        return new Promise<Blob>((resolve) => {
          mediaRecorder.current!.onstop = () => {
            const audioBlob = new Blob(audioChunks.current, {
              type: "audio/wav",
            });
            setAudioUrl(URL.createObjectURL(audioBlob));
            setRecording(false);
            resolve(audioBlob);
          };
          mediaRecorder.current.stop();
        });
      }
    };

    return {
      recording,
      audioUrl,
      startRecording,
      stopRecording,
      setAudioUrl,
    };
  };

  // AI 이름과 이미지 결정
  const displayName = chatState.aiName || contextAiName || "AI 친구";
  const displayImage = aiFriendImage || "/example_avatar_profile.png";

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Sidebar (ComfyUI) */}
      <div className="w-72 border-r bg-white hidden lg:block">
        {/* Add left sidebar content here */}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="p-4 border-b bg-white flex items-center justify-between">
          <div className="flex items-center">
            <Avatar className="h-10 w-10">
              <img src={displayImage} alt="AI Avatar" />
            </Avatar>
            <div className="ml-3">
              <h2 className="font-medium">{displayName}</h2>
              <p className="text-xs text-gray-500">활동중 상태</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {[Phone, Settings].map((Icon, idx) => (
              <button key={idx} className="p-2 rounded-full hover:bg-gray-100">
                <Icon className="h-5 w-5 text-gray-500" />
              </button>
            ))}
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(({ id, sender, text, time, image }) => (
            <div
              key={id}
              className={`flex ${
                sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {sender === "ai" && (
                <Avatar className="h-8 w-8 mr-2 mt-1">
                  <img src={displayImage} alt="AI Avatar" />
                </Avatar>
              )}
              <div
                className={`max-w-[70%] ${
                  sender === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-800"
                } rounded-2xl p-3 ${
                  sender === "user" ? "rounded-tr-none" : "rounded-tl-none"
                }`}
              >
                {image && (
                  <img
                    src={image}
                    alt="Captured"
                    className="rounded-lg max-w-full mb-2"
                  />
                )}
                <p>{text}</p>
                <span className="flex items-center justify-between mt-1 text-xs opacity-70">
                  {time}
                  {sender === "ai" && (
                    <button
                      className="ml-2 p-1 hover:bg-gray-300 rounded-full"
                      onClick={async () => {
                        try {
                          console.log("TTS 요청 시작:", text);

                          // 음성 변환 요청
                          const response = await fetch(
                            "http://localhost:8181/api/tts",
                            {
                              method: "POST",
                              headers: {
                                "Content-Type": "application/json",
                              },
                              body: JSON.stringify({ text: text }),
                            }
                          );

                          if (!response.ok) {
                            const errorText = await response.text();
                            console.error(
                              "서버 응답 에러:",
                              response.status,
                              errorText
                            );
                            throw new Error(
                              `음성 변환 요청 실패: ${response.status}`
                            );
                          }

                          // 오디오 blob 처리
                          const audioBlob = await response.blob();
                          console.log("받은 오디오 blob:", {
                            type: audioBlob.type,
                            size: audioBlob.size,
                            sizeKB: Math.round(audioBlob.size / 1024),
                          });

                          // Blob이 비어있는지 확인
                          if (audioBlob.size === 0) {
                            throw new Error("빈 오디오 데이터를 받았습니다");
                          }

                          const audioUrl = URL.createObjectURL(audioBlob);
                          const audio = new Audio(audioUrl);

                          // 오디오 이벤트 리스너들
                          audio.onloadstart = () =>
                            console.log("오디오 로드 시작");
                          audio.oncanplay = () =>
                            console.log("오디오 재생 가능");

                          audio.oncanplaythrough = () => {
                            console.log("오디오 완전히 로드됨, 재생 시작");
                            audio.play().catch((playError) => {
                              console.error("재생 실패:", playError);
                              URL.revokeObjectURL(audioUrl);
                              alert(`음성 재생 실패: ${playError.message}`);
                            });
                          };

                          audio.onerror = (e) => {
                            console.error("오디오 에러:", e);
                            console.error("오디오 에러 상세:", {
                              error: audio.error,
                              networkState: audio.networkState,
                              readyState: audio.readyState,
                            });
                            URL.revokeObjectURL(audioUrl);
                            alert("음성 재생에 실패했습니다.");
                          };

                          audio.onended = () => {
                            console.log("재생 완료");
                            URL.revokeObjectURL(audioUrl);
                          };

                          // 타임아웃 설정 (30초)
                          setTimeout(() => {
                            if (audio.readyState === 0) {
                              console.error("오디오 로드 타임아웃");
                              URL.revokeObjectURL(audioUrl);
                              alert("음성 로드 시간이 초과되었습니다.");
                            }
                          }, 30000);

                          console.log("TTS 설정 완료"); // 디버깅용
                        } catch (error) {
                          console.error("음성 재생 실패:", error);
                          alert(`음성 재생에 실패했습니다: ${error.message}`);
                        }
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

        {/* Camera Preview */}
        {showCameraPreview && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white p-4 rounded-lg max-w-md w-full">
              <div className="text-center mb-4">
                <h3 className="text-lg font-medium">카메라 미리보기</h3>
                <p className="text-sm text-gray-500">
                  원하는 각도에서 사진을 촬영하세요
                </p>
              </div>
              <div className="relative overflow-hidden rounded-lg mb-4">
                <img
                  src={
                    cameraStreamUrl ||
                    `${import.meta.env.VITE_API_URL}/api/camera/stream`
                  }
                  alt="카메라 미리보기"
                  className="w-full h-auto"
                />
              </div>
              <div className="flex justify-between">
                <Button
                  onClick={cameraStreamUrl ? stopCamera : toggleCamera}
                  className="bg-gray-500 hover:bg-gray-600"
                >
                  취소
                </Button>
                <Button
                  onClick={capturePhoto}
                  className="bg-blue-500 hover:bg-blue-600"
                >
                  사진 촬영
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="p-4 bg-white border-t">
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center bg-gray-100 rounded-full pr-2">
              <Textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="메시지를 입력하세요..."
                className="resize-none min-h-[40px] max-h-24 bg-transparent flex-1 py-2 pl-4 pr-20 focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <div className="flex items-center gap-1">
                <button className="p-1 hover:bg-gray-200 rounded-full">
                  <Mic className="h-5 w-5 text-gray-500" />
                </button>
                <button
                  className="p-1 hover:bg-gray-200 rounded-full"
                  onClick={cameraStreamUrl ? toggleCamera : startCamera}
                  disabled={isCapturing}
                >
                  <Camera className="h-5 w-5 text-gray-500" />
                </button>
              </div>
            </div>
            <Button
              onClick={handleSendMessage}
              className="shrink-0 h-10 w-10 rounded-full bg-blue-500 hover:bg-blue-600"
              disabled={!inputMessage.trim()}
            >
              <Send className="h-5 w-5 text-white" />
            </Button>
          </div>
        </div>

        {/* Bottom Navigation */}
        <nav className="py-2 grid grid-cols-4 border-t bg-white">
          {[
            { to: "/signup", icon: Home, label: "홈", active: true },
            { to: "#", icon: ImageIcon, label: "앨범" },
            { to: "#", icon: Heart, label: "추억" },
            { to: "/profile", icon: User, label: "프로필" },
          ].map(({ to, icon: Icon, label, active }) => (
            <Link
              key={label}
              to={to}
              className="flex flex-col items-center justify-center"
            >
              <Icon
                className={`h-6 w-6 ${
                  active ? "text-blue-500" : "text-gray-400"
                }`}
              />
              <span
                className={`text-[11px] mt-1 ${
                  active ? "text-blue-500" : "text-gray-400"
                }`}
              >
                {label}
              </span>
            </Link>
          ))}
        </nav>
      </div>

      {/* Right Sidebar (ComfyUI) */}
      <div className="w-72 border-l bg-white hidden lg:block">
        {/* Add right sidebar content here */}
      </div>
    </div>
  );
};

export default ChatPage;
