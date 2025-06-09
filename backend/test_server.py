#!/usr/bin/env python3
"""
简单的服务器测试脚本
用于检查端口是否可用和WebSocket连接是否正常
"""

import asyncio
import socket
import sys
from pathlib import Path

def check_port(host='localhost', port=8181):
    """检查端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"端口检查错误: {e}")
        return False

async def test_websocket():
    """测试WebSocket连接"""
    try:
        import websockets
        uri = "ws://localhost:8181/ws/realtime-chat?client_id=test_client"
        print(f"WebSocket 연결 시도: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공!")
            
            # 테스트 메시지 전송
            import json
            test_message = {
                "type": "connect_minimax",
                "model": "abab6.5s-chat"
            }
            await websocket.send(json.dumps(test_message))
            print("✅ 테스트 메시지 전송 완료")
            
            # 응답 대기 (최대 5초)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ 서버 응답 수신: {response[:100]}...")
            except asyncio.TimeoutError:
                print("⚠️ 서버 응답 시간 초과 (5초)")
                
    except Exception as e:
        print(f"❌ WebSocket 연결 실패: {e}")

def main():
    print("🔧 AI Companion 서버 테스트")
    print("=" * 40)
    
    # 1. 포트 확인
    print(f"1. 포트 8181 확인 중...")
    if check_port('localhost', 8181):
        print("✅ 포트 8181이 열려있습니다")
    else:
        print("❌ 포트 8181이 닫혀있습니다")
        print("   서버가 실행 중인지 확인하세요: python run_server.py")
        return
    
    # 2. WebSocket 테스트
    print(f"2. WebSocket 연결 테스트 중...")
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다")
    except Exception as e:
        print(f"테스트 중 오류: {e}")
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    main() 