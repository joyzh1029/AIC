from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import json
import asyncio
from datetime import datetime
from gtts import gTTS
import io
import logging

from app.services.schedule_service import ScheduleAgentService

router = APIRouter(
    prefix="/api/schedule",
    tags=["schedule"]
)

# 연결 관리자
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

manager = ConnectionManager()
schedule_service = ScheduleAgentService()

# 요청 모델
class ScheduleMessage(BaseModel):
    text: str
    user_id: Optional[str] = None

class TTSRequest(BaseModel):
    text: str

class EventRequest(BaseModel):
    user_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# 일정 관리 채팅 엔드포인트
@router.post("/chat")
async def schedule_chat_endpoint(message: ScheduleMessage):
    """
    일정 관리 관련 채팅 메시지 처리
    """
    try:
        user_id = message.user_id or str(uuid.uuid4())
        
        # 일정 관리 서비스 호출
        result = await schedule_service.process_message(
            user_id=user_id,
            message=message.text
        )
        
        if result.get("success"):
            ai_response = result.get("response", "죄송합니다. 일정 처리 중 오류가 발생했습니다.")
        else:
            ai_response = f"일정 관리 서비스에 연결할 수 없습니다: {result.get('error', '알 수 없는 오류')}"
        
        return {
            "success": True,
            "message": {
                "id": str(uuid.uuid4()),
                "sender": "ai",
                "text": ai_response,
                "time": datetime.now().strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
            }
        }
        
    except Exception as e:
        logging.error(f"Schedule chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")

# 일정 목록 조회 엔드포인트
@router.post("/events")
async def get_events_endpoint(request: EventRequest):
    """
    사용자의 일정 목록 조회
    """
    try:
        events = await schedule_service.get_events(
            user_id=request.user_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return {
            "success": True,
            "events": events
        }
    except Exception as e:
        logging.error(f"Get events error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 조회 중 오류 발생: {str(e)}")

# 대화 기록 초기화 엔드포인트
@router.post("/clear")
async def clear_conversation_endpoint(request: dict):
    """
    사용자의 일정 관리 대화 기록 초기화
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다")
        
        schedule_service.clear_conversation(user_id)
        
        return {
            "success": True,
            "message": "대화 기록이 초기화되었습니다"
        }
    except Exception as e:
        logging.error(f"Clear conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대화 기록 초기화 중 오류 발생: {str(e)}")

# TTS 엔드포인트
@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    텍스트를 음성으로 변환
    """
    try:
        tts = gTTS(text=request.text, lang='ko', slow=False)
        
        audio_buffer = io.BytesIO()
        tts.save(audio_buffer)
        audio_buffer.seek(0)
        
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    except Exception as e:
        logging.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS 처리 실패: {str(e)}")

# WebSocket 엔드포인트
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    실시간 일정 관리 WebSocket 연결
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 메시지 처리
            result = await schedule_service.process_message(
                user_id=client_id,
                message=message_data.get("text", "")
            )
            
            if result.get("success"):
                ai_response = result.get("response", "처리 중 오류가 발생했습니다.")
            else:
                ai_response = f"일정 관리 서비스를 사용할 수 없습니다: {result.get('error', '알 수 없는 오류')}"
            
            # 응답 전송
            await manager.send_message({
                "id": str(uuid.uuid4()),
                "sender": "ai",
                "text": ai_response,
                "time": datetime.now().strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
            }, client_id)
            
    except WebSocketDisconnect:
        logging.info(f"Client {client_id} disconnected")
        manager.disconnect(client_id)
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        manager.disconnect(client_id)
