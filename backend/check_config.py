#!/usr/bin/env python3
"""检查配置文件"""

from app.config import settings

print("=== 配置检查 ===")
print(f"MiniMax API Key 길이: {len(settings.minimax_api_key)}")
print(f"MiniMax API Key 시작: {settings.minimax_api_key[:10] if len(settings.minimax_api_key) > 10 else 'too short'}")
print(f"MiniMax Group ID: {settings.minimax_group_id}")
print(f"MiniMax Default Model: {settings.minimax_ws_default_model}")
print(f"MiniMax WebSocket URL: {settings.minimax_ws_realtime_base_url}")

# 检查是否使用默认值
if settings.minimax_api_key == "default_api_key":
    print("⚠️ 경고: MiniMax API 키가 기본값입니다. .env 파일을 확인하세요.")
else:
    print("✅ MiniMax API 키가 설정되었습니다.")

if settings.minimax_group_id == "default_group_id":
    print("⚠️ 경고: MiniMax Group ID가 기본값입니다.")
else:
    print("✅ MiniMax Group ID가 설정되었습니다.") 