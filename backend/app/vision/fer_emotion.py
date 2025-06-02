# core/fer_emotion.py
# FER 라이브러리를 활용한 얼굴 표정 감정 분석 모듈

import cv2
from fer import FER
from PIL import Image
import numpy as np

# FER 감정 추론기 초기화 (MTCNN 얼굴 검출기 포함)
detector = FER(mtcnn=True)

def analyze_facial_expression(image: Image.Image) -> str:
    # PIL 이미지를 OpenCV 형식으로 변환 (BGR)
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # 가장 강하게 감지된 감정을 추출 (최상위 하나만)
    top_emotion = detector.top_emotion(frame)

    if top_emotion:
        emotion, score = top_emotion
        return emotion  # 예: "happy", "sad"
    else:
        return "neutral"  # 감정이 감지되지 않으면 중립 반환

