from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import logging

from app.audio.stt import transcribe_audio, load_whisper_model

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

def convert_webm_to_wav(input_path, output_path):
    """将WebM音频转换为WAV格式"""
    try:
        import subprocess
        command = [
            "ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg 변환 실패: {result.stderr.decode()}")
            raise RuntimeError(f"오디오 변환 실패: {result.stderr.decode()}")
            
        logger.info(f"오디오 변환 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"오디오 변환 중 오류 발생: {str(e)}")
        raise RuntimeError(f"오디오 변환 실패: {str(e)}")

@router.post("/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    """将语音文件转换为文字"""
    if not whisper_model:
        raise HTTPException(status_code=500, detail="Whisper 모델이 초기화되지 않았습니다")
        
    temp_webm_path = None
    temp_wav_path = None
    
    try:
        # 检查文件大小
        content = await audio.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="빈 오디오 파일입니다")
            
        logger.info(f"업로드된 오디오 파일 크기: {len(content)} bytes")
        
        # 保存上传的音频文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
            temp_webm.write(content)
            temp_webm_path = temp_webm.name
            
        logger.info(f"임시 WebM 파일 저장됨: {temp_webm_path}")

        # 转换为WAV格式
        temp_wav_path = temp_webm_path.replace(".webm", ".wav")
        convert_webm_to_wav(temp_webm_path, temp_wav_path)

        # 使用Whisper模型进行转写
        text = transcribe_audio(whisper_model, temp_wav_path)

        # 检查是否为搜索查询
        is_search_query = any(kw in text.lower() for kw in ["검색", "찾아", "알려줘", "뭐야", "무엇", "어떤"])
        
        logger.info(f"음성 인식 완료 - 텍스트: {text}, 검색 쿼리: {is_search_query}")

        return JSONResponse({
            "success": True,
            "text": text,
            "is_search_query": is_search_query
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"음성 인식 처리 중 오류 발생: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
        
    finally:
        # 清理临时文件
        try:
            if temp_webm_path and os.path.exists(temp_webm_path):
                os.unlink(temp_webm_path)
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)
        except Exception as e:
            logger.error(f"임시 파일 삭제 중 오류 발생: {str(e)}") 