import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime

# 로깅 설정
logger = logging.getLogger(__name__)

# WebSocket 라우터 생성
websocket_router = APIRouter(tags=["WebSocket"])

# 활성 연결 관리를 위한 연결 관리자 클래스
class ConnectionManager:
    def __init__(self):
        # 활성 연결 저장 {client_id: {websocket: WebSocket, user_info: dict}}
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.message_history: Dict[str, List[Dict]] = {}  # 클라이언트별 메시지 히스토리
        
    async def connect(self, websocket: WebSocket, client_id: str, user_info: Optional[Dict] = None):
        """새로운 클라이언트를 연결합니다."""
        await websocket.accept()
        if not user_info:
            user_info = {}
        
        self.active_connections[client_id] = {"websocket": websocket, "user_info": user_info}
        
        # 새 클라이언트에 대한 메시지 히스토리 초기화
        if client_id not in self.message_history:
            self.message_history[client_id] = []
        
        logger.info(f"클라이언트 연결됨: {client_id}, 총 연결 수: {len(self.active_connections)}")
        
    def disconnect(self, client_id: str):
        """클라이언트 연결을 해제합니다."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"클라이언트 연결 해제: {client_id}, 남은 연결 수: {len(self.active_connections)}")
    
    async def send_message(self, message: Dict, client_id: str):
        """특정 클라이언트에게 메시지를 전송합니다."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]["websocket"]
            # 메시지 기록
            self.message_history[client_id].append(message)
            # 메시지 전송
            await websocket.send_text(json.dumps(message))
            logger.debug(f"메시지 전송됨 to {client_id}: {message}")
    
    async def broadcast(self, message: Dict, exclude: Optional[str] = None):
        """모든 클라이언트에게 메시지를 브로드캐스트합니다."""
        for client_id, connection_info in self.active_connections.items():
            if exclude and client_id == exclude:
                continue
            websocket = connection_info["websocket"]
            await websocket.send_text(json.dumps(message))
        logger.debug(f"메시지 브로드캐스트됨: {message}")
    
    def get_connection_info(self, client_id: str) -> Optional[Dict]:
        """클라이언트 연결 정보를 반환합니다."""
        return self.active_connections.get(client_id)
    
    def get_message_history(self, client_id: str) -> List[Dict]:
        """클라이언트의 메시지 기록을 반환합니다."""
        return self.message_history.get(client_id, [])

# 연결 관리자 인스턴스 생성
manager = ConnectionManager()

# 메시지 모델
class ChatMessage(BaseModel):
    client_id: str
    text: str
    sender: str = "user"  # 'user' 또는 'ai'
    timestamp: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "client_id": "user123",
                "text": "안녕하세요?",
                "sender": "user",
                "timestamp": 1625097600
            }
        }

# WebSocket 엔드포인트 정의
@websocket_router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str,
    user_name: Optional[str] = Query(None, description="사용자 이름")
):
    user_info = {"name": user_name} if user_name else {}
    
    await manager.connect(websocket, client_id, user_info)
    
    # 연결 확인 메시지 전송
    await manager.send_message({
        "type": "connection_established",
        "client_id": client_id,
        "message": "연결이 성공적으로 설정되었습니다.",
        "timestamp": datetime.now().timestamp()
    }, client_id)
    
    # 이전 메시지 내역 전송 (옵션)
    history = manager.get_message_history(client_id)
    if history:
        await manager.send_message({
            "type": "history",
            "messages": history
        }, client_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            # JSON 메시지 파싱
            try:
                message_data = json.loads(data)
                logger.debug(f"수신된 메시지: {message_data}")
                
                # 기본 메시지 처리
                if "text" in message_data:
                    # 타임스탬프 추가
                    if "timestamp" not in message_data:
                        message_data["timestamp"] = datetime.now().timestamp()
                    
                    # 사용자 메시지 처리
                    user_message = {
                        "type": "message",
                        "sender": message_data.get("sender", "user"),
                        "text": message_data["text"],
                        "timestamp": message_data["timestamp"]
                    }
                    
                    # 메시지를 모든 클라이언트에게 브로드캐스트 (옵션)
                    # await manager.broadcast(user_message)
                    
                    # 메시지를 보낸 클라이언트에게만 응답
                    await manager.send_message(user_message, client_id)
                    
                    # AI 응답 생성 (간단한 예시)
                    await asyncio.sleep(1)  # 지연 시뮬레이션
                    
                    # 실제 구현에서는 여기에 AI 모델 호출 로직 추가
                    ai_response = "죄송합니다만, 현재 AI 기능은 개발 중입니다. 곧 업데이트하겠습니다."
                    
                    # 사용자 메시지에 기반한 간단한 응답 생성
                    if "안녕" in message_data["text"]:
                        ai_response = "안녕하세요! 무엇을 도와드릴까요?"
                    elif "이름" in message_data["text"]:
                        ai_response = "저는 AI 친구 미나입니다. 반갑습니다!"
                    elif "날씨" in message_data["text"]:
                        ai_response = "오늘은 맑고 화창한 날씨입니다."
                    elif "고마워" in message_data["text"]:
                        ai_response = "천만에요! 더 필요한 것이 있으면 말씀해주세요."
                    
                    # AI 응답 전송
                    ai_message = {
                        "type": "message",
                        "sender": "ai",
                        "text": ai_response,
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    await manager.send_message(ai_message, client_id)
                    
            except json.JSONDecodeError:
                logger.error(f"유효하지 않은 JSON: {data}")
                await manager.send_message({
                    "type": "error",
                    "message": "유효하지 않은 메시지 형식입니다."
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        # 연결 해제 알림 브로드캐스트 (옵션)
        # await manager.broadcast({
        #     "type": "disconnect",
        #     "client_id": client_id,
        #     "message": f"클라이언트 {client_id}가 연결을 해제했습니다."
        # })
    except Exception as e:
        logger.error(f"WebSocket 오류: {str(e)}")
        manager.disconnect(client_id)

# 음성 메시지 처리를 위한 엔드포인트
@websocket_router.websocket("/ws/voice/{client_id}")
async def voice_websocket_endpoint(
    websocket: WebSocket, 
    client_id: str
):
    await manager.connect(websocket, f"voice_{client_id}")
    
    try:
        while True:
            # 음성 데이터 수신 (바이너리)
            data = await websocket.receive_bytes()
            
            # 실제 구현에서는 음성 처리 로직 추가
            logger.debug(f"음성 데이터 수신됨 ({len(data)} bytes)")
            
            # 간단한 응답
            await manager.send_message({
                "type": "voice_received",
                "message": "음성 데이터가 수신되었습니다.",
                "size": len(data)
            }, f"voice_{client_id}")
            
    except WebSocketDisconnect:
        manager.disconnect(f"voice_{client_id}")
    except Exception as e:
        logger.error(f"음성 WebSocket 오류: {str(e)}")
        manager.disconnect(f"voice_{client_id}")

# HTTP 엔드포인트를 통한 WebSocket 메시지 전송 (테스트용)
@websocket_router.post("/send-message/{client_id}")
async def send_message_to_client(client_id: str, message: ChatMessage):
    """HTTP 요청을 통해 특정 클라이언트에게 메시지를 전송합니다."""
    if client_id not in manager.active_connections:
        return {"success": False, "message": f"클라이언트 {client_id}가 연결되어 있지 않습니다."}
    
    await manager.send_message({
        "type": "message",
        "sender": message.sender,
        "text": message.text,
        "timestamp": message.timestamp or datetime.now().timestamp()
    }, client_id)
    
    return {"success": True, "message": "메시지가 성공적으로 전송되었습니다."}
