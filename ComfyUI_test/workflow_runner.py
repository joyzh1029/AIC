import json
import requests
import time
from pathlib import Path
import shutil
import sys
from typing import Optional, Dict, Any
import os

#실행코드 : uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# ComfyUI 설정 - 실제 실행 중인 포트로 수정
COMFYUI_URL = "http://127.0.0.1:8000"  # 당신의 ComfyUI가 8000 포트에서 실행 중
IMAGE_NAME = r"ComfyUI_test/static/abc.jpg"
IMAGE_JSON = r"ComfyUI_test/Image_abc.json"
TIMEOUT_SECONDS = 120

def find_comfyui_port():
    """ComfyUI가 실행 중인 포트를 자동으로 찾기"""
    possible_ports = [8000, 8188, 8189, 8190, 3000]
    
    for port in possible_ports:
        try:
            url = f"http://127.0.0.1:{port}"
            response = requests.get(f"{url}/queue", timeout=3)
            if response.status_code == 200:
                print(f"✓ ComfyUI 발견: {url}")
                return url
        except:
            continue
    return None

def check_comfyui_connection() -> bool:
    """ComfyUI 서버 연결 상태 확인"""
    global COMFYUI_URL
    
    print(f"현재 설정된 URL: {COMFYUI_URL}")
    
    # 먼저 설정된 URL로 테스트
    try:
        response = requests.get(f"{COMFYUI_URL}/queue", timeout=5)
        if response.status_code == 200:
            print(f"✓ ComfyUI 연결 성공: {COMFYUI_URL}")
            return True
    except Exception as e:
        print(f"✗ 설정된 URL 연결 실패: {e}")
    
    # 자동으로 포트 찾기
    print("ComfyUI 포트를 자동으로 찾는 중...")
    found_url = find_comfyui_port()
    
    if found_url:
        COMFYUI_URL = found_url
        print(f"✓ ComfyUI URL 업데이트: {COMFYUI_URL}")
        return True
    else:
        print("✗ ComfyUI를 찾을 수 없습니다!")
        return False

def prepare_image() -> Path:
    """이미지 파일 준비"""
    current_dir = Path(__file__).resolve().parent
    
    print(f"현재 디렉토리: {current_dir}")
    
    # 여러 가능한 위치에서 이미지 찾기
    possible_locations = [
        current_dir / IMAGE_NAME,
        current_dir / "static" / IMAGE_NAME,
        current_dir / "input" / IMAGE_NAME,
        current_dir / "images" / IMAGE_NAME
    ]
    
    for location in possible_locations:
        if location.exists():
            print(f"✓ 이미지 파일 발견: {location}")
            
            # static 디렉토리로 복사 (필요시)
            static_dir = current_dir / "static"
            static_dir.mkdir(exist_ok=True)
            target_path = static_dir / IMAGE_NAME
            
            if not target_path.exists():
                shutil.copy(location, target_path)
                print(f"이미지 복사: {location} -> {target_path}")
            
            return target_path
    
    raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {IMAGE_NAME}\n확인한 위치들: {[str(p) for p in possible_locations]}")

def load_workflow() -> Dict[str, Any]:
    """워크플로우 JSON 파일 로드 및 경로 수정"""
    current_dir = Path(__file__).resolve().parent
    workflow_path = current_dir / IMAGE_JSON
    
    print(f"워크플로우 파일 경로: {workflow_path}")
    
    if not workflow_path.exists():
        raise FileNotFoundError(f"워크플로우 JSON 파일을 찾을 수 없습니다: {workflow_path}")
    
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        
        # 이미지 파일 준비
        image_path = prepare_image()
        
        # LoadImage 노드의 이미지 경로 업데이트
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "LoadImage":
                node_data["inputs"]["image"] = IMAGE_NAME
                print(f"노드 {node_id}: 이미지 경로 업데이트됨 -> {IMAGE_NAME}")
        
        print(f"✓ 워크플로우 로드 완료 (노드 수: {len(workflow)})")
        return workflow
        
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파일 파싱 오류: {e}")

def submit_workflow(workflow: Dict[str, Any]) -> str:
    """워크플로우 제출 및 prompt_id 반환"""
    try:
        print("워크플로우 제출 중...")
        print(f"제출 URL: {COMFYUI_URL}/prompt")
        
        # 클라이언트 ID 생성
        client_id = f"fastapi_client_{int(time.time())}"
        
        payload = {
            "prompt": workflow,
            "client_id": client_id
        }
        
        print(f"페이로드 크기: {len(json.dumps(payload))} 문자")
        
        response = requests.post(
            f"{COMFYUI_URL}/prompt", 
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"응답 헤더: {dict(response.headers)}")
            print(f"응답 내용: {response.text}")
            response.raise_for_status()
        
        result = response.json()
        print(f"응답 데이터: {result}")
        
        prompt_id = result.get("prompt_id")
        
        if not prompt_id:
            raise Exception(f"응답에서 prompt_id를 찾을 수 없습니다. 응답: {result}")
        
        print(f"✓ 워크플로우 제출 완료. Prompt ID: {prompt_id}")
        return prompt_id
        
    except requests.Timeout:
        raise Exception("ComfyUI 서버 응답 시간 초과 (30초)")
    except requests.RequestException as e:
        raise Exception(f"ComfyUI 요청 실패: {e}")

