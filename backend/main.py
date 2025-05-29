from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
import base64
import urllib.request
import io
from PIL import Image
import websocket

app = FastAPI()

COMFYUI_HOST = "127.0.0.1:8000"
WORKFLOW_FILE = "workflow\Image_0527_v02.json"


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; restrict to specific domains as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 1. 워크플로우 불러오기
def load_workflow():
    if not os.path.exists(WORKFLOW_FILE):
        raise FileNotFoundError(f"Workflow 파일이 존재하지 않습니다: {WORKFLOW_FILE}")
    with open(WORKFLOW_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)

# 2. 이미지 base64로 인코딩
def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# 3. 워크플로우에 이미지 삽입
def update_workflow_with_image(workflow, base64_image):
    workflow["21"]["inputs"]["image"] = base64_image
    return workflow

# 4. 워크플로우 ComfyUI에 보내기
def queue_prompt(prompt):
    data = json.dumps({"prompt": prompt}).encode('utf-8')
    req = urllib.request.Request(
        f"http://{COMFYUI_HOST}/prompt",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code}: {e.reason}")
        print(f"Response body: {e.read().decode('utf-8')}")
        raise

# 5. WebSocket으로 결과 이미지 받기
def get_image(prompt_id):
    ws = websocket.WebSocket()
    ws.connect(f"ws://{COMFYUI_HOST}/ws")

    print(f"Waiting for image for prompt ID: {prompt_id}")

    while True:
        message = ws.recv()
        if isinstance(message, str):
            data = json.loads(message)
            print(f"Received message: {data}")
            if data['type'] == 'executing':
                if data['data']['node'] is None and data['data']['prompt_id'] == prompt_id:
                    print("Execution completed.")
                    break
        elif isinstance(message, bytes):
            print("Received binary data (likely image)")
            image = Image.open(io.BytesIO(message[8:]))  # Skip the first 8 bytes
            ws.close()
            return image
    
    ws.close()
    return None


@app.get("/")
async def root():
    return {"message": "Welcome to AIC API", "endpoints": ["/health", "/wanna-image/"]}

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}

@app.post("/wanna-image/")
async def upload_image(image: UploadFile = File(...)):
    print(">>> /wanna-image/ 요청 도착!")  # 요청 확인용 로그
    try:
        image_bytes = await image.read()
        base64_image = encode_image_to_base64(image_bytes)
        print(base64_image[:30] + "...")  # base64 이미지 일부 출력


        workflow = load_workflow()
        print("Workflow loaded successfully.")
        print("Workflow keys:", workflow.keys())
        workflow = update_workflow_with_image(workflow, base64_image)

        response = queue_prompt(workflow)
        prompt_id = response['prompt_id']
        print(f"Prompt queued successfully with ID: {prompt_id}")

        image_result = get_image(prompt_id)
        if image_result:
            output_filename = "generated_image.png"
            image_result.save(output_filename)
            print(f"Image saved as {output_filename}")
            print(f"Image size: {image_result.size}")
            print(f"Image mode: {image_result.mode}")

            # 이미지 base64로 인코딩해서 반환
            buffered = io.BytesIO()
            image_result.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return {"base64_image": img_base64}
        else:
            print("Failed to receive image from ComfyUI.")
            return {"error": "ComfyUI로부터 이미지를 받지 못했습니다."}

    except Exception as e:
        return {"error": f"이미지 처리 중 오류 발생: {str(e)}"}

    # file_location = os.path.join(UPLOAD_DIR, file.filename)
    # with open(file_location, "wb") as buffer:
    #     shutil.copyfileobj(file.file, buffer)
    # print(f"이미지 저장 위치: {file_location}")
    # # 실제로는 comfyui로 전송 후 변환된 이미지를 반환해야 함
    # # 여기서는 업로드된 이미지를 바로 반환
    # return FileResponse(file_location, media_type="image/png")