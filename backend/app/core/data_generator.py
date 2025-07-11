"""
데이터 생성 도구 모듈
환경 데이터(날씨, 수면, 스트레스 등)와 감정 히스토리 데이터를 생성하는 데 사용
"""

import random
from typing import List

def generate_random_weather() -> str:
    """랜덤 날씨 데이터 생성"""
    weather_conditions = [
        "맑음", "흐림", "구름 많음", "가벼운 비", "중간 비", "폭우", "눈", "안개", "미세먼지"
    ]
    temperatures = list(range(-5, 35))
    temp = random.choice(temperatures)
    condition = random.choice(weather_conditions)
    return f"{condition} {temp}°C"

def generate_random_sleep() -> str:
    """랜덤 수면 데이터 생성"""
    sleep_hours = random.uniform(4.0, 10.0)
    sleep_quality = random.choice(["매우 좋음", "좋음", "보통", "나쁨", "매우 나쁨"])
    return f"{sleep_hours:.1f}시간 ({sleep_quality})"

def generate_random_stress() -> str:
    """랜덤 스트레스 데이터 생성"""
    stress_levels = ["매우 낮음", "낮음", "보통", "높음", "매우 높음"]
    stress_score = random.randint(1, 10)
    level = stress_levels[min(stress_score // 2, 4)]
    return f"{level} ({stress_score}/10)"

def generate_emotion_history(face_emotion: str = None, voice_emotion: str = None, history_length: int = 3) -> List[str]:
    """현재 감지된 감정을 기반으로 감정 히스토리 데이터 생성"""
    emotions = ["평온", "기쁨", "슬픔", "분노", "두려움", "놀람", "혐오", "중성"]
    
    # 영어 감정 라벨을 한국어로 변환
    emotion_mapping = {
        "Neutral": "평온",
        "Happiness": "기쁨", 
        "Sadness": "슬픔",
        "Anger": "분노",
        "Fear": "두려움",
        "Surprise": "놀람",
        "Disgust": "혐오"
    }
    
    # 감정 라벨 변환
    face_emotion_kr = emotion_mapping.get(face_emotion, face_emotion) if face_emotion else None
    voice_emotion_kr = emotion_mapping.get(voice_emotion, voice_emotion) if voice_emotion else None
    
    # 히스토리 리스트 초기화
    history = []
    
    # 감지된 감정 추가
    if face_emotion_kr:
        history.append(face_emotion_kr)
    if voice_emotion_kr and voice_emotion_kr != face_emotion_kr:
        history.append(voice_emotion_kr)
    
    # 감지된 감정이 없으면 랜덤 감정 사용
    if not history:
        history.append(random.choice(emotions))
    
    # 랜덤 히스토리 감정 추가
    while len(history) < history_length:
        # 70% 확률로 유사한 감정 선택, 30% 확률로 랜덤 선택
        if random.random() < 0.7 and len(history) > 0:
            # 유사한 감정 선택 (현재 히스토리에서)
            history.append(random.choice(history))
        else:
            history.append(random.choice(emotions))
    
    return history[:history_length]

def generate_environment_context(face_emotion: str = None, voice_emotion: str = None) -> dict:
    """완전한 환경 컨텍스트 데이터 생성"""
    return {
        "weather": generate_random_weather(),
        "sleep": generate_random_sleep(),
        "stress": generate_random_stress(),
        "emotion_history": generate_emotion_history(face_emotion, voice_emotion)
    } 