from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import time
import asyncio
import logging

from app.nlp.llm import generate_response
from app.emotion.synthesizer import synthesize_emotion_3way
from app.core.mbti_data import MBTI_PERSONAS, MBTI_COMPATIBILITY # mbti_data.py에서 임포트

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[float] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: str
    ai_id: str
    user_mbti: Optional[str] = None # ✨ 사용자 MBTI 추가
    relationship_type: Optional[str] = None # ✨ 관계 유형(동질적 or 보완적) 추가
    ai_name: Optional[str] = None # ✨ AI 친구 이름
    generated_image_url: Optional[str] = None # ✨ 생성된 AI 이미지 URL (백엔드에서 사용하진 않지만 프론트엔드에서 전달)
    context: Optional[Dict[str, Any]] = None

@router.post("")
async def chat_endpoint(request: ChatRequest):
    try:
        # 기본 컨텍스트 설정
        context = request.context or {
            "weather": "알 수 없음",
            "sleep": "알 수 없음",
            "stress": "알 수 없음",
            "emotion_history": []
        }
        
        # 사용자 메시지 추출
        user_messages = [msg.content for msg in request.messages if msg.role == "user"]
        user_text = user_messages[-1] if user_messages else ""

        # ✨ 1. 사용자 MBTI 및 관계 유형 유효성 검사 및 AI MBTI 결정
        user_mbti = request.user_mbti
        relationship_type = request.relationship_type

        if not user_mbti or not relationship_type:
            raise HTTPException(
                status_code=400,
                detail="User MBTI and relationship type are required."
            )

        ai_mbti = MBTI_COMPATIBILITY.get(user_mbti, {}).get(relationship_type)

        if not ai_mbti:
            raise HTTPException(
                status_code=400,
                detail=f"Could not determine AI MBTI for user_mbti: {user_mbti} and relationship_type: {relationship_type}"
            )

        ai_persona_text = MBTI_PERSONAS.get(ai_mbti, "당신은 사용자에게 공감하고 위로하는 AI입니다.")
        logging.info(f"Determined AI MBTI: {ai_mbti}, Persona: {ai_persona_text}")


        # 감정 합성 - 세 방향 감정 합성 함수 사용
        # 여기서는 예시로 기본값을 사용하지만, 실제 응용에서는 컨텍스트나 분석에서 가져와야 함
        face_emotion = context.get("face_emotion", "neutral")
        text_emotion = context.get("text_emotion", "neutral")
        voice_emotion = context.get("voice_emotion", "neutral")
        emotion = synthesize_emotion_3way(face_emotion, text_emotion, voice_emotion)
        logging.info(f"Synthesized emotion for LLM: {emotion}")


        # VLM 분석 결과가 있는지 확인
        vlm_analysis = context.get("vlm_analysis")
        if vlm_analysis:
            logging.info(f"Using VLM analysis in response generation: {vlm_analysis[:100]}...")

        # 응답 생성 - 새로운 async 함수 사용
        response_text = await generate_response(
            emotion=emotion,
            user_text=user_text,
            context=context,
            ai_mbti_persona=ai_mbti  # ✨ AI MBTI 페르소나 전달
        )
        logging.info(f"LLM generated response: {response_text}")

        # 응답 구성
        return JSONResponse(content={
            "success": True,
            "response": response_text,
            "emotion": emotion,
            "ai_mbti": ai_mbti,       # 결정된 AI의 MBTI
            "ai_persona": ai_persona_text, # AI의 적용된 페르소나
        })
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/upload")
async def upload_image(image: UploadFile = File(...)):
    logger = logging.getLogger(__name__)
    logger.info("=== Starting image upload process ===")
    
    try:
        logger.info(f"Received image upload request. Filename: {image.filename}, Content-Type: {image.content_type}")
        
        # Read image content
        content = await image.read()
        logger.info(f"Successfully read image content. Size: {len(content)} bytes")
        
        # Ensure upload directory exists
        save_dir = os.path.join("static", "uploads")
        os.makedirs(save_dir, exist_ok=True)
        logger.info(f"Using save directory: {os.path.abspath(save_dir)}")
        
        # Generate unique filename
        filename = f"img_{int(time.time())}_{image.filename}"
        save_path = os.path.join(save_dir, filename)
        logger.info(f"Saving image to: {save_path}")
        
        # Save the image file
        with open(save_path, "wb") as f:
            f.write(content)
        logger.info("Successfully saved image file")
        
        # Analyze image using VLM
        try:
            logger.info("Starting image analysis with VLM...")
            from PIL import Image
            from app.multimodal.vlm import load_smol_vlm, summarize_scene
            
            # Load VLM model
            logger.info("Loading VLM model...")
            start_time = time.time()
            processor, model, device = load_smol_vlm()
            logger.info(f"VLM model loaded in {time.time() - start_time:.2f} seconds")
            
            # Open and analyze image
            logger.info(f"Opening and analyzing image: {save_path}")
            img = Image.open(save_path).convert('RGB')
            logger.info(f"Image opened successfully. Size: {img.size} pixels")
            
            start_analysis = time.time()
            analysis = summarize_scene(img, processor, model, device)
            analysis_time = time.time() - start_analysis
            logger.info(f"Image analysis completed in {analysis_time:.2f} seconds")
            logger.info(f"Analysis result: {analysis[:100]}..." if len(analysis) > 100 else f"Analysis result: {analysis}")
            
            # Generate a response that includes the VLM analysis
            try:
                from app.nlp.llm import generate_response
                
                # Create a context that includes the VLM analysis
                vlm_context = {
                    "weather": "맑음",
                    "sleep": "7시간",
                    "stress": "중간",
                    "location_scene": "이미지 분석 결과 참조",
                    "emotion_history": ["neutral", "neutral", "neutral"],
                    "vlm_analysis": analysis  # Add VLM analysis to context
                }
                
                # Generate a response that includes the VLM analysis
                ai_response = await generate_response(
                    emotion="neutral",
                    user_text="이 사진을 분석해줘",
                    context=vlm_context,
                    ai_mbti_persona=None  # 기본 페르소나 사용
                )
                
                response = {
                    "success": True, 
                    "message": "이미지 업로드 및 분석 성공", 
                    "image_url": f"/static/uploads/{filename}",
                    "analysis": analysis,
                    "ai_response": ai_response
                }
            except Exception as e:
                logger.error(f"Error generating AI response with VLM analysis: {str(e)}")
                response = {
                    "success": True, 
                    "message": "이미지 업로드 성공 (응답 생성 실패)", 
                    "image_url": f"/static/uploads/{filename}",
                    "analysis": analysis
                }
            logger.info("Returning successful response with analysis")
            return JSONResponse(content=response)
            
        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}", exc_info=True)
            response = {
                "success": True, 
                "message": "이미지 업로드 성공 (분석 실패)", 
                "image_url": f"/static/uploads/{filename}",
                "analysis": None,
                "error": str(e)
            }
            logger.error(f"Returning response with analysis error: {response}")
            return JSONResponse(content=response)
            
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}", exc_info=True)
        response = {
            "success": False, 
            "message": "이미지 업로드 실패", 
            "error": str(e)
        }
        logger.error(f"Returning error response: {response}")
        return JSONResponse(
            status_code=500, 
            content=response
        )
