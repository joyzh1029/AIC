import cv2
import threading
import time
from collections import deque
from queue import Queue

from backend.app.vision.webcam import capture_webcam_image
from backend.app.multimodal.vlm import load_smol_vlm, analyze_face_emotion
from backend.app.audio.stt import load_whisper_model, transcribe_stream
from backend.app.vision.fer_emotion import analyze_facial_expression
from backend.app.emotion.emotion import synthesize_emotion
from backend.app.nlp.llm import configure_gemini, generate_response
from backend.app.emotion.summary import most_common_emotion, print_emotion_summary
from PIL import Image

# 실행 상태 및 큐 초기화
running_event = threading.Event()
running_event.set()
emotion_logs = deque(maxlen=10)
analysis_queue = Queue(maxsize=1)

def webcam_thread():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("웹캠을 열 수 없습니다.")
        return

    print("웹캠 창 열림. 'q'로 분석 요청, 't'로 종료.")

    while running_event.is_set():
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow("Webcam - Press 'q' to analyze once, 't' to terminate", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            if not analysis_queue.full():
                analysis_queue.put(frame.copy())
                print("🎬 분석 요청이 큐에 등록됨.")
            else:
                print("⏳ 이전 분석이 아직 끝나지 않았습니다.")
        elif key == ord('t'):
            running_event.clear()
            break

    cap.release()
    cv2.destroyAllWindows()

def synthesize_emotion_3way(face, text_emotion, voice_tone_emotion):
    if face != "neutral":
        return face
    elif voice_tone_emotion != "neutral":
        return voice_tone_emotion
    else:
        return text_emotion

def analyze_loop(vlm_model, processor, device, whisper_model):
    while running_event.is_set():
        if not analysis_queue.empty():
            try:
                frame = analysis_queue.get()
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                # 얼굴 감정 분석
                face_emotion = analyze_facial_expression(image)

                # 음성에서 텍스트, 텍스트 감정, 목소리 톤 감정 추출
                text, text_emotion, voice_tone_emotion = transcribe_stream(whisper_model)

                # SmolVLM으로 배경/장면 인식
                scene_context = analyze_face_emotion(image, processor, vlm_model, device)

                # 로그 저장
                emotion_logs.append({
                    "face": face_emotion,
                    "text": text,
                    "text_emotion": text_emotion,
                    "voice_emotion": voice_tone_emotion,
                    "scene": scene_context
                })

                print(f"[표정 감정] {face_emotion} / [텍스트 감정] {text_emotion} / [목소리톤 감정] {voice_tone_emotion}")
                print(f"[사용자 발화] {text}")
                print(f"[현재 장면 요약] {scene_context}")

            except Exception as e:
                print(f"[❗예외] {e}")
        time.sleep(0.2)

    # 종료 후 분석 및 Gemini 응답
    if emotion_logs:
        all_faces = [e["face"] for e in emotion_logs]
        all_texts = " ".join([e["text"] for e in emotion_logs])
        all_text_emotions = [e["text_emotion"] for e in emotion_logs]
        all_voice_emotions = [e["voice_emotion"] for e in emotion_logs]
        last_scene = emotion_logs[-1]["scene"]

        final_face = most_common_emotion(all_faces)
        final_text_emotion = most_common_emotion(all_text_emotions)
        final_voice_emotion = most_common_emotion(all_voice_emotions)

        final_emotion = synthesize_emotion_3way(final_face, final_text_emotion, final_voice_emotion)

        context = {
            "weather": "맑음",
            "sleep": "7시간",
            "stress": "중간",
            "location_scene": last_scene,
            "emotion_history": [final_face, final_text_emotion, final_voice_emotion]
        }

        print_emotion_summary(emotion_logs)

        response = generate_response(final_emotion, all_texts, context)
        print("\n🧠 Gemini 응답:")
        print(response)
    else:
        print("❗ 분석된 감정 로그가 없습니다.")

if __name__ == "__main__":
    print("🔧 모델 로딩 중...")
    processor, vlm_model, device = load_smol_vlm()
    whisper_model = load_whisper_model()
    configure_gemini()

    webcam = threading.Thread(target=webcam_thread)
    analyzer = threading.Thread(target=analyze_loop, args=(vlm_model, processor, device, whisper_model))

    webcam.start()
    analyzer.start()

    webcam.join()
    analyzer.join()

    print("👋 종료되었습니다.")
