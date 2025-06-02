// hooks/useVoiceRecorder.tsx

import { useRef, useState } from "react";

/**
 * useVoiceRecorder
 * - 마이크 녹음, 중지, 결과(blob) 반환 커스텀 훅
 */
export function useVoiceRecorder() {
  const [recording, setRecording] = useState(false);       // 녹음 중 상태
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null); // 녹음 결과
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  // 녹음 시작
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    audioChunks.current = [];
    mediaRecorderRef.current.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.current.push(event.data);
    };
    mediaRecorderRef.current.onstop = () => {
      setAudioBlob(new Blob(audioChunks.current, { type: "audio/webm" }));
    };
    mediaRecorderRef.current.start();
    setRecording(true);
  };

  // 녹음 중지
  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  // 결과 초기화
  const reset = () => setAudioBlob(null);

  return { recording, audioBlob, startRecording, stopRecording, reset };
}