#def wait_for_completion(prompt_id: str) -> Dict[str, Any]: #방법1
    """작업 완료 대기 및 결과 반환"""
    print(f"작업 완료 대기 중... (Prompt ID: {prompt_id})")
    
    for attempt in range(TIMEOUT_SECONDS):
        time.sleep(1)
        
        try:
            # 1. 큐 상태 확인
            queue_response = requests.get(f"{COMFYUI_URL}/queue", timeout=10)
            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                
                running = queue_data.get("queue_running", [])
                pending = queue_data.get("queue_pending", [])
                
                # 큐 구조 확인 및 적응
                is_running = False
                is_pending = False
                
                # 실행 중인 작업 확인
                for item in running:
                    if isinstance(item, list) and len(item) > 1 and item[1] == prompt_id:
                        is_running = True
                        break
                    elif isinstance(item, dict) and item.get("prompt_id") == prompt_id:
                        is_running = True
                        break
                
                # 대기 중인 작업 확인  
                for item in pending:
                    if isinstance(item, list) and len(item) > 1 and item[1] == prompt_id:
                        is_pending = True
                        break
                    elif isinstance(item, dict) and item.get("prompt_id") == prompt_id:
                        is_pending = True
                        break
                
                if is_running:
                    if attempt % 10 == 0:
                        print(f"작업 실행 중... ({attempt}초 경과)")
                    continue
                elif is_pending:
                    if attempt % 10 == 0:
                        print(f"작업 대기 중... ({attempt}초 경과)")
                    continue
            
            # 2. 히스토리에서 완료된 작업 확인
            history_response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
            
            if history_response.status_code != 200:
                if attempt % 10 == 0:
                    print(f"히스토리 조회 실패 (상태: {history_response.status_code})")
                continue
                
            data = history_response.json()
            
            if prompt_id not in data:
                if attempt % 20 == 0:
                    print(f"히스토리에서 {prompt_id} 찾는 중... ({attempt}초 경과)")
                continue
            
            job_data = data[prompt_id]
            print(f"작업 데이터 발견: {list(job_data.keys())}")
            
            # 오류 상태 확인
            status = job_data.get("status", {})
            if status.get("status_str") == "error":
                error_details = extract_error_message(status)
                raise Exception(f"ComfyUI 처리 오류: {error_details}")
            
            # 완료 상태 확인
            outputs = job_data.get("outputs", {})
            if outputs:
                print(f"✓ 작업 완료! 출력 노드 수: {len(outputs)}")
                return outputs
                
        except requests.RequestException as e:
            if attempt % 10 == 0:
                print(f"상태 확인 재시도 중... ({attempt}초 경과): {e}")
            continue
        
        # 진행상황 출력
        if attempt % 20 == 0 and attempt > 0:
            print(f"대기 중... ({attempt}초 경과)")
    
    raise TimeoutError(f"작업 완료 대기 시간 초과 ({TIMEOUT_SECONDS}초)")

def wait_for_completion(prompt_id: str) -> Dict[str, Any]: #방법2
    """작업 완료 대기 및 결과 반환 (시간 제한 없음)"""
    print(f"작업 완료 대기 중... (Prompt ID: {prompt_id})")

    attempt = 0
    while True:
        time.sleep(1)
        attempt += 1

        try:
            # 1. 큐 상태 확인
            queue_response = requests.get(f"{COMFYUI_URL}/queue", timeout=10)
            if queue_response.status_code == 200:
                queue_data = queue_response.json()

                running = queue_data.get("queue_running", [])
                pending = queue_data.get("queue_pending", [])

                is_running = False
                is_pending = False

                for item in running:
                    if isinstance(item, list) and len(item) > 1 and item[1] == prompt_id:
                        is_running = True
                        break
                    elif isinstance(item, dict) and item.get("prompt_id") == prompt_id:
                        is_running = True
                        break

                for item in pending:
                    if isinstance(item, list) and len(item) > 1 and item[1] == prompt_id:
                        is_pending = True
                        break
                    elif isinstance(item, dict) and item.get("prompt_id") == prompt_id:
                        is_pending = True
                        break

                if is_running or is_pending:
                    if attempt % 20 == 0:
                        print(f"대기 중... ({attempt}초 경과)")
                    continue

            # 2. 히스토리에서 완료된 작업 확인
            history_response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
            if history_response.status_code != 200:
                if attempt % 20 == 0:
                    print(f"히스토리 조회 실패 (상태: {history_response.status_code})")
                continue

            data = history_response.json()
            if prompt_id not in data:
                if attempt % 20 == 0:
                    print(f"히스토리에서 {prompt_id} 찾는 중... ({attempt}초 경과)")
                continue

            job_data = data[prompt_id]
            print(f"작업 데이터 발견: {list(job_data.keys())}")

            status = job_data.get("status", {})
            if status.get("status_str") == "error":
                error_details = extract_error_message(status)
                raise Exception(f"ComfyUI 처리 오류: {error_details}")

            outputs = job_data.get("outputs", {})
            if outputs:
                print(f"✓ 작업 완료! 출력 노드 수: {len(outputs)}")
                return outputs

        except requests.RequestException as e:
            if attempt % 20 == 0:
                print(f"요청 오류 발생, 재시도 중... ({attempt}초 경과): {e}")
            continue

        if attempt % 60 == 0:
            print(f"⏳ 계속 대기 중... ({attempt}초 경과)")

