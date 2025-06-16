from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import os
import json
import httpx

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")

router = APIRouter(prefix="/api", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    voice_id: str = "female-tianmei-jingpin"
    speed: float = 1.0
    vol: float = 1.0
    audio_sample_rate: int = 24000
    bitrate: int = 128000
    format: str = "mp3"


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        if not MINIMAX_API_KEY:
            raise HTTPException(
                status_code=500, detail="MINIMAX_API_KEY가 설정되지 않았습니다."
            )

        if not request.text:
            raise HTTPException(status_code=400, detail="텍스트가 필요합니다")

        print(f"TTS 요청: {request.text[:30]}...")

        # Minimax TTS API 호출
        url = "https://api.minimax.chat/v1/text_to_speech"
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        }

        # Minimax API 정확한 파라미터 사용
        payload = {
            "model": "speech-01",
            "text": request.text,
            "voice_id": request.voice_id,
            "speed": request.speed,
            "vol": request.vol,
            "audio_sample_rate": request.audio_sample_rate,
            "bitrate": request.bitrate,
            "format": request.format,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            print(f"Minimax 응답: {response.status_code}")
            print(f"응답 크기: {len(response.content)} bytes")
            print(f"Content-Type: {response.headers.get('content-type')}")

            # 에러 체크 - JSON 응답인 경우
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                error_data = response.json()
                print(f"API 에러: {error_data}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Minimax API 에러: {error_data.get('message', 'Unknown error')}",
                )

            if response.status_code != 200:
                print(f"HTTP 에러: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Minimax API HTTP 에러: {response.status_code}",
                )

            # 오디오 데이터 검증
            audio_data = response.content
            if len(audio_data) < 1000:  # 너무 작으면 에러일 가능성
                print(f"의심스러운 응답: {audio_data}")
                raise HTTPException(
                    status_code=500, detail="받은 오디오 데이터가 너무 작습니다"
                )

            print(f"TTS 성공: {len(audio_data)} bytes")

            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3",
                    "Cache-Control": "no-cache",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"TTS 전체 에러: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS 실패: {str(e)}")


@router.websocket("/tts/realtime")
async def realtime_tts(websocket: WebSocket):
    await websocket.accept()

    try:
        if not MINIMAX_API_KEY:
            await websocket.send_text(
                json.dumps({"error": "MINIMAX_API_KEY가 설정되지 않았습니다."})
            )
            return

        print("Realtime TTS 연결됨")

        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                text = message.get("text", "")

                if not text:
                    await websocket.send_text(
                        json.dumps({"error": "텍스트가 필요합니다"})
                    )
                    continue

                print(f"Realtime TTS 요청: {text[:30]}...")

                url = "https://api.minimax.chat/v1/text_to_speech"
                headers = {
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "speech-01",
                    "text": text,
                    "voice_id": "female-tianmei-jingpin",
                    "speed": 1.0,
                    "vol": 1.0,
                    "audio_sample_rate": 24000,
                    "bitrate": 128000,
                    "format": "mp3",
                }

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code != 200:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "error": f"Minimax API 오류: {response.status_code} - {response.text}"
                                }
                            )
                        )
                        continue

                    # 오디오 데이터를 base64로 인코딩
                    import base64

                    audio_data = response.content
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")

                    print("Realtime TTS 성공")

                    await websocket.send_text(
                        json.dumps(
                            {"type": "audio", "audio": audio_base64, "format": "mp3"}
                        )
                    )

            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"error": "잘못된 JSON 형식입니다"})
                )
            except Exception as e:
                print(f"Realtime TTS 에러: {str(e)}")
                await websocket.send_text(
                    json.dumps({"error": f"TTS 변환 실패: {str(e)}"})
                )

    except WebSocketDisconnect:
        print("Realtime TTS 연결 해제됨")
    except Exception as e:
        print(f"WebSocket 에러: {str(e)}")


@router.get("/tts/test")
async def test_tts():
    try:
        if not MINIMAX_API_KEY:
            return {"error": "MINIMAX_API_KEY가 설정되지 않았습니다"}

        return {
            "status": "ok",
            "httpx_installed": True,
            "api_key_exists": bool(MINIMAX_API_KEY),
            "api_key_length": len(MINIMAX_API_KEY) if MINIMAX_API_KEY else 0,
            "endpoints": {
                "regular_tts": "/api/tts",
                "realtime_tts": "/api/tts/realtime",
            },
        }
    except Exception as e:
        return {"error": str(e)}


# 에러 날 경우 밑의 실행되는 코드로

# from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel
# import io
# import os
# import json


# MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")

# # ✨ prefix 추가
# router = APIRouter(prefix="/api", tags=["tts"])


# # ==================== TTS 모델 ====================
# class TTSRequest(BaseModel):
#     text: str
#     voice_id: str = "female-tianmei-jingpin"
#     speed: float = 1.0
#     vol: float = 1.0
#     audio_sample_rate: int = 24000
#     bitrate: int = 128000
#     format: str = "mp3"


# # ==================== 기존 TTS 엔드포인트 (유지) ====================
# @router.post("/tts")  # 이제 /api/tts 경로가 됨
# async def text_to_speech(request: TTSRequest):
#     try:
#         # httpx 클라이언트 임포트 및 초기화
#         try:
#             import httpx
#         except ImportError:
#             raise HTTPException(
#                 status_code=500,
#                 detail="httpx 패키지가 설치되지 않았습니다. pip install httpx를 실행하세요.",
#             )

#         if not MINIMAX_API_KEY:
#             raise HTTPException(
#                 status_code=500, detail="MINIMAX_API_KEY가 설정되지 않았습니다."
#             )

#         if not request.text:
#             raise HTTPException(status_code=400, detail="텍스트가 필요합니다")

