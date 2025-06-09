#!/usr/bin/env python3
"""简单的连接测试"""

import asyncio
import websockets
import json

async def simple_test():
    uri = "ws://localhost:8181/ws/realtime-chat?client_id=simple_test"
    print(f"连接到: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 连接成功")
            
            # 发送连接请求
            message = {"type": "connect_minimax", "model": "abab6.5s-chat"}
            await websocket.send(json.dumps(message))
            print("📤 发送连接请求")
            
            # 接收一个响应
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"📥 接收响应: {response}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test()) 