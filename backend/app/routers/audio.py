from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import logging
from app.audio.stt import transcribe_audio, load_whisper_model
from app.nlp.llm import generate_response
from funasr import AutoModel
import torch
from app.emotion.ser_emotion import analyze_voice_emotion_korean

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audio", tags=["audio"])

# 加载Whisper模型
try:
    whisper_model = load_whisper_model()
    logger.info("Whisper 모델 로딩 완료")
except Exception as e:
    logger.error(f"Whisper 모델 로딩 실패: {str(e)}")
    whisper_model = None

model_dir = "FunAudioLLM/SenseVoiceSmall"
model = AutoModel(
    model=model_dir,
    vad_model="FunAudioLLM/SenseVoiceSmall",
    vad_kwargs={
        "max_single_segment_time": 30000,
        "disable_update": True,
        "model_type": "vad",
        "hub": "hf"
    },
    device="cuda:0" if torch.cuda.is_available() else "cpu",
    hub="hf",
)

def analyze_voice_emotion(audio_path: str) -> str:
    """分析语音情感，调用真实模型"""
    return analyze_voice_emotion_korean(audio_path)

@router.post("/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    """将语音文件转换为文字并生成回复"""
    if not whisper_model:
        raise HTTPException(
            status_code=500,
            detail="Whisper 모델이 초기화되지 않았습니다. 서버를 재시작해주세요."
        )

    try:
        # 检查文件大小
        file_size = 0
        while chunk := await audio.read(8192):
            file_size += len(chunk)
        await audio.seek(0)
        logger.info(f"업로드된 오디오 파일 크기: {file_size} bytes")

        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="파일이 너무 큽니다")

        # 保存上传的音频文件
        content = await audio.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="빈 오디오 파일입니다")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
            temp_webm.write(content)
            temp_webm_path = temp_webm.name
            logger.info(f"임시 WebM 파일 저장됨: {temp_webm_path}")

        # 转换为WAV格式
        temp_wav_path = temp_webm_path.replace(".webm", ".wav")
        convert_webm_to_wav(temp_webm_path, temp_wav_path)
        logger.info(f"오디오 변환 완료: {temp_wav_path}")

        # 语音转文字
        text = transcribe_audio(whisper_model, temp_wav_path)
        if not text:
            raise HTTPException(status_code=400, detail="음성 인식 결과가 없습니다")
        logger.info(f"음성 인식 결과: {text}")

        # 分析语音情感
        try:
            voice_emotion = analyze_voice_emotion(temp_wav_path)
        except Exception as e:
            logger.error(f"음성 감정 분석 실패: {str(e)}")
            voice_emotion = "unknown"
        logger.info(f"음성 감정 분석 결과: {voice_emotion}")

        # 生成LLM回复
        context = {
            "weather": "晴朗",  # 这里可以接入实际的天气API
            "sleep": "充足",    # 这里可以接入实际的睡眠数据
            "stress": "正常",   # 这里可以接入实际的压力数据
            "emotion_history": ["平静", "开心"]  # 这里可以接入实际的情感历史数据
        }

        llm_response = await generate_response(
            emotion=voice_emotion,  # 음성 감정을 emotion으로 사용
            user_text=text,
            context=context,
            ai_mbti_persona=None  # 기본 페르소나 사용
        )

        # 清理临时文件
        try:
            os.unlink(temp_webm_path)
            os.unlink(temp_wav_path)
        except Exception as e:
            logger.warning(f"임시 파일 삭제 실패: {str(e)}")

        return JSONResponse({
            "success": True,
            "text": text,
            "voice_emotion": voice_emotion,
            "response": llm_response,
            "is_search_query": False  # 可以添加查询检测逻辑
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"음성 처리 중 오류 발생: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

def convert_webm_to_wav(input_path: str, output_path: str):
    """将WebM音频转换为WAV格式"""
    try:
        import subprocess
        command = [
            "ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise Exception(f"FFmpeg 변환 실패: {result.stderr.decode()}")
    except Exception as e:
        raise Exception(f"오디오 변환 실패: {str(e)}")

