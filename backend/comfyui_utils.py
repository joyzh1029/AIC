import os
import json
import base64
import urllib.request
import io
from PIL import Image
import websocket

COMFYUI_HOST = "192.168.0.76:8000"
WORKFLOW_FILE = "workflow/Image_0613_v03.json"


def load_workflow():
    if not os.path.exists(WORKFLOW_FILE):
        raise FileNotFoundError(f"Workflow 파일이 존재하지 않습니다: {WORKFLOW_FILE}")
    with open(WORKFLOW_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")


def update_workflow_with_image(workflow, base64_image):
    workflow["21"]["inputs"]["image"] = base64_image
    return workflow


def queue_prompt(prompt):
    data = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        f"http://{COMFYUI_HOST}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def get_image(prompt_id):
    ws = websocket.WebSocket()
    ws.connect(f"ws://{COMFYUI_HOST}/ws")
    print(f"Waiting for image for prompt ID: {prompt_id}")
    while True:
        message = ws.recv()
        if isinstance(message, str):
            data = json.loads(message)
            print(f"Received message: {data}")
            if data["type"] == "executing":
                if (
                    data["data"]["node"] is None
                    and data["data"]["prompt_id"] == prompt_id
                ):
                    print("Execution completed.")
                    break
        elif isinstance(message, bytes):
            print("Received binary data (likely image)")
            image = Image.open(io.BytesIO(message[8:]))  # Skip the first 8 bytes
            ws.close()
            return image
    ws.close()
    return None
