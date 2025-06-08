#!/usr/bin/env python3
"""测试消息发送功能"""

import asyncio
import websockets
import json

async def test_message_sending():
    """测试完整的消息发送流程"""
    uri = "ws://localhost:8181/ws/realtime-chat?client_id=test_message_client"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공")
            
            # 1. 连接到MiniMax
            connect_message = {
                "type": "connect_minimax",
                "model": "abab6.5s-chat"
            }
            await websocket.send(json.dumps(connect_message))
            print("📤 MiniMax 연결 요청 전송")
            
            # 等待连接状态
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 응답: {response_data}")
            
            if response_data.get('type') == 'connection_status' and response_data.get('connected'):
                print("✅ MiniMax 연결 성공!")
                
                # 2. 发送用户消息
                user_message = {
                    "type": "user_message", 
                    "text": "안녕하세요! 간단한 인사를 해주세요."
                }
                await websocket.send(json.dumps(user_message))
                print("📤 사용자 메시지 전송: 안녕하세요! 간단한 인사를 해주세요.")
                
                # 3. 等待AI响应
                print("⏳ AI 응답 대기 중...")
                timeout_count = 0
                while timeout_count < 10:  # 최대 30초 대기 (3초 x 10)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        response_data = json.loads(response)
                        print(f"📥 응답: {response_data.get('type', 'unknown')}")
                        
                        if response_data.get('type') == 'minimax_response':
                            data = response_data.get('data', {})
                            if data.get('type') in ['text_complete', 'response_complete']:
                                print(f"🤖 AI 응답: {data.get('text', '')}")
                                break
                            elif data.get('type') == 'text_delta':
                                print(f"📝 텍스트 증분: {data.get('text', '')}")
                        
                        timeout_count = 0  # 응답이 있으면 카운터 리셋
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        print(f"⏰ 대기 중... ({timeout_count}/10)")
                
                if timeout_count >= 10:
                    print("❌ AI 응답 시간 초과")
            else:
                print("❌ MiniMax 연결 실패")
                
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    print("🧪 메시지 전송 테스트 시작")
    print("=" * 50)
    asyncio.run(test_message_sending())
    print("=" * 50)
    print("🏁 테스트 완료") 