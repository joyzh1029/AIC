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
    # VLM 입력용 프롬프트: 반드시 <image> 토큰 포함해야 함
    prompt = "<image> Summarize the atmosphere and what is happening in the scene."

    inputs = processor(
        text=prompt,
        images=[image],
        return_tensors="pt"
    ).to(device)

    ids = model.generate(**inputs, max_new_tokens=300)
    text = processor.batch_decode(ids, skip_special_tokens=True)

    return text[0].strip() if text else "No scene description detected."

