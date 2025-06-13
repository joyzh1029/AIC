from fastapi import Form, HTTPException
from fastapi.responses import FileResponse
import json
from typing import Iterator
import requests
import os
import tempfile
import glob
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel

# .env에서 환경변수 불러오기
load_dotenv()
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_TTS_URL = f"https://api.minimax.chat/v1/t2a_v2?GroupId={MINIMAX_GROUP_ID}"

class TTSRequest(BaseModel):
    text: str
    speaker: str = "ko"

def build_tts_stream_headers() -> dict:
    """Minimax TTS API 호출을 위한 헤더 생성 함수"""
    return {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'authorization': "Bearer " + MINIMAX_API_KEY,
    }

def build_tts_stream_body(text: str) -> str:
    """TTS 변환 요청에 사용할 payload(body) 생성 함수"""
    body = json.dumps({
        "model": "speech-02-turbo",            # 사용할 TTS 모델
        "text": text,                          # 변환할 텍스트(프론트에서 입력)
        "stream": True,                        # 스트리밍 모드 사용 (응답속도 빠름)
        "voice_setting": {                     # 목소리/감정/속도 등 설정
            "voice_id": "Lovely_Girl",         # 목소리의 id.
            "speed": 1.4,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {                     # 오디오 파일 출력 옵션
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1
        },
        "language_boost": "Korean"             # 한국어 발음 우선
    })
    return body

def call_tts_stream(text: str) -> Iterator[bytes]:
    """Minimax TTS API에 요청, 오디오 청크(HEX 인코딩) yield하는 제너레이터"""
    tts_headers = build_tts_stream_headers()
    tts_body = build_tts_stream_body(text)
    response = requests.request("POST", MINIMAX_TTS_URL, stream=True, headers=tts_headers, data=tts_body)
    for chunk in response.raw:
        # API 스트리밍 형식에 맞게 'data:'로 시작하는 청크만 처리
        if chunk and chunk[:5] == b'data:':
            data = json.loads(chunk[5:])
            if "data" in data and "extra_info" not in data:
                if "audio" in data["data"]:
                    yield data["data"]['audio']  # 오디오 청크(HEX)

def cleanup_old_files(directory=".", pattern="output_*.mp3", max_files=50):
    """mp3 파일이 max_files(50)개 초과 시, 오래된 파일부터 삭제"""
    files = sorted(
        glob.glob(os.path.join(directory, pattern)),
        key=os.path.getmtime   # 수정시간 기준 정렬
    )
    # max_files 초과 파일은 삭제
    if len(files) > max_files:
        for file in files[:len(files)-max_files]:
            try:
                os.remove(file)
            except Exception as e:
                print(f"파일 삭제 실패: {file} ({e})")

async def text_to_speech(text: str = Form(...)):
    """
    프론트엔드에서 전송한 텍스트를 TTS로 변환해 mp3 파일로 반환
    """
    try:
        # 임시 파일로 mp3 저장
        with tempfile.NamedTemporaryFile(delete=False, prefix="output_", suffix=".mp3") as temp_file:
            temp_file_path = temp_file.name
            audio = b""
            for chunk in call_tts_stream(text):
                if chunk and chunk != '\n':
                    decoded_hex = bytes.fromhex(chunk)
                    audio += decoded_hex
            temp_file.write(audio)
        # mp3 파일이 50개 초과 시 오래된 파일 자동 삭제
        cleanup_old_files(directory=".", pattern="output_*.mp3", max_files=50)
        # mp3 파일 반환
        return FileResponse(temp_file_path, media_type="audio/mp3", filename=os.path.basename(temp_file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 변환 실패: {str(e)}")