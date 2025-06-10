import whisper
import torch
from transformers import AutoProcessor, AutoModel  # 변경된 import
import threading

# 전역 변수
_shutdown_event = threading.Event()

def initialize_models():
    """모델들을 초기화하고 반환하는 함수"""
    # 장치 설정
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Whisper 모델 로드
    whisper_model = whisper.load_model("base")
    
    # Vision-Language 모델 로드 (클래스 이름 변경)
    processor = AutoProcessor.from_pretrained("microsoft/git-base")
    vlm_model = AutoModel.from_pretrained("microsoft/git-base").to(device)
    
    return processor, vlm_model, device, whisper_model

def shutdown_threads():
    """스레드 종료 이벤트를 설정하는 함수"""
    _shutdown_event.set()