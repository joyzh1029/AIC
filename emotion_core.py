# emotion_core.py

def extract_emotion_from_text(text: str) -> str:
    keywords = ["happy", "sad", "angry", "neutral", "surprised", "fear", "disgust"]
    text_lower = text.lower()
    for kw in keywords:
        if kw in text_lower:
            return kw
    return "neutral"

def extract_emotion_from_vlm(vlm_text: str) -> str:
    return extract_emotion_from_text(vlm_text)

def synthesize_emotion(face_emotion: str, voice_emotion: str) -> str:
    """
    얼굴 감정이 'neutral'이 아니면 우선, 아니면 음성 감정 사용
    """
    if face_emotion != "neutral":
        return face_emotion
    return voice_emotion
