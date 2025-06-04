import { useState, useRef } from "react";

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

export default useVoiceRecorder;