# core/webcam.py
# OpenCV로 웹캠에서 이미지를 캡처하여 PIL 이미지로 반환함

import cv2
import os
from PIL import Image

def capture_webcam_image(save_path=None, show_preview=False) -> Image.Image:
    # 웹캠 장치 연결
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("웹캠을 열 수 없습니다.")

    # 한 프레임 읽기
    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError("이미지 캡처 실패")

    # 프리뷰 표시 (선택 사항)
    if show_preview:
        cv2.imshow("Captured Frame", frame)
        cv2.waitKey(1000)  # 1초간 화면 표시
        cv2.destroyAllWindows()

    # 리소스 해제
    cap.release()

    # OpenCV(BGR) → PIL(RGB) 변환
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame_rgb)

    # 저장 옵션이 있으면 파일로 저장
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        image.save(save_path)

    return image
