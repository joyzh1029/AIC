#!/usr/bin/env python3
"""测试用户消息发送功能"""

import asyncio
import websockets
import json

async def test_user_message():
    uri = "ws://localhost:8181/ws/realtime-chat?client_id=message_test"
    print(f"连接到: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 连接成功")
            
            # 1. 连接到MiniMax
            connect_message = {"type": "connect_minimax", "model": "abab6.5s-chat"}
            await websocket.send(json.dumps(connect_message))
            print("📤 发送连接请求")
            
            # 等待连接响应
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 连接响应: {response_data}")
            
            if response_data.get('connected'):
                print("✅ MiniMax连接成功")
                
                # 2. 发送用户消息
                user_message = {
                    "type": "user_message",
                    "text": "你好！请简单介绍一下你自己。"
                }
                await websocket.send(json.dumps(user_message))
                print("📤 发送用户消息: 你好！请简单介绍一下你自己。")
                
                # 3. 等待AI响应
                print("⏳ 等待AI响应...")
                message_count = 0
                while message_count < 20:  # 最多等待20个消息
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)
                        message_count += 1
                        
                        print(f"📥 [{message_count}] 收到响应: {response_data.get('type', 'unknown')}")
                        
                        if response_data.get('type') == 'minimax_response':
                            data = response_data.get('data', {})
                            event_type = data.get('type')
                            
                            if event_type == 'response.text.delta':
                                print(f"📝 文本增量: {data.get('delta', '')}")
                            elif event_type == 'response.text.done':
                                print(f"✅ 文本完成: {data.get('text', '')}")
                            elif event_type == 'response.done':
                                print("✅ 响应完成!")
                                break
                        elif response_data.get('type') == 'error':
                            print(f"❌ 错误: {response_data.get('message', '')}")
                            break
                            
                    except asyncio.TimeoutError:
                        print("⏰ 超时等待响应")
                        break
                        
                if message_count >= 20:
                    print("⚠️ 达到最大消息数量限制")
            else:
                print("❌ MiniMax连接失败")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🧪 用户消息测试开始")
    print("=" * 50)
    asyncio.run(test_user_message())
    print("=" * 50)
    print("🏁 测试完成") 