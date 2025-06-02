from fastapi import APIRouter, UploadFile, File, HTTPException
from faster_whisper import WhisperModel
import tempfile, shutil, os
import requests  # LLM API 호출용

router = APIRouter()

# Whisper 모델 1회 로드
model = WhisperModel("base", device="cuda", compute_type="int8")

#  LLM 프롬프트 엔드포인트 URL (실제 연결 시 수정필요)
LLM_API_URL = "http://localhost:8080/api/chat"

@router.post("/api/stt-to-chat")
async def stt_to_chat(audio: UploadFile = File(...)):
    """
    음성 → 텍스트(STT) → LLM(프롬프트 입력) → AI 답변 반환
    """
    # 1. 음성파일 임시 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name

    try:
        # 2. STT 처리
        segments, _ = model.transcribe(tmp_path)
        user_text = " ".join([seg.text for seg in segments]).strip()

        if not user_text:
            raise HTTPException(status_code=400, detail="STT 결과가 비어 있습니다.")

        # 3. LLM(chat) API에 프롬프트(텍스트)로 POST 요청
        # 아래는 LLM API가 {"prompt": "..."}를 입력으로 받는다는 가정
        llm_payload = {"prompt": user_text}
        llm_response = requests.post(LLM_API_URL, json=llm_payload, timeout=30)

        if llm_response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"LLM API 호출 실패: {llm_response.text}")

        llm_result = llm_response.json()

        # 4. AI의 답변을 함께 반환 ({"user_text": ..., "ai_reply": ...})
        return {
            "user_text": user_text,
            "ai_reply": llm_result.get("result")  # LLM 엔드포인트 응답 형식에 맞게 수정
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT→LLM 처리 중 오류: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
