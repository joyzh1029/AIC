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
from app.core.data_generator import generate_environment_context

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audio", tags=["audio"])

# Whisper 모델 로딩
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
    """음성 감정 분석, 실제 모델 호출"""
    return analyze_voice_emotion_korean(audio_path)

@router.post("/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    """음성 파일을 텍스트로 변환하고 응답 생성"""
    if not whisper_model:
        raise HTTPException(
            status_code=500,
            detail="Whisper 모델이 초기화되지 않았습니다. 서버를 재시작해주세요."
        )

    try:
        # 파일 크기 확인
        file_size = 0
        while chunk := await audio.read(8192):
            file_size += len(chunk)
        await audio.seek(0)
        logger.info(f"업로드된 오디오 파일 크기: {file_size} bytes")

        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="파일이 너무 큽니다")

        # 업로드된 오디오 파일 저장
        content = await audio.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="빈 오디오 파일입니다")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
            temp_webm.write(content)
            temp_webm_path = temp_webm.name
            logger.info(f"임시 WebM 파일 저장됨: {temp_webm_path}")

        # WAV 형식으로 변환
        temp_wav_path = temp_webm_path.replace(".webm", ".wav")
        convert_webm_to_wav(temp_webm_path, temp_wav_path)
        logger.info(f"오디오 변환 완료: {temp_wav_path}")

        # 음성을 텍스트로 변환
        text = transcribe_audio(whisper_model, temp_wav_path)
        if not text:
            raise HTTPException(status_code=400, detail="음성 인식 결과가 없습니다")
        logger.info(f"음성 인식 결과: {text}")

        # 음성 감정 분석
        try:
            voice_emotion = analyze_voice_emotion(temp_wav_path)
        except Exception as e:
            logger.error(f"음성 감정 분석 실패: {str(e)}")
            voice_emotion = "unknown"
        logger.info(f"음성 감정 분석 결과: {voice_emotion}")

        # 환경 컨텍스트 데이터 생성 (실제 감지된 음성 감정 사용)
        context_data = generate_environment_context(voice_emotion=voice_emotion)
        context_data["location_scene"] = "음성 대화 장면"  # 장면 정보 추가

        logger.info(f"생성된 환경 데이터: {context_data}")

        llm_response = await generate_response(
            emotion=voice_emotion,  # 음성 감정을 emotion으로 사용
            user_text=text,
            context=context_data,
            ai_mbti_persona=None  # 기본 페르소나 사용
        )

        # 임시 파일 정리
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
            "is_search_query": False  # 쿼리 감지 로직 추가 가능
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
    """WebM 오디오를 WAV 형식으로 변환"""
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

