#!/usr/bin/env python3
"""测试欢迎消息音频功能"""

import asyncio
import websockets
import json
import time

async def test_audio_welcome():
    """测试音频欢迎消息功能"""
    client_id = f"audio_test-{int(time.time())}"
    uri = f"ws://localhost:8181/ws/realtime-chat?client_id={client_id}"
    print(f"连接到: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 1. 连接到MiniMax
            connect_msg = {
                "type": "connect_minimax",
                "model": "abab6.5s-chat"
            }
            await websocket.send(json.dumps(connect_msg))
            print("📤 发送MiniMax连接请求")
            
            # 2. 等待连接响应
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            print(f"📥 连接响应: {response_data}")
            
            if response_data.get('type') == 'connection_status' and response_data.get('connected'):
                print("✅ MiniMax连接成功")
                
                # 3. 发送欢迎消息（模拟前端的欢迎消息请求）
                print("📤 发送欢迎消息请求")
                welcome_msg = {
                    "type": "user_message",
                    "text": "안녕하세요"
                }
                await websocket.send(json.dumps(welcome_msg))
                
                # 4. 等待音频和文本响应
                audio_received = False
                text_received = False
                timeout_count = 0
                
                while (not audio_received or not text_received) and timeout_count < 30:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1)
                        response_data = json.loads(response)
                        event_type = response_data.get('type', 'unknown')
                        
                        print(f"📥 收到事件: {event_type}")
                        
                        if event_type == 'minimax_response':
                            data = response_data.get('data', {})
                            data_type = data.get('type', 'unknown')
                            
                            print(f"   📋 MiniMax响应详情: {data}")  # 添加详细日志
                            
                            if data_type == 'text_complete' or data_type == 'response_complete':
                                text_content = data.get('text', '')
                                if text_content:
                                    print(f"📝 收到文本响应: {text_content}")
                                    text_received = True
                            
                            elif data_type == 'audio_complete':
                                audio_data = data.get('audio', '')
                                if audio_data:
                                    print(f"🔊 收到音频响应 (长度: {len(audio_data)} chars)")
                                    audio_received = True
                            
                            elif data_type == 'text_delta':
                                delta_text = data.get('text', '')
                                if delta_text:
                                    print(f"📝 文本片段: {delta_text}")
                            
                            elif data_type == 'response.text.done':
                                text_content = data.get('text', '')
                                if text_content:
                                    print(f"📝 收到完整文本: {text_content}")
                                    text_received = True
                            
                            elif data_type == 'response.audio.done':
                                audio_data = data.get('audio', '')
                                if audio_data:
                                    print(f"🔊 收到完整音频 (长度: {len(audio_data)} chars)")
                                    audio_received = True
                            
                            elif data_type == 'response.done':
                                print("🏁 响应完成")
                                # 尝试从response.done中提取内容
                                response_obj = data.get('response', {})
                                output = response_obj.get('output', [])
                                for item in output:
                                    if item.get('type') == 'message' and item.get('role') == 'assistant':
                                        content = item.get('content', [])
                                        for c in content:
                                            if c.get('type') == 'text':
                                                text_content = c.get('text', '')
                                                if text_content:
                                                    print(f"📝 从response.done提取文本: {text_content}")
                                                    text_received = True
                                            elif c.get('type') == 'audio':
                                                audio_data = c.get('audio', '')
                                                if audio_data:
                                                    print(f"🔊 从response.done提取音频 (长度: {len(audio_data)} chars)")
                                                    audio_received = True
                        
                        elif event_type == 'ping':
                            # 忽略心跳消息
                            continue
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        print(f"⏳ 等待响应中... ({timeout_count}/30)")
                        continue
                
                # 5. 检查结果
                if audio_received and text_received:
                    print("✅ 成功收到音频和文本响应!")
                elif text_received:
                    print("⚠️  只收到文本响应，没有音频")
                elif audio_received:
                    print("⚠️  只收到音频响应，没有文本")
                else:
                    print("❌ 没有收到完整响应")
                    
            else:
                print(f"❌ MiniMax连接失败: {response_data}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_audio_welcome()) 