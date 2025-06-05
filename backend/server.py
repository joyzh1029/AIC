from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import io
import base64
import requests
from datetime import datetime
import uvicorn
#10~13줄 6.4코드 추가
import os
from PIL import Image
from uuid import uuid4
from fastapi.staticfiles import StaticFiles

from comfyui_utils import (
    load_workflow, encode_image_to_base64, update_workflow_with_image,
    queue_prompt, get_image
)
from db_utils import (
    db, collection, embedding_model,
    ChatData, QueryData, ChatResponse,
    get_similarity_grade, normalize_similarity_score
)


# 이미지 저장 경로 설정(6.4코드 추가/수정)
IMAGE_SAVE_DIR = "static/images"
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static") #6.4코드 추가

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.post("/wanna-image/")
# async def upload_image(image: UploadFile = File(...)):
#     print(">>> /wanna-image/ 요청 도착!")
#     try:
#         image_bytes = await image.read()
#         base64_image = encode_image_to_base64(image_bytes)
#         workflow = load_workflow()
#         workflow = update_workflow_with_image(workflow, base64_image)
#         response = queue_prompt(workflow)
#         prompt_id = response['prompt_id']

#         image_result = get_image(prompt_id)

#         if image_result:
#             buffered = io.BytesIO()
#             image_result.save(buffered, format="PNG")
#             img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8") 
#             return {"base64_image": img_base64}
#         else:
#             return {"error": "ComfyUI로부터 이미지를 받지 못했습니다."}    
        
#     except Exception as e:
#         return {"error": f"이미지 처리 중 오류 발생: {str(e)}"}

#6.4코드 변경/수정/추가
@app.post("/wanna-image/")
async def upload_image(image: UploadFile = File(...)):
    print(">>> /wanna-image/ 요청 도착!")
    try:
        image_bytes = await image.read()
        base64_image = encode_image_to_base64(image_bytes)
        workflow = load_workflow()
        workflow = update_workflow_with_image(workflow, base64_image)
        response = queue_prompt(workflow)
        prompt_id = response['prompt_id']

        image_result = get_image(prompt_id)

        if image_result:
            # ✅ 이미지 파일 저장
            filename = f"{uuid4().hex}.png"
            save_path = os.path.join(IMAGE_SAVE_DIR, filename)
            image_result.save(save_path, format="PNG")

            # ✅ URL로 접근 가능하도록 반환
            image_url = f"http://localhost:8183/static/images/{filename}"
            return {"image_url": image_url}
        else:
            return {"error": "ComfyUI로부터 이미지를 받지 못했습니다."}

    except Exception as e:
        return {"error": f"이미지 처리 중 오류 발생: {str(e)}"}

    
        

@app.post("/save_chat")
async def save_chat(data: ChatData):
    try:
        embedding = embedding_model.encode(data.message).tolist()
        timestamp = datetime.utcnow()
        unique_id = f"{data.user_id}_{int(timestamp.timestamp())}_{abs(hash(data.message))}"

        # Chroma에 저장
        collection.add(
            documents=[data.message],
            embeddings=[embedding],
            ids=[unique_id],
            metadatas=[{
                "user_id": data.user_id,
                "timestamp": timestamp.isoformat()
            }]
        )

        # Firestore 로그 저장
        db.collection("chat_logs").add({
            "user_id": data.user_id,
            "message": data.message,
            "timestamp": timestamp,
            "chroma_id": unique_id
        })

        return {
            "status": "saved",
            "id": unique_id,
            "timestamp": timestamp.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}")



@app.post("/query_chat", response_model=List[ChatResponse])
async def query_chat(data: QueryData):
    try:
        query_embedding = embedding_model.encode(data.query).tolist()
        search_limit = min(data.limit * 3, 50)
        results = collection.query(
            query_embeddings=[query_embedding],
            where={"user_id": data.user_id},
            n_results=search_limit
        )
        responses = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                similarity_score = normalize_similarity_score(results['distances'][0][i])
                if similarity_score < data.similarity_threshold:
                    continue
                similarity_grade = get_similarity_grade(similarity_score)
                response = ChatResponse(
                    id=doc_id,
                    message=results['documents'][0][i],
                    similarity_score=round(similarity_score, 4),
                    similarity_grade=similarity_grade,
                    timestamp=results['metadatas'][0][i].get('timestamp')
                )
                responses.append(response)
        responses.sort(key=lambda x: x.similarity_score, reverse=True)
        responses = responses[:data.limit]
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

@app.get("/chat_history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 10):
    try:
        docs = db.collection("chat_logs")\
            .where("user_id", "==", user_id)\
            .order_by("timestamp", direction="DESCENDING")\
            .limit(limit)\
            .stream()
        history = []
        for doc in docs:
            data = doc.to_dict()
            history.append({
                "id": doc.id,
                "message": data["message"],
                "timestamp": data["timestamp"].isoformat() if data.get("timestamp") else None,
                "chroma_id": data.get("chroma_id")
            })
        return {"user_id": user_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기록 조회 실패: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    print("ComfyUI and DB 작동중... (포트 8183)")
    uvicorn.run(app, host="0.0.0.0", port=8183)