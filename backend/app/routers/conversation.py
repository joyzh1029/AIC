from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io

from app.audio.stt import transcribe_audio, load_whisper_model
from app.emotion.fer_emotion import analyze_facial_expression
from app.emotion.ser_emotion import analyze_voice_emotion_korean
from app.multimodal.vlm import summarize_scene, load_smol_vlm
from app.nlp.llm import generate_response

router = APIRouter(prefix="/api/conversation", tags=["conversation"])

# 모델 로딩
whisper_model = load_whisper_model()
processor, vlm_model, device = load_smol_vlm()

def is_search_query(text: str) -> bool:
    keywords = ["추천", "비교", "정보", "알고 싶", "리뷰", "어떤", "검색", "신제품"]
    return any(kw in text for kw in keywords)

@router.post("/respond")
async def unified_conversation_endpoint(
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    text: str = Form("")
):
    try:
        # Step 1: 텍스트 확보
        audio_path = "temp_audio.webm"
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
        stt_text = transcribe_audio(whisper_model, audio_path)
        user_text = stt_text or text or ""

        # Step 2: 검색 의도 감지 (처리는 프론트에서 /search/query로 분기)
        if is_search_query(user_text):
            print("🔎 검색 질의 감지됨. 프론트엔드에서 /search/query 로 분기 요망.")
            return JSONResponse(content={
                "success": False,
                "mode": "search_detected",
                "message": "검색 질의로 감지됨. /search/query 엔드포인트를 사용하세요.",
                "text": user_text
            })

        # Step 3: 감정 분석
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        face_emotion = analyze_facial_expression(pil_image)
        voice_emotion = analyze_voice_emotion_korean(audio_path)
        scene = summarize_scene(pil_image, processor, vlm_model, device)

        context = {
            "location_scene": scene,
            "emotion_history": [face_emotion, voice_emotion]
        }

        response = generate_response(
            face_emotion=face_emotion,
            voice_emotion=voice_emotion,
            scene=scene,
            user_text=user_text,
            context=context
        )

        return JSONResponse(content={
            "success": True,
            "mode": "emotion",
            "response": response,
            "face": face_emotion,
            "voice": voice_emotion,
            "scene": scene,
            "text": user_text
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

