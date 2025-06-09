#!/usr/bin/env python3
"""连接诊断工具"""

import asyncio
import websockets
import json
import sys

async def diagnose_connection():
    """诊断连接问题"""
    print("🔍 开始连接诊断...")
    
    # 1. 基础WebSocket连接测试
    print("\n1. 基础WebSocket连接测试")
    try:
        uri = "ws://localhost:8181/ws/realtime-chat?client_id=diagnose_test"
        print(f"   连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket连接成功")
            
            # 2. MiniMax连接测试
            print("\n2. MiniMax连接测试")
            connect_msg = {"type": "connect_minimax", "model": "abab6.5s-chat"}
            await websocket.send(json.dumps(connect_msg))
            print("   📤 发送MiniMax连接请求")
            
            # 等待连接响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                print(f"   📥 连接响应: {data}")
                
                if data.get('connected'):
                    print("   ✅ MiniMax连接成功")
                    
                    # 3. 简单文本消息测试
                    print("\n3. 简单文本消息测试")
                    test_msg = {
                        "type": "user_message",
                        "text": "Hello"
                    }
                    await websocket.send(json.dumps(test_msg))
                    print("   📤 发送测试消息: Hello")
                    
                    # 等待响应
                    print("   ⏳ 等待AI响应...")
                    response_count = 0
                    while response_count < 10:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=3)
                            data = json.loads(response)
                            response_count += 1
                            
                            msg_type = data.get('type', 'unknown')
                            print(f"   📥 [{response_count}] {msg_type}")
                            
                            if msg_type == 'minimax_response':
                                response_data = data.get('data', {})
                                if response_data.get('type') in ['text_complete', 'response_complete']:
                                    text = response_data.get('text', '')
                                    print(f"   🤖 AI响应: {text}")
                                    print("   ✅ 文本消息测试成功")
                                    break
                            elif msg_type == 'error':
                                print(f"   ❌ 错误: {data.get('message', '')}")
                                break
                        except asyncio.TimeoutError:
                            print("   ⏰ 响应超时")
                            break
                    
                    if response_count >= 10:
                        print("   ⚠️ 达到最大响应数")
                        
                else:
                    print(f"   ❌ MiniMax连接失败: {data.get('message', 'Unknown error')}")
                    
            except asyncio.TimeoutError:
                print("   ❌ MiniMax连接超时")
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"   ❌ WebSocket连接关闭: {e}")
    except ConnectionRefusedError:
        print("   ❌ 连接被拒绝 - 服务器可能未运行")
        print("   💡 请检查服务器是否在 localhost:8181 运行")
    except asyncio.TimeoutError:
        print("   ❌ WebSocket连接超时")
    except Exception as e:
        print(f"   ❌ 连接错误: {e}")

    print("\n" + "="*50)
    print("🏁 诊断完成")

if __name__ == "__main__":
    asyncio.run(diagnose_connection()) 