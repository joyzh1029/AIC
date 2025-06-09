#!/usr/bin/env python3
"""严格按照MiniMax API标准的测试"""

import asyncio
import websockets
import json

async def test_standard_api():
    """测试标准API调用"""
    print("📋 MiniMax标准API测试")
    
    try:
        # 直连MiniMax API (模拟我们后端的操作)
        minimax_url = "wss://api.minimax.chat/ws/v1/realtime?model=abab6.5s-chat"
        
        # 这里需要从环境变量获取API密钥
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('MINIMAX_API_KEY')
        if not api_key:
            print("❌ 请设置MINIMAX_API_KEY环境变量")
            return
            
        headers = [("Authorization", f"Bearer {api_key}")]
        
        print(f"连接到MiniMax: {minimax_url}")
        async with websockets.connect(minimax_url, additional_headers=headers) as ws:
            print("✅ 直连MiniMax成功")
            
            # 1. 等待session.created
            print("⏳ 等待session.created...")
            while True:
                response = await ws.recv()
                data = json.loads(response)
                print(f"📥 收到: {data.get('type', 'unknown')}")
                
                if data.get('type') == 'session.created':
                    print("✅ 会话创建成功")
                    break
            
            # 2. 发送用户消息 (按照API文档标准格式，添加status)
            user_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "status": "completed",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Hello! Please respond in Chinese."
                        }
                    ]
                }
            }
            
            await ws.send(json.dumps(user_message))
            print("📤 发送用户消息")
            
            # 3. 发送response.create (添加status字段)
            response_create = {
                "event_id": "event_001",
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": "Please respond in Chinese. Be helpful and concise.",
                    "voice": "male-qn-qingse",
                    "output_audio_format": "pcm16",
                    "temperature": 0.7,
                    "max_response_output_tokens": "150",
                    "status": "incomplete"
                }
            }
            
            await ws.send(json.dumps(response_create))
            print("📤 发送response.create")
            
            # 4. 等待响应
            print("⏳ 等待AI响应...")
            response_count = 0
            while response_count < 15:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(response)
                    response_count += 1
                    
                    event_type = data.get('type', 'unknown')
                    print(f"📥 [{response_count}] {event_type}")
                    
                    if event_type == 'response.text.done':
                        text = data.get('text', '')
                        print(f"🤖 AI完整响应: {text}")
                        print("✅ 标准API测试成功!")
                        break
                    elif event_type == 'response.done':
                        print("🔄 响应完成")
                        # 从response.done中提取文本
                        response_obj = data.get('response', {})
                        output = response_obj.get('output', [])
                        for item in output:
                            if item.get('type') == 'message' and item.get('role') == 'assistant':
                                content = item.get('content', [])
                                for c in content:
                                    if c.get('type') == 'text':
                                        print(f"🤖 AI响应: {c.get('text', '')}")
                        print("✅ 标准API测试成功!")
                        break
                    elif event_type == 'error':
                        error_detail = data.get('error', {})
                        print(f"❌ MiniMax错误: {error_detail}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ 响应超时")
                    break
            
            if response_count >= 15:
                print("⚠️ 达到最大响应数")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🧪 开始MiniMax标准API测试")
    print("="*50)
    asyncio.run(test_standard_api())
    print("="*50)
    print("🏁 测试完成") 