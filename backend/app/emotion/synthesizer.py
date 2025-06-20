"""
감정 합성 모듈 - 얼굴 표정, 텍스트 감정, 음성 감정 결합
"""


def synthesize_emotion_3way(
    face: str, text_emotion: str, voice_tone_emotion: str
) -> str:
    """
    3방향 감정 합성 - 얼굴 표정, 텍스트 감정, 음성 감정 결합
    우선순위: 얼굴 표정 > 음성 감정 > 텍스트 감정

    Args:
        face: 얼굴 표정 감정
        text_emotion: 텍스트 내용 감정
        voice_tone_emotion: 음성 어조 감정

    Returns:
        합성된 최종 감정
    """
    if face != "neutral":
        return face
    elif voice_tone_emotion != "neutral":
        return voice_tone_emotion
    else:
        return text_emotion
