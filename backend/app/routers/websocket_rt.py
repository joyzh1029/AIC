from fastapi import APIRouter, WebSocket
import asyncio
import json
import os
import websockets

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ==================== 웹소켓 클래스 ====================
class SimpleRealtimeConnection:
    def __init__(self, client_ws: WebSocket):
        self.client_ws = client_ws
        self.openai_ws = None

    async def connect_openai(self):
        url = (
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        )
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.openai_ws = await websockets.connect(url, extra_headers=headers)
        await self.client_ws.send_text(json.dumps({"type": "connected"}))

    async def start(self):
        await self.connect_openai()
        await asyncio.gather(self.client_loop(), self.openai_loop())

    async def client_loop(self):
        try:
            while True:
                message = await self.client_ws.receive_text()
                if self.openai_ws:
                    await self.openai_ws.send(message)
        except:
            pass

    async def openai_loop(self):
        try:
            async for message in self.openai_ws:
                await self.client_ws.send_text(message)
        except:
            pass


# ==================== 웹소켓 엔드포인트 ====================
@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = SimpleRealtimeConnection(websocket)
    await connection.start()
