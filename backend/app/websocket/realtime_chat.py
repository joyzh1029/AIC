from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import asyncio
import websockets
import json
import logging
from typing import Dict
from ..config import settings

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 활성 WebSocket 연결 저장
active_connections: Dict[str, WebSocket] = {}
# 각 연결에 대한 MiniMax WebSocket 저장
minimax_connections: Dict[str, websockets.WebSocketServerProtocol] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.minimax_connections: Dict[str, websockets.WebSocketServerProtocol] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"클라이언트 {client_id} 연결됨")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.minimax_connections:
            asyncio.create_task(self.close_minimax_connection(client_id))
        logger.info(f"클라이언트 {client_id} 연결 해제됨")

    async def close_minimax_connection(self, client_id: str):
        if client_id in self.minimax_connections:
            try:
                await self.minimax_connections[client_id].close()
                del self.minimax_connections[client_id]
            except Exception as e:
                logger.error(f"{client_id}의 MiniMax 연결 종료 중 오류: {e}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message))

    async def connect_to_minimax(self, client_id: str, model: str = None):
        """MiniMax와의 WebSocket 연결 생성"""
        if model is None:
            model = settings.minimax_ws_default_model
        
        url = f"{settings.minimax_ws_realtime_base_url}?model={model}"
        headers = {
            "Authorization": f"Bearer {settings.minimax_api_key}"
        }
        
        try:
            minimax_ws = await websockets.connect(
                url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )
            self.minimax_connections[client_id] = minimax_ws
            logger.info(f"{client_id}에 대해 MiniMax에 연결됨")
            
            # MiniMax 응답을 수신하는 작업 시작
            asyncio.create_task(self.listen_minimax_responses(client_id))
            
            return True
        except Exception as e:
            logger.error(f"{client_id}의 MiniMax 연결 실패: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"MiniMax 연결 실패: {str(e)}"
            }, client_id)
            return False

    async def listen_minimax_responses(self, client_id: str):
        """MiniMax의 응답을 수신하여 클라이언트에 전달"""
        minimax_ws = self.minimax_connections.get(client_id)
        if not minimax_ws:
            return

        try:
            async for message in minimax_ws:
                try:
                    response_data = json.loads(message)
                    # MiniMax 응답을 클라이언트로 전달
                    await self.send_personal_message({
                        "type": "minimax_response",
                        "data": response_data
                    }, client_id)
                except json.JSONDecodeError as e:
                    logger.error(f"{client_id}의 MiniMax 응답 파싱 실패: {e}")
                except Exception as e:
                    logger.error(f"{client_id}의 MiniMax 응답 처리 중 오류: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"{client_id}의 MiniMax 연결 종료됨")
        except Exception as e:
            logger.error(f"{client_id}의 MiniMax 응답 수신 중 오류: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"MiniMax 연결 오류: {str(e)}"
            }, client_id)

    async def send_to_minimax(self, client_id: str, message: dict):
        """MiniMax로 메시지 전송"""
        minimax_ws = self.minimax_connections.get(client_id)
        if not minimax_ws:
            # 연결이 없으면 새로 연결 시도
            if not await self.connect_to_minimax(client_id):
                return False
            minimax_ws = self.minimax_connections.get(client_id)

        try:
            await minimax_ws.send(json.dumps(message))
            logger.info(f"{client_id}에 대해 MiniMax로 메시지 전송: {message.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"{client_id}의 MiniMax 메시지 전송 실패: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"MiniMax로 메시지 전송 실패: {str(e)}"
            }, client_id)
            return False

manager = ConnectionManager()

@router.websocket("/realtime-chat")
async def websocket_endpoint(websocket: WebSocket, client_id: str = "default"):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "connect_minimax":
                    # MiniMax 연결 생성
                    model = message.get("model", settings.minimax_ws_default_model)
                    success = await manager.connect_to_minimax(client_id, model)
                    await manager.send_personal_message({
                        "type": "connection_status",
                        "connected": success,
                        "model": model
                    }, client_id)
                
                elif message_type == "send_to_minimax":
                    # 메시지를 MiniMax로 전달
                    minimax_message = message.get("message", {})
                    await manager.send_to_minimax(client_id, minimax_message)
                
                elif message_type == "disconnect_minimax":
                    # MiniMax 연결 해제
                    await manager.close_minimax_connection(client_id)
                    await manager.send_personal_message({
                        "type": "connection_status",
                        "connected": False
                    }, client_id)
                
                else:
                    # 알 수 없는 메시지 타입
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"알 수 없는 메시지 타입: {message_type}"
                    }, client_id)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "잘못된 JSON 형식입니다"
                }, client_id)
            except Exception as e:
                logger.error(f"{client_id}의 메시지 처리 중 오류: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"메시지 처리 중 오류: {str(e)}"
                }, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"{client_id}의 WebSocket 오류: {e}")
        manager.disconnect(client_id)
