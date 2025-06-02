# core/emotion.py
# 텍스트 또는 VLM 결과로부터 감정을 추출하고, 표정과 음성 감정을 종합함

def extract_emotion_from_text(text: str) -> str:
    # 텍스트에서 사전 정의된 감정 키워드를 찾아 감정을 분류함
    keywords = ["happy", "sad", "angry", "neutral", "surprised", "fear", "disgust"] # 한국어 감정 추가 필요
    text_lower = text.lower()
    for kw in keywords:
        if kw in text_lower:
            return kw
    return "neutral"

def extract_emotion_from_vlm(vlm_text: str) -> str:
    # VLM에서 받은 문장을 그대로 텍스트 감정 분석에 활용
    return extract_emotion_from_text(vlm_text)

def synthesize_emotion(face_emotion: str, voice_emotion: str) -> str:
    # 종합 감정 판단: 얼굴 감정이 'neutral'이 아니면 우선시하고, 아니면 음성 감정 사용
    return face_emotion if face_emotion != "neutral" else voice_emotion
