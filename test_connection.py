#!/usr/bin/env python3
"""
ComfyUI 연결 테스트 스크립트
사용법: python test_connection.py
"""

import requests
import json
from pathlib import Path

def test_comfyui_ports():
    """여러 포트에서 ComfyUI 찾기"""
    ports = [8000, 8188, 8189, 8190, 3000, 7860]
    
    print("=== ComfyUI 포트 스캔 ===")
    
    found_ports = []
    
    for port in ports:
        url = f"http://127.0.0.1:{port}"
        try:
            # 기본 페이지 테스트
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✓ 포트 {port}: 웹서버 응답 ({response.status_code})")
                
                # ComfyUI API 엔드포인트 테스트
                api_endpoints = ["/queue", "/history", "/system_stats"]
                api_working = 0
                
                for endpoint in api_endpoints:
                    try:
                        api_response = requests.get(f"{url}{endpoint}", timeout=2)
                        if api_response.status_code == 200:
                            api_working += 1
                            print(f"  - {endpoint}: OK")
                        else:
                            print(f"  - {endpoint}: {api_response.status_code}")
                    except:
                        print(f"  - {endpoint}: 실패")
                
                if api_working >= 2:
                    print(f"  → ComfyUI로 확인됨!")
                    found_ports.append((port, url))
                else:
                    print(f"  → 일반 웹서버 (ComfyUI 아님)")
            else:
                print(f"✗ 포트 {port}: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"✗ 포트 {port}: 연결 거부")
        except requests.exceptions.Timeout:
            print(f"✗ 포트 {port}: 타임아웃")
        except Exception as e:
            print(f"✗ 포트 {port}: {e}")
    
    return found_ports

def test_queue_api(url):
    """큐 API 자세히 테스트"""
    print(f"\n=== 큐 API 테스트: {url} ===")
    
    try:
        response = requests.get(f"{url}/queue", timeout=5)
        print(f"응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("큐 데이터:")
            print(f"  - 실행 중: {len(data.get('queue_running', []))}")
            print(f"  - 대기 중: {len(data.get('queue_pending', []))}")
            
            if data.get('queue_running'):
                print("  실행 중인 작업들:")
                for i, item in enumerate(data['queue_running']):
                    print(f"    {i}: {item}")
            
            return True
        else:
            print(f"큐 API 오류: {response.text}")
            return False
            
    except Exception as e:
        print(f"큐 API 테스트 실패: {e}")
        return False

def test_simple_prompt(url):
    """간단한 프롬프트 제출 테스트"""
    print(f"\n=== 간단한 프롬프트 테스트: {url} ===")
    
    # 매우 간단한 워크플로우 (빈 이미지 생성)
    simple_workflow = {
        "1": {
            "inputs": {
                "width": 256,
                "height": 256, 
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        }
    }
    
    try:
        payload = {
            "prompt": simple_workflow,
            "client_id": "test_client"
        }
        
        response = requests.post(
            f"{url}/prompt",
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"프롬프트 제출 응답: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"성공! Prompt ID: {result.get('prompt_id', 'N/A')}")
            return True
        else:
            print(f"프롬프트 제출 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"프롬프트 테스트 실패: {e}")
        return False

def check_files():
    """필요한 파일들 확인"""
    print("\n=== 파일 확인 ===")
    
    current_dir = Path(__file__).parent
    
    # 체크할 파일들
    files_to_check = [
        "abc.jpg",
        "Image_abc.json",
        "main.py",
        "workflow_runner.py"
    ]
    
    # 가능한 위치들
    locations = [
        current_dir,
        current_dir / "static",
        current_dir / "input",
        current_dir / "images"
    ]
    
    for filename in files_to_check:
        found = False
        for location in locations:
            filepath = location / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"✓ {filename}: {filepath} ({size} bytes)")
                found = True
                break
        
        if not found:
            print(f"✗ {filename}: 찾을 수 없음")

def main():
    """메인 테스트 함수"""
    print("ComfyUI 연결 및 파일 테스트")
    print("=" * 50)
    
    # 1. 파일 확인
    check_files()
    
    # 2. ComfyUI 포트 찾기
    found_ports = test_comfyui_ports()
    
    if not found_ports:
        print("\n❌ ComfyUI를 찾을 수 없습니다!")
        print("ComfyUI가 실행 중인지 확인해주세요.")
        return
    
    # 3. 찾은 포트들에 대해 상세 테스트
    for port, url in found_ports:
        print(f"\n{'='*50}")
        print(f"ComfyUI 상세 테스트: {url}")
        print(f"{'='*50}")
        
        # 큐 API 테스트
        queue_ok = test_queue_api(url)
        
        if queue_ok:
            # 간단한 프롬프트 테스트
            prompt_ok = test_simple_prompt(url)
            
            if prompt_ok:
                print(f"\n✅ {url} - 모든 테스트 통과!")
                print(f"workflow_runner.py에서 COMFYUI_URL을 다음으로 설정하세요:")
                print(f'COMFYUI_URL = "{url}"')
                break
        else:
            print(f"❌ {url} - API 테스트 실패")

if __name__ == "__main__":
    main()