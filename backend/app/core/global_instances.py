# backend/app/core/global_instances.py

import logging

logger = logging.getLogger(__name__)

# 전역 변수 선언
_global_analyzer = None
_global_vlm_model = None
_global_processor = None
_global_device = None
_global_whisper_model = None

def set_global_analyzer(analyzer_instance):
    """
    전역 분석기 인스턴스를 설정합니다.
    """
    global _global_analyzer
    _global_analyzer = analyzer_instance
    logger.info("Global analyzer instance set.")

def get_global_analyzer():
    """
    설정된 전역 분석기 인스턴스를 가져옵니다.
    """
    if _global_analyzer is None:
        logger.error("Analyzer is not initialized (get_global_analyzer called before set_global_analyzer).")
        raise RuntimeError("Analyzer is not initialized. Call set_global_analyzer first.")
    return _global_analyzer

def set_global_models(vlm_model, processor, device, whisper_model):
    """
    전역 모델 인스턴스들을 설정합니다.
    """
    global _global_vlm_model, _global_processor, _global_device, _global_whisper_model
    _global_vlm_model = vlm_model
    _global_processor = processor
    _global_device = device
    _global_whisper_model = whisper_model
    logger.info("Global VLM, Processor, Device, Whisper models set.")

def get_global_models():
    """
    설정된 전역 모델 인스턴스들을 가져옵니다.
    """
    if _global_vlm_model is None or _global_processor is None or _global_device is None or _global_whisper_model is None:
        logger.error("Models are not initialized (get_global_models called before set_global_models).")
        raise RuntimeError("Models are not initialized. Call set_global_models first.")
    return _global_vlm_model, _global_processor, _global_device, _global_whisper_model