#         print(f"TTS 요청 받음: {request.text[:50]}...")  # 디버깅용

#         # Minimax TTS API 호출
#         url = "https://api.minimax.chat/v1/text_to_speech"
#         headers = {
#             "Authorization": f"Bearer {MINIMAX_API_KEY}",
#             "Content-Type": "application/json",
#         }
#         payload = {
#             "text": request.text,
#             "voice_id": request.voice_id,
#             "speed": request.speed,
#             "vol": request.vol,
#             "audio_sample_rate": request.audio_sample_rate,
#             "bitrate": request.bitrate,
#             "format": request.format,
#         }

#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.post(url, json=payload, headers=headers)

#             if response.status_code != 200:
#                 raise HTTPException(
#                     status_code=500,
#                     detail=f"Minimax API 오류: {response.status_code} - {response.text}",
#                 )

#         # 오디오 데이터를 바이트로 변환
#         audio_data = response.content

#         print("TTS 변환 성공")  # 디버깅용

#         # StreamingResponse로 오디오 반환
#         return StreamingResponse(
#             io.BytesIO(audio_data),
#             media_type="audio/mpeg",
#             headers={
#                 "Content-Disposition": "inline; filename=speech.mp3",
#                 "Cache-Control": "no-cache",
#             },
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"TTS 에러: {str(e)}")  # 디버깅용
#         import traceback

#         traceback.print_exc()  # 전체 에러 스택 출력
#         raise HTTPException(status_code=500, detail=f"TTS 변환 실패: {str(e)}")


# # ==================== 새로운 Realtime TTS 엔드포인트 ====================
# @router.websocket("/tts/realtime")  # /api/tts/realtime 경로가 됨
# async def realtime_tts(websocket: WebSocket):
#     await websocket.accept()

#     try:
#         # httpx 클라이언트 임포트 및 초기화
#         try:
#             import httpx
#         except ImportError:
#             await websocket.send_text(
#                 json.dumps(
#                     {
#                         "error": "httpx 패키지가 설치되지 않았습니다. pip install httpx를 실행하세요."
#                     }
#                 )
#             )
#             return

#         if not MINIMAX_API_KEY:
#             await websocket.send_text(
#                 json.dumps({"error": "MINIMAX_API_KEY가 설정되지 않았습니다."})
#             )
#             return

#         print("Realtime TTS 연결됨")  # 디버깅용

#         while True:
#             # 클라이언트에서 텍스트 받기
#             data = await websocket.receive_text()

#             try:
#                 message = json.loads(data)
#                 text = message.get("text", "")

#                 if not text:
#                     await websocket.send_text(
#                         json.dumps({"error": "텍스트가 필요합니다"})
#                     )
#                     continue

#                 print(f"Realtime TTS 요청: {text[:50]}...")  # 디버깅용

#                 # Minimax TTS API 호출
#                 url = "https://api.minimax.chat/v1/text_to_speech"
#                 headers = {
#                     "Authorization": f"Bearer {MINIMAX_API_KEY}",
#                     "Content-Type": "application/json",
#                 }
#                 payload = {
#                     "text": text,
#                     "voice_id": "female-tianmei-jingpin",
#                     "speed": 1.0,
#                     "vol": 1.0,
#                     "audio_sample_rate": 24000,
#                     "bitrate": 128000,
#                     "format": "mp3",
#                 }

#                 async with httpx.AsyncClient(timeout=30.0) as client:
#                     response = await client.post(url, json=payload, headers=headers)

#                     if response.status_code != 200:
#                         await websocket.send_text(
#                             json.dumps(
#                                 {
#                                     "error": f"Minimax API 오류: {response.status_code} - {response.text}"
#                                 }
#                             )
#                         )
#                         continue

#                 # 오디오 데이터를 base64로 인코딩해서 전송
#                 import base64

#                 audio_data = response.content
#                 audio_base64 = base64.b64encode(audio_data).decode("utf-8")

#                 print("Realtime TTS 변환 성공")  # 디버깅용

#                 # 오디오 데이터 전송
#                 await websocket.send_text(
#                     json.dumps(
#                         {"type": "audio", "audio": audio_base64, "format": "mp3"}
#                     )
#                 )

#             except json.JSONDecodeError:
#                 await websocket.send_text(
#                     json.dumps({"error": "잘못된 JSON 형식입니다"})
#                 )
#             except Exception as e:
#                 print(f"Realtime TTS 에러: {str(e)}")  # 디버깅용
#                 await websocket.send_text(
#                     json.dumps({"error": f"TTS 변환 실패: {str(e)}"})
#                 )

#     except WebSocketDisconnect:
#         print("Realtime TTS 연결 해제됨")  # 디버깅용
#     except Exception as e:
#         print(f"WebSocket 에러: {str(e)}")  # 디버깅용


# @router.get("/tts/test")  # /api/tts/test 경로가 됨
# async def test_tts():
#     try:
#         # Minimax 설정 확인
#         if not MINIMAX_API_KEY:
#             return {"error": "MINIMAX_API_KEY가 설정되지 않았습니다"}

#         # httpx 패키지 확인
#         try:
#             import httpx

#             return {
#                 "status": "ok",
#                 "httpx_installed": True,
#                 "api_key_exists": bool(MINIMAX_API_KEY),
#                 "api_key_length": len(MINIMAX_API_KEY) if MINIMAX_API_KEY else 0,
#                 "endpoints": {
#                     "regular_tts": "/api/tts",
#                     "realtime_tts": "/api/tts/realtime",
#                 },
#             }
#         except ImportError:
#             return {
#                 "error": "httpx 패키지가 설치되지 않았습니다",
#                 "command": "pip install httpx",
#             }

#     except Exception as e:
#         return {"error": str(e)}
