"""
情绪合成模块 - 结合面部表情、文本情绪和语音情绪
"""

def synthesize_emotion_3way(face: str, text_emotion: str, voice_tone_emotion: str) -> str:
    """
    三向情绪合成 - 结合面部表情、文本情绪和语音情绪
    优先级: 面部表情 > 语音情绪 > 文本情绪
    
    Args:
        face: 面部表情情绪
        text_emotion: 文本内容情绪
        voice_tone_emotion: 语音语调情绪
        
    Returns:
        合成后的最终情绪
    """
    if face != "neutral":
        return face
    elif voice_tone_emotion != "neutral":
        return voice_tone_emotion
    else:
        return text_emotion
