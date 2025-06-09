#!/usr/bin/env python3
"""测试音频功能"""

import asyncio
import websockets
import json
import base64
import os

async def test_audio_functionality():
    """테스트 오디오 기능"""
    uri = "ws://localhost:8181/ws/realtime-chat?client_id=audio_test"
    print(f"연결 시도: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공")
            
            # 1. MiniMax 연결
            connect_message = {"type": "connect_minimax", "model": "abab6.5s-chat"}
            await websocket.send(json.dumps(connect_message))
            print("📤 MiniMax 연결 요청 전송")
            
            # 연결 응답 대기
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 연결 응답: {response_data.get('type', 'unknown')}")
            
            if response_data.get('connected'):
                print("✅ MiniMax 연결 성공!")
                
                # 2. 모의 오디오 데이터 생성 (실제 환경에서는 마이크 입력)
                # 간단한 테스트용 빈 WebM 헤더 생성
                mock_audio_data = base64.b64encode(b"mock_audio_data_for_testing").decode('utf-8')
                
                # 3. 오디오 메시지 전송
                audio_message = {
                    "type": "audio_message",
                    "audio_data": mock_audio_data,
                    "format": "webm",
                    "encoding": "opus"
                }
                await websocket.send(json.dumps(audio_message))
                print("📤 모의 오디오 데이터 전송")
                
                # 4. 응답 대기
                print("⏳ AI 음성 응답 대기...")
                message_count = 0
                while message_count < 15:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        response_data = json.loads(response)
                        message_count += 1
                        
                        msg_type = response_data.get('type', 'unknown')
                        print(f"📥 [{message_count}] 응답 타입: {msg_type}")
                        
                        if msg_type == 'minimax_response':
                            data = response_data.get('data', {})
                            data_type = data.get('type', 'unknown')
                            
                            if data_type == 'audio_delta':
                                print(f"🎵 음성 증분 데이터 수신")
                            elif data_type == 'audio_complete':
                                print(f"✅ 완전한 음성 응답 수신")
                                break
                            elif data_type == 'text_complete':
                                print(f"📝 텍스트 응답: {data.get('text', '')}")
                            elif data_type == 'response_complete':
                                print(f"✅ 응답 완료: {data.get('text', '')}")
                                break
                                
                        elif msg_type == 'error':
                            print(f"❌ 오류: {response_data.get('message', '')}")
                            break
                        elif msg_type == 'ping':
                            print("💓 심박수 신호 수신")
                            
                    except asyncio.TimeoutError:
                        print("⏰ 응답 대기 시간 초과")
                        break
                        
                if message_count >= 15:
                    print("⚠️ 최대 응답 수 도달")
                    
            else:
                print("❌ MiniMax 연결 실패")
                
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    print("🎤 오디오 기능 테스트 시작")
    print("=" * 50)
    asyncio.run(test_audio_functionality())
    print("=" * 50)
    print("🏁 테스트 완료") 