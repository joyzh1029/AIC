import json
import uuid
import urllib.request
import urllib.parse
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import requests
from io import BytesIO
import os

app = FastAPI()

# ComfyUI 서버 설정
COMFYUI_SERVER = "127.0.0.1:8000"
COMFYUI_URL = f"http://{COMFYUI_SERVER}"

# 고정 워크플로우
WORKFLOW = {
    "3": {
        "inputs": {
            "seed": 437417013841600,
            "steps": 20,
            "cfg": 7,
            "sampler_name": "dpmpp_sde",
            "scheduler": "karras",
            "denoise": 1,
            "model": ["13", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0]
        },
        "class_type": "KSampler"
    },
    "4": {
        "inputs": {
            "ckpt_name": "sdvn53dcutewave_v10.safetensors"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "5": {
        "inputs": {
            "width": 768,
            "height": 768,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage"
    },
    "6": {
        "inputs": {
            "text": ["16", 0],
            "clip": ["13", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "7": {
        "inputs": {
            "text": "bad hands",
            "clip": ["13", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "8": {
        "inputs": {
            "samples": ["3", 0],
            "vae": ["4", 2]
        },
        "class_type": "VAEDecode"
    },
    "9": {
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": ["8", 0]
        },
        "class_type": "SaveImage"
    },
    "11": {
        "inputs": {
            "lora_name": "age_slider_v20.safetensors",
            "strength_model": -4.0,
            "strength_clip": -4.0,
            "model": ["4", 0],
            "clip": ["4", 1]
        },
        "class_type": "LoraLoader"
    },
    "13": {
        "inputs": {
            "lora_name": "emotion_happy_slider_v1.safetensors",
            "strength_model": 1.0,
            "strength_clip": 1.0,
            "model": ["11", 0],
            "clip": ["11", 1]
        },
        "class_type": "LoraLoader"
    },
    "15": {
        "inputs": {
            "image": "input.jpg"
        },
        "class_type": "LoadImage"
    },
    "16": {
        "inputs": {
            "model": "wd-v1-4-moat-tagger-v2",
            "threshold": 0.7,
            "character_threshold": 0.85,
            "replace_underscore": False,
            "trailing_comma": False,
            "exclude_tags": "",
            "image": ["15", 0]
        },
        "class_type": "WD14Tagger|pysssss"
    }
}

def queue_prompt(prompt):
    """프롬프트 실행"""
    client_id = str(uuid.uuid4())
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_image(filename, subfolder="", folder_type="output"):
    """이미지 가져오기"""
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{COMFYUI_URL}/view?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    """히스토리 가져오기"""
    with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

@app.post("/generate")
async def generate_image(file: UploadFile = File(...)):
    """이미지 업로드하고 생성"""
    try:
        # 1. 이미지 업로드
        contents = await file.read()
        files = {"image": ("input.jpg", BytesIO(contents), "image/jpeg")}
        upload_response = requests.post(f"{COMFYUI_URL}/upload/image", files=files)
        
        if upload_response.status_code != 200:
            raise HTTPException(status_code=400, detail="이미지 업로드 실패")
        
        uploaded_name = upload_response.json().get("name", "input.jpg")
        
        # 2. 워크플로우에 업로드된 이미지 이름 설정
        workflow = WORKFLOW.copy()
        workflow["15"]["inputs"]["image"] = uploaded_name
        
        # 3. 워크플로우 실행
        result = queue_prompt(workflow)
        prompt_id = result["prompt_id"]
        
        # 4. 완료까지 대기 (간단한 폴링)
        import time
        while True:
            try:
                history = get_history(prompt_id)
                if prompt_id in history and history[prompt_id].get("status", {}).get("completed", False):
                    break
                time.sleep(1)
            except:
                time.sleep(1)
        
        # 5. 생성된 이미지 정보 가져오기
        history = get_history(prompt_id)
        images = []
        
        for node_id in history[prompt_id]['outputs']:
            node_output = history[prompt_id]['outputs'][node_id]
            if 'images' in node_output:
                for image in node_output['images']:
                    images.append(image['filename'])
        
        if not images:
            raise HTTPException(status_code=500, detail="이미지 생성 실패")
        
        # 🆕 6. 로컬에 자동 저장 추가
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        saved_images = []
        for filename in images:
            try:
                # ComfyUI에서 이미지 가져오기
                image_data = get_image(filename)
                # 로컬에 저장
                file_path = os.path.join(output_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                saved_images.append({
                    "filename": filename,
                    "path": file_path,
                    "saved": True
                })
                print(f"✅ 저장 완료: {file_path}")
            except Exception as e:
                print(f"❌ 저장 실패: {filename} - {str(e)}")
                saved_images.append({
                    "filename": filename,
                    "saved": False,
                    "error": str(e)
                })
        
        return {
            "success": True, 
            "images": images,
            "saved_images": saved_images,
            "message": f"{len(saved_images)}개 이미지 생성 및 저장 완료"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류: {str(e)}")

@app.get("/image/{filename}")
async def download_image(filename: str):
    """생성된 이미지 다운로드"""
    try:
        image_data = get_image(filename)
        # output 폴더에 저장
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "wb") as f:
            f.write(image_data)
        return FileResponse(file_path, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)