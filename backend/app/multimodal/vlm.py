# core/vlm.py
# SmolVLM 모델을 로딩하고, 이미지 기반으로 장면을 설명하거나 분위기를 요약함

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForVision2Seq

# SmolVLM 모델 경로 및 디바이스 설정
MODEL_PATH = "HuggingFaceTB/SmolVLM-256M-Instruct"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def load_smol_vlm():
    # VLM 프로세서 및 모델 로딩
    processor = AutoProcessor.from_pretrained(MODEL_PATH)
    model = AutoModelForVision2Seq.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32
    ).to(DEVICE)
    return processor, model, DEVICE

def analyze_face_emotion(image: Image.Image, processor, model, device) -> str:
    # 장면/상황에 대한 설명을 요청하는 멀티모달 프롬프트 구성
    messages = [{
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": "Summerize the atmosphere and what is happening in the scene."}
        ]
    }]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)

    # 이미지 + 텍스트 프롬프트를 모델 입력으로 변환
    inputs = processor(text=prompt, images=[image], return_tensors="pt").to(device)

    # 결과 생성
    ids = model.generate(**inputs, max_new_tokens=500)
    text = processor.batch_decode(ids, skip_special_tokens=True)

    # 텍스트 요약 결과 반환
    return text[0].strip()
