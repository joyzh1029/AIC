#!/usr/bin/env python3
"""测试音频数据调试"""

import asyncio
import websockets
import json
import time

async def test_audio_debugging():
    """测试音频数据处理"""
    client_id = f"debug_test-{int(time.time())}"
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
            
            start_time = time.time()
            while time.time() - start_time < 60:  # 60秒超时
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    event_type = response_data.get("type", "")
                    
                    if event_type == "connection_status":
                        if response_data.get("connected"):
                            print("✅ MiniMax连接成功，等待环欢迎消息...")
                        else:
                            print("❌ MiniMax连接失败")
                            break
                    
                    elif event_type == "welcome_generating":
                        print("🔄 环欢迎消息生成中...")
                    
                    elif event_type == "welcome_text_complete":
                        text = response_data.get("text", "")
                        print(f"📝 环欢迎消息文本: {text}")
                    
                    elif event_type == "welcome_audio_complete":
                        audio = response_data.get("audio", "")
                        print(f"🎵 环欢迎消息音频: 长度={len(audio)}")
                        
                        # 分析音频数据
                        if audio:
                            # 检查字符类型
                            ascii_count = sum(1 for c in audio if ord(c) < 128)
                            non_ascii_count = len(audio) - ascii_count
                            
                            print(f"   - ASCII字符: {ascii_count}")
                            print(f"   - 非ASCII字符: {non_ascii_count}")
                            print(f"   - 前100字符: {audio[:100]}")
                            print(f"   - 后100字符: {audio[-100:]}")
                            
                            # 尝试base64解码
                            import base64
                            try:
                                decoded = base64.b64decode(audio)
                                print(f"✅ Base64解码成功: {len(decoded)}字节")
                            except Exception as e:
                                print(f"❌ Base64解码失败: {e}")
                                
                                # 尝试清理
                                import re
                                cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', audio)
                                padding = len(cleaned) % 4
                                if padding > 0:
                                    cleaned += '=' * (4 - padding)
                                
                                try:
                                    decoded = base64.b64decode(cleaned)
                                    print(f"✅ 清理后解码成功: 原长度={len(audio)}, 清理后={len(cleaned)}, 解码后={len(decoded)}字节")
                                except Exception as e2:
                                    print(f"❌ 清理后仍失败: {e2}")
                        
                        print("🎯 环欢迎消息测试完成")
                        break
                    
                    elif event_type == "error":
                        print(f"❌ 错误: {response_data.get('message', '')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏱️ 等待响应超时，继续...")
                    continue
                    
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_audio_debugging()) 