def extract_error_message(status: Dict[str, Any]) -> str:
    """오류 메시지 추출"""
    messages = status.get('messages', [])
    if messages and isinstance(messages[-1], list) and len(messages[-1]) > 1:
        return messages[-1][1].get('exception_message', 'Unknown error')
    return f"ComfyUI 오류 발생. 상태: {status}"

def process_outputs(outputs: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """출력 결과에서 이미지와 태그 정보 추출"""
    image_filename = None
    tag_result = None
    
    print(f"출력 데이터 처리 중... 노드 수: {len(outputs)}")
    
    for node_id, node_data in outputs.items():
        print(f"노드 {node_id} 데이터: {list(node_data.keys())}")
        
        # 이미지 파일명 추출
        if "images" in node_data and node_data["images"]:
            for img_data in node_data["images"]:
                filename = img_data.get("filename")
                subfolder = img_data.get("subfolder", "")
                if filename:
                    # 서브폴더가 있으면 경로에 포함
                    if subfolder:
                        image_filename = f"{subfolder}/{filename}"
                    else:
                        image_filename = filename
                    print(f"✓ 출력 이미지 발견: {image_filename}")
                    break
        
        # 태그 결과 추출
        if "text" in node_data and node_data["text"]:
            for text_data in node_data["text"]:
                if text_data:
                    tag_result = text_data
                    print("✓ 태그 결과 발견")
                    break
    
    return image_filename, tag_result

def save_results(image_filename: str, tag_result: Optional[str]) -> Path:
    """결과 파일들 저장"""
    if not image_filename:
        raise Exception("저장할 이미지가 없습니다")
    
    # 출력 디렉토리 생성
    current_dir = Path(__file__).resolve().parent
    output_dir = current_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 파일명에서 서브폴더 제거해서 저장
    clean_filename = image_filename.split("/")[-1]
    output_path = output_dir / clean_filename
    
    # ComfyUI에서 이미지 다운로드
    try:
        print("이미지 다운로드 중...")
        
        # URL 인코딩 처리
        from urllib.parse import quote
        encoded_filename = quote(image_filename)
        image_url = f"{COMFYUI_URL}/view?filename={encoded_filename}"
        
        print(f"이미지 URL: {image_url}")
        
        response = requests.get(image_url, timeout=30)
        print(f"다운로드 응답 코드: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"이미지 다운로드 실패: HTTP {response.status_code}")
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"✓ 이미지 저장 완료: {output_path} ({len(response.content)} bytes)")
        
    except Exception as e:
        print(f"✗ 이미지 다운로드 실패: {e}")
        raise Exception(f"이미지를 저장할 수 없습니다: {e}")
    
    # 태그 결과 저장
    if tag_result:
        json_path = output_path.with_suffix(".json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"tags": tag_result}, f, ensure_ascii=False, indent=2)
            print(f"✓ 태그 결과 저장 완료: {json_path}")
        except Exception as e:
            print(f"✗ 태그 결과 저장 실패: {e}")
    
    return output_path

def run_workflow() -> str:
    """메인 워크플로우 실행 함수"""
    try:
        print("=" * 50)
        print("ComfyUI 워크플로우 실행 시작")
        print("=" * 50)
        
        # 1. ComfyUI 연결 확인
        print("1. ComfyUI 연결 확인 중...")
        if not check_comfyui_connection():
            raise Exception(f"ComfyUI 서버에 연결할 수 없습니다. ComfyUI가 실행 중인지 확인하세요.")
        
        # 2. 워크플로우 로드 (이미지 준비 포함)
        print("\n2. 워크플로우 로드 중...")
        workflow = load_workflow()
        
        # 3. 워크플로우 제출
        print("\n3. 워크플로우 제출 중...")
        prompt_id = submit_workflow(workflow)
        
        # 4. 완료 대기
        print("\n4. 작업 완료 대기 중...")
        outputs = wait_for_completion(prompt_id)
        
        # 5. 결과 처리
        print("\n5. 결과 처리 중...")
        image_filename, tag_result = process_outputs(outputs)
        
        # 6. 결과 저장
        print("\n6. 결과 저장 중...")
        output_path = save_results(image_filename, tag_result)
        
        print("=" * 50)
        print(f"✓ 워크플로우 실행 완료: {output_path}")
        print("=" * 50)
        return str(output_path)
        
    except Exception as e:
        print("=" * 50)
        print(f"✗ 오류 발생: {e}")
        print("=" * 50)
        raise

if __name__ == "__main__":
    # 테스트 실행
    try:
        result = run_workflow()
        print(f"테스트 실행 완료: {result}")
    except Exception as e:
        print(f"테스트 실행 실패: {e}")