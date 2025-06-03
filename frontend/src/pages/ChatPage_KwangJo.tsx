import React, { useState, useRef } from "react";
import { Mic, Volume2, Send } from "lucide-react";

// 1. 녹음 훅
const useVoiceRecorder = () => {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    audioChunksRef.current = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };
    mediaRecorderRef.current = recorder;
    recorder.start();
    setRecording(true);
  };

  const stopRecording = async (): Promise<Blob> => {
    return new Promise((resolve) => {
      mediaRecorderRef.current!.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        setRecording(false);
        resolve(blob);
      };
      mediaRecorderRef.current!.stop();
    });
  };

  return { recording, startRecording, stopRecording };
};

// 2. STT 요청 함수
const sendAudioToSTT = async (audioBlob: Blob): Promise<string> => {
  const formData = new FormData();
  formData.append("audio", audioBlob, "voice.wav");
  const res = await fetch("http://localhost:8181/api/stt", { method: "POST", body: formData });
  if (!res.ok) throw new Error("STT 서버 오류");
  const data = await res.json();
  return data.result || data.text || "";
};

// 3. TTS 요청 함수 (음성 재생)
const playTTS = async (text: string) => {
  const formData = new FormData();
  formData.append("text", text);
  const res = await fetch("http://localhost:8181/api/tts", { method: "POST", body: formData });
  if (!res.ok) throw new Error("TTS 서버 오류");
  const audioBlob = await res.blob();
  const audioUrl = URL.createObjectURL(audioBlob);
  new Audio(audioUrl).play();
};

const ChatPage = () => {
  const [messages, setMessages] = useState<{ sender: "user" | "ai"; text: string }[]>([]);
  const [input, setInput] = useState("");
  const { recording, startRecording, stopRecording } = useVoiceRecorder();

  // 음성 버튼 클릭
  const handleMic = async () => {
    if (!recording) {
      await startRecording();
    } else {
      const audioBlob = await stopRecording();
      const stt = await sendAudioToSTT(audioBlob);
      setMessages((msgs) => [...msgs, { sender: "user", text: stt }]);
    }
  };

  // 텍스트 전송
  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { sender: "user", text: input }]);
    setInput("");
  };

  return (
    <div>
      {/* 메시지 출력 */}
      {messages.map((msg, idx) => (
        <div key={idx} style={{ textAlign: msg.sender === "user" ? "right" : "left" }}>
          <span>{msg.text}</span>
          {msg.sender === "ai" && (
            <button onClick={() => playTTS(msg.text)}>
              <Volume2 />
            </button>
          )}
        </div>
      ))}

      {/* 입력창 및 버튼 */}
      <div>
        <input value={input} onChange={e => setInput(e.target.value)} disabled={recording} />
        <button onClick={handleSend} disabled={recording}><Send /></button>
        <button onClick={handleMic}>
          <Mic color={recording ? "red" : "black"} />
        </button>
      </div>
    </div>
  );
};

export default ChatPage;
