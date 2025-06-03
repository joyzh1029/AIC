import threading
import os
from pathlib import Path

from app.vision.webcam import webcam_thread
from app.multimodal.vlm import load_smol_vlm
from app.audio.stt import load_whisper_model
from app.nlp.llm import configure_gemini
from app.emotion.analyzer import analyze_loop, running_event

def initialize_models():
    """加载所有必要的模型"""
    print("🔧 모델 로딩 중...")
    processor, vlm_model, device = load_smol_vlm()
    whisper_model = load_whisper_model()
    configure_gemini()
    
    return processor, vlm_model, device, whisper_model

def start_background_threads(processor, vlm_model, device, whisper_model):
    """启动后台线程"""
    # 웹캠 스레드 시작
    webcam = threading.Thread(target=webcam_thread)
    webcam.daemon = True
    
    # 분석 스레드 시작
    analyzer = threading.Thread(target=analyze_loop, args=(vlm_model, processor, device, whisper_model))
    analyzer.daemon = True
    
    webcam.start()
    analyzer.start()
    
    return webcam, analyzer

def initialize_directories():
    """初始化上传目录"""
    BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    UPLOADS_DIR = BASE_DIR / "uploads"
    ORIGINAL_DIR = UPLOADS_DIR / "original"
    GENERATED_DIR = UPLOADS_DIR / "generated"
    
    os.makedirs(ORIGINAL_DIR, exist_ok=True)
    os.makedirs(GENERATED_DIR, exist_ok=True)
    
    return BASE_DIR

def shutdown_threads():
    """关闭所有线程"""
    running_event.clear()
    print("👋 종료되었습니다.")
