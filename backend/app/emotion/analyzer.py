import cv2
import threading
import time
import numpy as np
from collections import deque
from queue import Queue
from PIL import Image

from app.multimodal.vlm import summarize_scene
from app.audio.stt import record_audio, transcribe_audio
from backend.app.emotion.fer_emotion import analyze_facial_expression
from backend.app.emotion.ser_emotion import analyze_voice_emotion_korean
from backend.app.nlp.llm import generate_response
from app.emotion.summary import most_common_emotion, print_emotion_summary

# 실행 상태 및 큐 초기화
running_event = threading.Event()
running_event.set()
emotion_logs = deque(maxlen=10)
analysis_queue = Queue(maxsize=1)

# 감정 합성 함수는 app.emotion.synthesizer 모듈로 이동되었습니다

def analyze_loop(vlm_model, processor, device, whisper_model):
    while running_event.is_set():
        if not analysis_queue.empty():
            try:
                frame = analysis_queue.get()
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                # 얼굴 감정 분석
                face_emotion = analyze_facial_expression(image)

                # 음성 녹음 및 텍스트 변환, 목소리톤 감정 추출
                file_path = record_audio()
                text = transcribe_audio(whisper_model, file_path)
                voice_tone_emotion = analyze_voice_emotion_korean(file_path)

                # SmolVLM으로 배경/장면 인식
                scene_context = summarize_scene(image, processor, vlm_model, device)

                # 로그 저장
                emotion_logs.append({
                    "face": face_emotion,
                    "text": text,
                    "voice_emotion": voice_tone_emotion,
                    "scene": scene_context
                })

                print(f"[표정 감정] {face_emotion} / [목소리톤 감정] {voice_tone_emotion}")
                print(f"[사용자 발화] {text}")
                print(f"[현재 장면 요약] {scene_context}")

            except Exception as e:
                print(f"[❗예외] {e}")
        time.sleep(0.2)

    # 종료 후 분석 및 Gemini 응답
    if emotion_logs:
        all_faces = [e["face"] for e in emotion_logs]
        all_texts = " ".join([e["text"] for e in emotion_logs])
        all_voice_emotions = [e["voice_emotion"] for e in emotion_logs]
        last_scene = emotion_logs[-1]["scene"]

        final_face = most_common_emotion(all_faces)
        final_voice_emotion = most_common_emotion(all_voice_emotions)

        context = {
            "weather": "맑음",
            "sleep": "7시간",
            "stress": "중간",
            "location_scene": last_scene,
            "emotion_history": [final_face, final_voice_emotion]
        }

        print_emotion_summary(emotion_logs)

        # 감정 합성 (간단한 처리)
        emotion = final_face if final_face != "unknown" else final_voice_emotion

        # 비동기 함수 호출을 위한 처리
        import asyncio
        try:
            response = asyncio.run(generate_response(
                emotion=emotion,
                user_text=all_texts,
                context=context,
                ai_mbti_persona=None  # 기본 페르소나 사용
            ))
        except Exception as e:
            print(f"응답 생성 중 오류: {e}")
            response = "죄송합니다, 응답을 생성할 수 없습니다."
            
        print("\n🧠 Gemini 응답:")
        print(response)
    else:
        print("❗ 분석된 감정 로그가 없습니다.")

def analyze_image(image):
    """이미지 분석 처리 함수"""
    face_emotion = analyze_facial_expression(image)
    
    # 이미지를 분석 큐에 추가 (백그라운드 분석용)
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    if not analysis_queue.full():
        analysis_queue.put(frame)
    
    return face_emotion
