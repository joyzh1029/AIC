#!/usr/bin/env python3
"""
데이터 생성기 기능 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.data_generator import (
    generate_random_weather,
    generate_random_sleep,
    generate_random_stress,
    generate_emotion_history,
    generate_environment_context
)

def test_data_generator():
    """데이터 생성기의 각 기능 테스트"""
    print("🧪 데이터 생성기 기능 테스트")
    print("=" * 50)
    
    # 날씨 생성 테스트
    print("🌤️  날씨 데이터 생성:")
    for i in range(5):
        weather = generate_random_weather()
        print(f"  {i+1}. {weather}")
    
    print("\n😴 수면 데이터 생성:")
    for i in range(5):
        sleep = generate_random_sleep()
        print(f"  {i+1}. {sleep}")
    
    print("\n😰 스트레스 데이터 생성:")
    for i in range(5):
        stress = generate_random_stress()
        print(f"  {i+1}. {stress}")
    
    print("\n😊 감정 히스토리 생성:")
    # 다양한 감정 입력 테스트
    test_emotions = [
        ("Neutral", "Happiness"),
        ("Sadness", "Anger"),
        ("Fear", "Surprise"),
        (None, "기쁨"),
        ("평온", None)
    ]
    
    for i, (face, voice) in enumerate(test_emotions):
        history = generate_emotion_history(face, voice)
        print(f"  {i+1}. 얼굴: {face}, 음성: {voice} -> 히스토리: {history}")
    
    print("\n🌍 완전한 환경 컨텍스트 생성:")
    # 완전한 환경 컨텍스트 테스트
    context1 = generate_environment_context("Neutral", "Happiness")
    print(f"  평온+기쁨: {context1}")
    
    context2 = generate_environment_context("Sadness", "Anger")
    print(f"  슬픔+분노: {context2}")
    
    context3 = generate_environment_context()
    print(f"  입력 없음: {context3}")
    
    print("\n✅ 모든 테스트 완료!")

if __name__ == "__main__":
    test_data_generator() 