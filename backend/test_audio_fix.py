#!/usr/bin/env python3
"""测试音频累积和播放功能修复"""

import asyncio
import websockets
import json
import time

async def test_audio_accumulation():
    """测试音频数据累积功能"""
    client_id = f"audio_fix_test-{int(time.time())}"
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
            
            if response_data.get("type") == "connection_status" and response_data.get("connected"):
                print("✅ MiniMax连接成功")
                
                # 3. 发送欢迎消息请求
                welcome_msg = {
                    "type": "user_message",
                    "text": "안녕하세요"
                }
                await websocket.send(json.dumps(welcome_msg))
                print("📤 发送欢迎消息请求")
                
                # 4. 监听响应
                audio_deltas = []
                transcript = ""
                start_time = time.time()
                
                while time.time() - start_time < 30:  # 30秒超时
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        response_data = json.loads(response)
                        
                        if response_data.get("type") == "minimax_response":
                            data = response_data.get("data", {})
                            event_type = data.get("type", "")
                            
                            if event_type == "audio_delta":
                                audio_data = data.get("audio", "")
                                if audio_data:
                                    audio_deltas.append(audio_data)
                                    print(f"🎵 收到音频增量 #{len(audio_deltas)} (长度: {len(audio_data)})")
                            
                            elif event_type == "response.audio_transcript.done":
                                transcript = data.get("transcript", "")
                                print(f"📝 收到转录文本: {transcript}")
                            
                            elif event_type == "audio_complete":
                                print(f"🎯 音频完成事件")
                                print(f"📊 统计信息:")
                                print(f"   - 总音频增量数: {len(audio_deltas)}")
                                print(f"   - 转录文本: {transcript}")
                                if audio_deltas:
                                    total_length = sum(len(delta) for delta in audio_deltas)
                                    print(f"   - 总音频数据长度: {total_length}")
                                    print("✅ 音频数据接收完整")
                                else:
                                    print("❌ 没有收到音频数据")
                                break
                            
                            elif event_type == "response.output_item.done":
                                print("🏁 响应输出完成")
                                break
                                
                    except asyncio.TimeoutError:
                        print("⏱️ 等待响应超时")
                        break
                        
            else:
                print("❌ MiniMax连接失败")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_audio_accumulation()) 