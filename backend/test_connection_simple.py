#!/usr/bin/env python3
"""简单的连接测试脚本"""

import asyncio
import websockets
import json
import time

async def test_simple_connection():
    """测试简单的WebSocket连接"""
    client_id = f"test-{int(time.time())}"
    uri = f"ws://localhost:8181/ws/realtime-chat?client_id={client_id}"
    print(f"连接到: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 1. 首先尝试连接到MiniMax
            connect_msg = {
                "type": "connect_minimax",
                "model": "abab6.5s-chat"
            }
            await websocket.send(json.dumps(connect_msg))
            print("📤 发送MiniMax连接请求")
            
            # 2. 等待连接响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_data = json.loads(response)
                print(f"📥 收到响应: {response_data}")
                
                if response_data.get('type') == 'connection_status' and response_data.get('connected'):
                    print("✅ MiniMax连接成功")
                    
                    # 3. 发送一个简单的文本消息
                    print("📤 发送测试消息")
                    test_msg = {
                        "type": "user_message",
                        "text": "Hello"
                    }
                    await websocket.send(json.dumps(test_msg))
                    
                    # 4. 等待响应
                    timeout_count = 0
                    while timeout_count < 30:  # 最多等待30秒
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=1)
                            response_data = json.loads(response)
                            print(f"📥 收到MiniMax响应: {response_data.get('type', 'unknown')}")
                            
                            if response_data.get('type') == 'minimax_response':
                                data = response_data.get('data', {})
                                if data.get('type') == 'response_complete':
                                    print(f"✅ 收到完整响应: {data.get('text', '')}")
                                    break
                                elif data.get('type') == 'text_delta':
                                    print(f"📝 文本片段: {data.get('text', '')}")
                        except asyncio.TimeoutError:
                            timeout_count += 1
                            print(f"⏳ 等待响应中... ({timeout_count}/30)")
                            continue
                            
                else:
                    print(f"❌ MiniMax连接失败: {response_data}")
                
            except asyncio.TimeoutError:
                print("❌ 连接响应超时")
                
            # 5. 正常关闭连接
            print("🔌 断开连接")
            await websocket.send(json.dumps({"type": "disconnect_minimax"}))
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_connection()) 