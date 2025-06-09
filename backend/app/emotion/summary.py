# utils/summary.py
# 감정 로그를 분석하여 표정과 음성 감정 분포를 출력하는 유틸리티

from collections import Counter

def most_common_emotion(lst):
    # 리스트에서 가장 많이 등장한 감정 하나 반환
    # 비어있으면 기본값 'neutral' 반환
    return Counter(lst).most_common(1)[0][0] if lst else "neutral"

def print_emotion_summary(logs):
    faces = [e["face"] for e in logs]
    voices = [e["voice_emotion"] for e in logs] 

    print("🧾 감정 요약:")
    print(" - 표정 감정 분포:", Counter(faces))
    print(" - 음성 감정 분포:", Counter(voices))

