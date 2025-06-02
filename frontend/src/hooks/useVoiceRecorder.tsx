import { useRef, useState } from "react";

/**
 * useVoiceRecorder
 * - 마이크 녹음, 중지, 결과(blob) 반환 커스텀 훅
 */
export function useVoiceRecorder() {
  const [recording, setRecording] = useState(false);       // 녹음 중 상태
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null); // 녹음 결과
  const [error, setError] = useState<string | null>(null); // 에러 상태
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // 녹음 시작
  const startRecording = async () => {
    try {
      setError(null);
      
      // 마이크 권한 요청 및 스트림 생성
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        }
      });

      streamRef.current = stream;
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunks.current = [];

      // 데이터 수집
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };

      // 녹음 완료 시 Blob 생성
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunks.current, { 
          type: "audio/webm;codecs=opus" 
        });
        setAudioBlob(blob);
        
        // 스트림 정리
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      // 에러 처리
      mediaRecorderRef.current.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('녹음 중 오류가 발생했습니다.');
        setRecording(false);
      };

      mediaRecorderRef.current.start();
      setRecording(true);

    } catch (err) {
      console.error('Error starting recording:', err);
      setError('마이크 권한이 필요합니다.');
      setRecording(false);
    }
  };

  // 녹음 중지
  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  // 결과 초기화
  const reset = () => {
    setAudioBlob(null);
    setError(null);
    audioChunks.current = [];
  };

  return { 
    recording, 
    audioBlob, 
    error,
    startRecording, 
    stopRecording, 
    reset 
  };
}