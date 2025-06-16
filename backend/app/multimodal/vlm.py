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

def summarize_scene(image: Image.Image, processor, model, device) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "Describe the scene. Summerize the description including important keywords."}
            ]
        }
    ]

    # 1. Chat 템플릿을 텍스트 prompt로 생성
    prompt = processor.apply_chat_template(
        messages,
        add_generation_prompt=True
    )

    # 2. prompt와 image를 processor로 encode (여기서만 images 전달)
    inputs = processor(
        text=prompt,
        images=[image],
        return_tensors="pt"
    ).to(device)

    # 3. 모델 생성
    ids = model.generate(**inputs, max_new_tokens=100)
    decoded = processor.batch_decode(ids, skip_special_tokens=True)

    return decoded[0].strip() if decoded else "No scene description detected."
