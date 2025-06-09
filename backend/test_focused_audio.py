#!/usr/bin/env python3
"""专门测试音频数据处理"""

import asyncio
import websockets
import json
import time

async def test_focused_audio():
    """专门测试音频数据处理过程"""
    client_id = f"focused_test-{int(time.time())}"
    uri = f"ws://localhost:8181/ws/realtime-chat?client_id={client_id}"
    print(f"连接到: {uri}")
    
    audio_chunks = {}
    total_expected_chunks = 0
    final_audio = ""
    
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
                            print("✅ MiniMax连接成功，等待欢迎消息...")
                        else:
                            print("❌ MiniMax连接失败")
                            break
                    
                    elif event_type == "welcome_generating":
                        print("🔄 欢迎消息生成中...")
                        audio_chunks = {}  # 重置音频数据收集
                        total_expected_chunks = 0
                    
                    elif event_type == "welcome_text_complete":
                        text = response_data.get("text", "")
                        print(f"📝 欢迎消息文本: {text[:100]}...")
                    
                    elif event_type == "minimax_response":
                        # 这里不应该收到音频数据，因为环欢迎消息在后端处理
                        data = response_data.get("data", {})
                        if data.get("type") == "audio_delta":
                            print("⚠️ 警告: 收到了不应该出现的audio_delta事件")
                    
                    elif event_type == "welcome_audio_chunk":
                        chunk_index = response_data.get("chunk_index", 0)
                        total_chunks = response_data.get("total_chunks", 0)
                        chunk_audio = response_data.get("audio", "")
                        print(f"🧩 收到音频分块: {chunk_index + 1}/{total_chunks}, 长度={len(chunk_audio)}")
                        
                        # 收集分块
                        audio_chunks[chunk_index] = chunk_audio
                        total_expected_chunks = total_chunks
                        
                        # 检查是否收到了所有分块
                        if len(audio_chunks) == total_chunks:
                            print(f"📊 分块接收完成: 共{total_chunks}块")
                            
                            # 组装完整音频
                            complete_audio = ""
                            for i in range(total_chunks):
                                complete_audio += audio_chunks.get(i, "")
                            
                            print(f"🎵 组装完成音频: 长度={len(complete_audio)}")
                            
                            # 测试base64解码
                            import base64
                            try:
                                decoded = base64.b64decode(complete_audio)
                                print(f"   ✅ 组装音频Base64解码成功: {len(decoded)}字节")
                            except Exception as e:
                                print(f"   ❌ 组装音频Base64解码失败: {e}")
                                # 分析前面的字符
                                print(f"   前100字符: {complete_audio[:100]}")
                                print(f"   后100字符: {complete_audio[-100:]}")
                            
                            final_audio = complete_audio
                    
                    elif event_type == "welcome_audio_complete":
                        audio = response_data.get("audio", "")
                        final_audio = audio
                        print(f"🎵 收到最终音频: 长度={len(audio)}")
                        
                        # 详细分析最终音频
                        if audio:
                            # 检查前面和后面的字符
                            print(f"   前50字符: {audio[:50]}")
                            print(f"   后50字符: {audio[-50:]}")
                            
                            # 检查是否包含异常字符
                            unusual_chars = set()
                            for i, char in enumerate(audio[:1000]):  # 只检查前1000字符
                                if char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=":
                                    unusual_chars.add(f"'{char}'({ord(char)})")
                                    if len(unusual_chars) >= 10:  # 只记录前10个异常字符
                                        break
                            
                            if unusual_chars:
                                print(f"   异常字符: {', '.join(unusual_chars)}")
                            else:
                                print("   ✅ 字符集正常")
                            
                            # 尝试base64解码
                            import base64
                            try:
                                decoded = base64.b64decode(audio)
                                print(f"   ✅ Base64解码成功: {len(decoded)}字节")
                            except Exception as e:
                                print(f"   ❌ Base64解码失败: {e}")
                        
                        print("🎯 音频测试完成")
                        break
                    
                    elif event_type == "error":
                        print(f"❌ 错误: {response_data.get('message', '')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏱️ 等待响应超时，继续...")
                    continue
                    
        # 对比分析
        print(f"\n📊 最终分析:")
        print(f"收集的音频分块数: {len(audio_chunks)}")
        print(f"预期分块数: {total_expected_chunks}")
        print(f"最终音频长度: {len(final_audio)}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_focused_audio()) 