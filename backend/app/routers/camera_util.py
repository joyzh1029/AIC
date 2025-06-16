from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import base64
import io
import cv2
import numpy as np
from PIL import Image
import threading
import time

router = APIRouter()


# ==================== 카메라 상태 관리 ====================
class CameraState:
    def __init__(self):
        self.camera: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.lock = threading.Lock()
        self.last_frame = None
        self.last_emotion = None


camera_state = CameraState()


# ==================== 카메라 유틸리티 함수 ====================
def analyze_facial_expression(image):
    # 실제 분석 로직이 없으므로 기본값 반환
    # 실제 프로젝트에서는 여기에 감정 분석 로직을 구현
    emotions = ["neutral", "happy", "sad", "angry", "surprised", "fearful", "disgusted"]
    import random

    return random.choice(emotions)


def generate_frames():
    while camera_state.is_running and camera_state.camera is not None:
        try:
            success, frame = camera_state.camera.read()
            if not success:
                break

            # 프레임 저장
            camera_state.last_frame = frame.copy()

            # JPEG으로 인코딩
            ret, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()

            # 멀티파트 응답 형식으로 전송
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

            # 프레임 속도 제어
            time.sleep(0.05)  # 약 20fps
        except Exception as e:
            print(f"Error in generate_frames: {str(e)}")
            break


# ==================== 카메라 엔드포인트 (simple_camera_server) ====================
@router.post("/api/camera/start")
async def start_camera():
    with camera_state.lock:
        try:
            # 이미 실행 중인 경우 중지
            if camera_state.is_running and camera_state.camera is not None:
                camera_state.camera.release()
                camera_state.is_running = False
                time.sleep(0.5)  # 리소스 해제 대기

            # 카메라 초기화
            camera_state.camera = cv2.VideoCapture(0)
            if not camera_state.camera.isOpened():
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": "카메라를 열 수 없습니다."},
                )

            camera_state.is_running = True
            return JSONResponse(
                content={"success": True, "message": "카메라가 시작되었습니다."}
            )
        except Exception as e:
            print(f"Error starting camera: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"카메라 시작 중 오류 발생: {str(e)}",
                },
            )


@router.post("/api/camera/stop")
async def stop_camera():
    with camera_state.lock:
        try:
            if camera_state.camera is not None:
                camera_state.camera.release()
                camera_state.camera = None
            camera_state.is_running = False
            return JSONResponse(
                content={"success": True, "message": "카메라가 중지되었습니다."}
            )
        except Exception as e:
            print(f"Error stopping camera: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"카메라 중지 중 오류 발생: {str(e)}",
                },
            )


@router.get("/api/camera/stream")
async def video_stream():
    if not camera_state.is_running or camera_state.camera is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "카메라가 실행 중이 아닙니다."},
        )

    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


# ==================== 카메라 캡처 엔드포인트 (camera_server + simple_camera_server) ====================
@router.post("/api/camera/capture")
async def capture_image(request: Request = None):
    # camera_server.py 방식 (request body에서 이미지 받기)
    if request:
        try:
            data = await request.json()
            image_data = data.get("image", "")

            # base64 디코딩
            if image_data.startswith("data:image"):
                # data:image/jpeg;base64, 같은 접두사 제거
                image_data = image_data.split(",")[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # 이미지 분석 처리 (간단한 구현)
            face_emotion = analyze_facial_expression(image)

            # 응답 반환
            return JSONResponse(
                content={
                    "success": True,
                    "emotion": face_emotion,
                    "message": "이미지가 성공적으로 분석되었습니다.",
                }
            )
        except Exception as e:
            # 실패시 simple_camera_server 방식으로 폴백
            pass

    # simple_camera_server.py 방식 (카메라에서 직접 캡처)
    with camera_state.lock:
        try:
            if (
                not camera_state.is_running
                or camera_state.camera is None
                or camera_state.last_frame is None
            ):
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": "카메라가 실행 중이 아니거나 프레임이 없습니다.",
                    },
                )

            # 현재 프레임 복사
            frame = camera_state.last_frame.copy()

            # 이미지 분석 처리
            face_emotion = analyze_facial_expression(frame)
            camera_state.last_emotion = face_emotion

            # 이미지를 base64로 인코딩
            ret, buffer = cv2.imencode(".jpg", frame)
            image_bytes = buffer.tobytes()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # 응답 반환
            return JSONResponse(
                content={
                    "success": True,
                    "emotion": face_emotion,
                    "image": f"data:image/jpeg;base64,{image_base64}",
                    "message": "이미지가 성공적으로 분석되었습니다.",
                }
            )
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"이미지 처리 중 오류 발생: {str(e)}",
                },
            )
