#!/usr/bin/env python3
"""测试PCM16音频功能"""

import asyncio
import websockets
import json
import base64
import struct
import math

def generate_test_pcm16_audio(duration_seconds=2, sample_rate=24000, frequency=440):
    """生成测试用 PCM16 音频数据 (440Hz 사인波)"""
    samples = int(duration_seconds * sample_rate)
    audio_data = []
    
    for i in range(samples):
        # 生成440Hz的正弦波
        sample = math.sin(2 * math.pi * frequency * i / sample_rate)
        # 转换为16位PCM (范围: -32768 到 32767)
        pcm_sample = int(sample * 32767)
        # 限制范围
        pcm_sample = max(-32768, min(32767, pcm_sample))
        audio_data.append(pcm_sample)
    
    # 转换为二进制数据 (little endian)
    binary_data = struct.pack('<' + 'h' * len(audio_data), *audio_data)
    
    # Base64编码
    base64_data = base64.b64encode(binary_data).decode('utf-8')
    
    return base64_data

async def test_pcm_audio_functionality():
    """테스트 PCM16 오디오 기능"""
    uri = "ws://localhost:8181/ws/realtime-chat?client_id=pcm_audio_test"
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
                
                # 2. PCM16 테스트 오디오 생성
                print("🎵 PCM16 테스트 오디오 생성 중...")
                test_audio_base64 = generate_test_pcm16_audio(
                    duration_seconds=2, 
                    sample_rate=24000, 
                    frequency=440  # 440Hz A음
                )
                
                # 3. PCM16 오디오 메시지 전송
                audio_message = {
                    "type": "audio_message",
                    "audio_data": test_audio_base64,
                    "format": "pcm16",
                    "sample_rate": 24000,
                    "channels": 1
                }
                await websocket.send(json.dumps(audio_message))
                print("📤 PCM16 오디오 데이터 전송 (2초, 440Hz, 24kHz)")
                
                # 4. 응답 대기
                print("⏳ AI 음성/텍스트 응답 대기...")
                message_count = 0
                while message_count < 20:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
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
                                # 음성 데이터 크기 로그
                                audio_size = len(data.get('audio', ''))
                                print(f"   오디오 데이터 크기: {audio_size} characters")
                            elif data_type == 'text_delta':
                                text = data.get('text', '')
                                print(f"📝 텍스트 증분: {text}")
                            elif data_type == 'text_complete':
                                print(f"📝 텍스트 완료: {data.get('text', '')}")
                            elif data_type == 'response_complete':
                                print(f"✅ 응답 완료: {data.get('text', '')}")
                                break
                            elif data_type == 'session.created':
                                print("🔗 MiniMax 세션 생성됨")
                                
                        elif msg_type == 'error':
                            error_msg = response_data.get('message', '')
                            print(f"❌ 오류: {error_msg}")
                            break
                        elif msg_type == 'ping':
                            print("💓 심박수 신호")
                            
                    except asyncio.TimeoutError:
                        print("⏰ 응답 대기 시간 초과")
                        break
                        
                if message_count >= 20:
                    print("⚠️ 최대 응답 수 도달")
                    
            else:
                print("❌ MiniMax 연결 실패")
                
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    print("🎤 PCM16 오디오 기능 테스트 시작")
    print("=" * 60)
    asyncio.run(test_pcm_audio_functionality())
    print("=" * 60)
    print("🏁 테스트 완료") 