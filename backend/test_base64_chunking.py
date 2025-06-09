#!/usr/bin/env python3
"""Base64 청킹 테스트 스크립트"""

import base64
import sys
import os

# 현재 스크립트의 디렉토리 경로
script_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, script_dir)

def test_base64_chunking():
    """Base64 청킹과 재조립 테스트"""
    
    # 테스트용 더미 바이너리 데이터 생성 (1MB)
    test_data = b'A' * (1024 * 1024)  # 1MB of 'A'
    
    # Base64 인코딩
    original_base64 = base64.b64encode(test_data).decode('utf-8')
    print(f"원본 Base64 길이: {len(original_base64)}")
    
    # 청킹 로직 (백엔드와 동일)
    MAX_CHUNK_SIZE = 800000
    safe_chunk_size = (MAX_CHUNK_SIZE // 4) * 4  # 4의 배수로 맞춤
    
    chunks = []
    for i in range(0, len(original_base64), safe_chunk_size):
        chunk = original_base64[i:i + safe_chunk_size]
        chunks.append(chunk)
    
    total_chunks = len(chunks)
    print(f"총 청크 수: {total_chunks}")
    print(f"안전한 청크 크기: {safe_chunk_size}")
    
    # 각 청크 검증
    for i, chunk in enumerate(chunks):
        print(f"청크 {i+1}: 길이 {len(chunk)}")
        try:
            decoded_chunk = base64.b64decode(chunk)
            print(f"  ✅ 청크 {i+1} Base64 디코딩 성공: {len(decoded_chunk)} 바이트")
        except Exception as e:
            print(f"  ❌ 청크 {i+1} Base64 디코딩 실패: {e}")
            return False
    
    # 청크 재조립
    reassembled_base64 = ''.join(chunks)
    print(f"재조립된 Base64 길이: {len(reassembled_base64)}")
    
    # 재조립된 데이터 검증
    try:
        reassembled_data = base64.b64decode(reassembled_base64)
        print(f"✅ 재조립된 Base64 디코딩 성공: {len(reassembled_data)} 바이트")
        
        # 원본 데이터와 비교
        if reassembled_data == test_data:
            print("✅ 원본 데이터와 재조립된 데이터가 일치합니다!")
            return True
        else:
            print("❌ 원본 데이터와 재조립된 데이터가 일치하지 않습니다!")
            return False
            
    except Exception as e:
        print(f"❌ 재조립된 Base64 디코딩 실패: {e}")
        return False

def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n=== 엣지 케이스 테스트 ===")
    
    # 1. 정확히 청크 크기와 같은 데이터
    MAX_CHUNK_SIZE = 800000
    safe_chunk_size = (MAX_CHUNK_SIZE // 4) * 4
    
    # safe_chunk_size / 4 * 3 바이트 (Base64로 인코딩하면 safe_chunk_size 문자)
    exact_size_data = b'X' * (safe_chunk_size // 4 * 3)
    exact_base64 = base64.b64encode(exact_size_data).decode('utf-8')
    print(f"정확한 크기 데이터 Base64 길이: {len(exact_base64)}")
    
    if len(exact_base64) == safe_chunk_size:
        print("✅ 정확한 크기 데이터 테스트 성공")
    else:
        print("❌ 정확한 크기 데이터 테스트 실패")
    
    # 2. 청크 크기보다 조금 큰 데이터
    slightly_larger_data = exact_size_data + b'Y' * 100
    larger_base64 = base64.b64encode(slightly_larger_data).decode('utf-8')
    print(f"조금 큰 데이터 Base64 길이: {len(larger_base64)}")
    
    # 청킹 테스트
    chunks = []
    for i in range(0, len(larger_base64), safe_chunk_size):
        chunk = larger_base64[i:i + safe_chunk_size]
        chunks.append(chunk)
    
    print(f"조금 큰 데이터 청크 수: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  청크 {i+1} 길이: {len(chunk)}")
        try:
            base64.b64decode(chunk)
            print(f"    ✅ 청크 {i+1} 디코딩 성공")
        except Exception as e:
            print(f"    ❌ 청크 {i+1} 디코딩 실패: {e}")

if __name__ == "__main__":
    print("Base64 청킹 테스트 시작...")
    
    success = test_base64_chunking()
    test_edge_cases()
    
    if success:
        print("\n🎉 모든 테스트 통과!")
    else:
        print("\n💥 테스트 실패!")
        sys.exit(1) 