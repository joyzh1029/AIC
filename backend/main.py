import cv2
import threading
import time
import base64
import io
import json
import numpy as np
import os
import sys
from collections import deque
from queue import Queue

# 현재 디렉토리를 Python 경로에 추가 (상대 경로 임포트를 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 상대 경로로 임포트 변경
from app.vision.webcam import capture_webcam_image
from app.multimodal.vlm import load_smol_vlm, analyze_face_emotion
from app.audio.stt import load_whisper_model, transcribe_stream
from app.vision.fer_emotion import analyze_facial_expression
from app.emotion.emotion import synthesize_emotion
from app.nlp.llm import configure_gemini, generate_response
from app.emotion.summary import most_common_emotion, print_emotion_summary
from PIL import Image

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# 카메라 캡처 API 엔드포인트
@app.post("/api/camera/capture")
async def capture_image(request: Request):
    try:
        # 요청 본문에서 이미지 데이터 가져오기
        data = await request.json()
        image_data = data.get("image", "")
        
        # base64 디코딩
        if image_data.startswith("data:image"):
            # data:image/jpeg;base64, 같은 접두사 제거
            image_data = image_data.split(",")[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 이미지 분석 처리
        face_emotion = analyze_facial_expression(image)
        
        # 이미지를 분석 큐에 추가 (백그라운드 분석용)
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        if not analysis_queue.full():
            analysis_queue.put(frame)
        
        # 응답 반환
        return JSONResponse(content={
            "success": True,
            "emotion": face_emotion,
            "message": "이미지가 성공적으로 분석되었습니다."
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"이미지 처리 중 오류 발생: {str(e)}"})

# FastAPI 앱 실행 (uvicorn에서 실행할 때 사용)
@app.on_event("startup")
def startup_event():
    # 모델 로딩
    global processor, vlm_model, device, whisper_model
    print("🔧 모델 로딩 중...")
    processor, vlm_model, device = load_smol_vlm()
    whisper_model = load_whisper_model()
    configure_gemini()
    
    # 분석 스레드 시작
    global analyzer
    analyzer = threading.Thread(target=analyze_loop, args=(vlm_model, processor, device, whisper_model))
    analyzer.daemon = True
    analyzer.start()

@app.on_event("shutdown")
def shutdown_event():
    # 스레드 종료 이벤트 설정
    running_event.clear()
    print("👋 종료되었습니다.")

if __name__ == "__main__":
    import uvicorn
    import numpy as np
    
    print("🔧 모델 로딩 중...")
    processor, vlm_model, device = load_smol_vlm()
    whisper_model = load_whisper_model()
    configure_gemini()

    # 웹캠 스레드는 독립 실행 모드에서만 사용
    webcam = threading.Thread(target=webcam_thread)
    analyzer = threading.Thread(target=analyze_loop, args=(vlm_model, processor, device, whisper_model))

    webcam.start()
    analyzer.start()

    # FastAPI 앱 실행
    uvicorn.run(app, host="0.0.0.0", port=8181)
    
    # 스레드 종료 대기
    webcam.join()
    analyzer.join()

    print("👋 종료되었습니다.")
