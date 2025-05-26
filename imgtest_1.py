import requests
import time
import json
import os

# 1. JSON 워크플로우 로드
with open("testimg1.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)

# 2. 이미지 업로드 (ComfyUI input 폴더에 수동으로 복사해야 함)
input_image = "your_input.jpg"
input_image_name = os.path.basename(input_image)

# 3. 이미지 경로 업데이트 (ComfyUI가 input 이미지 불러오도록 설정)
# 워크플로우에서 이미지 노드를 찾아서 해당 경로로 설정해야 함
for node in workflow.get("prompt", {}).values():
    if node.get("class_type") == "LoadImage":
        node["inputs"]["image"] = input_image_name

# 4. 워크플로우 전송
try:
    res = requests.post("http://127.0.0.1:8003/prompt", json=workflow)
    res.raise_for_status()
    prompt_id = res.json()["prompt_id"]
    print(f"📤 요청 성공 - Prompt ID: {prompt_id}")
except requests.exceptions.RequestException as e:
    print("❌ ComfyUI 서버 연결 실패123:", e)
    exit(1)

# 5. 결과 대기
while True:
    time.sleep(1)
    try:
        result = requests.get(f"http://127.0.0.1:8003/history/{prompt_id}").json()
    except Exception as e:
        print("🔁 결과 확인 중 오류:", e)
        continue

    if "history" in result and prompt_id in result["history"]:
        print("✅ 이미지 생성 완료")
        break

# 6. 결과 이미지 경로 출력
outputs = result["history"][prompt_id]["outputs"]
for output in outputs.values():
    for image in output.get("images", []):
        filename = image["filename"]
        subfolder = image.get("subfolder", "")
        path = os.path.join("output", subfolder, filename)
        print(f"🖼️ 생성된 이미지 경로: {path}")
