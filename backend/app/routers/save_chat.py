from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List
from pprint import pprint

from db_utils import (
    db,
    collection,
    embedding_model,
    ChatData,
    QueryData,
    ChatResponse,
    get_similarity_grade,
    normalize_similarity_score,
)

# ✨ prefix 추가
router = APIRouter(prefix="/api", tags=["chat"])


# ==================== 채팅 관련 엔드포인트 ====================
@router.post("/save_chat")  # /api/save_chat
async def save_chat(data: ChatData):
    try:
        embedding = embedding_model.encode(data.message).tolist()
        timestamp = datetime.utcnow()
        unique_id = (
            f"{data.user_id}_{int(timestamp.timestamp())}_{abs(hash(data.message))}"
        )

        # Chroma에 저장
        collection.add(
            documents=[data.message],
            embeddings=[embedding],
            ids=[unique_id],
            metadatas=[{"user_id": data.user_id, "timestamp": timestamp.isoformat()}],
        )

        # Firestore 로그 저장
        db.collection("chat_logs").add(
            {
                "user_id": data.user_id,
                "message": data.message,
                "timestamp": timestamp,
                "chroma_id": unique_id,
            }
        )

        return {"status": "saved", "id": unique_id, "timestamp": timestamp.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}")


@router.post("/query_chat", response_model=List[ChatResponse])  # /api/query_chat
async def query_chat(data: QueryData):
    try:
        query_embedding = embedding_model.encode(data.query).tolist()
        search_limit = min(data.limit * 3, 50)
        results = collection.query(
            query_embeddings=[query_embedding],
            where={"user_id": data.user_id},
            n_results=search_limit,
        )
        responses = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                similarity_score = normalize_similarity_score(
                    results["distances"][0][i]
                )
                if similarity_score < data.similarity_threshold:
                    continue
                similarity_grade = get_similarity_grade(similarity_score)
                response = ChatResponse(
                    id=doc_id,
                    message=results["documents"][0][i],
                    similarity_score=round(similarity_score, 4),
                    similarity_grade=similarity_grade,
                    timestamp=results["metadatas"][0][i].get("timestamp"),
                )
                responses.append(response)
        responses.sort(key=lambda x: x.similarity_score, reverse=True)
        responses = responses[: data.limit]
        # pprint(responses)
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")


@router.get("/chat_history/{user_id}")  # /api/chat_history/{user_id}
async def get_chat_history(user_id: str, limit: int = 10):
    try:
        # 방법 1: 인덱스 없이 단순 쿼리 (모든 문서 가져온 후 필터링)
        docs = db.collection("chat_logs").stream()

        # 메모리에서 필터링 및 정렬
        user_chats = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("user_id") == user_id:
                user_chats.append(
                    {
                        "id": doc.id,
                        "message": data["message"],
                        "timestamp": data.get("timestamp"),
                        "chroma_id": data.get("chroma_id"),
                    }
                )

        # 타임스탬프로 정렬 (최신 순)
        user_chats.sort(
            key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min,
            reverse=True,
        )

        # 개수 제한
        history = user_chats[:limit]

        # 타임스탬프를 문자열로 변환
        for chat in history:
            if chat["timestamp"] and hasattr(chat["timestamp"], "isoformat"):
                chat["timestamp"] = chat["timestamp"].isoformat()
            elif chat["timestamp"]:
                chat["timestamp"] = str(chat["timestamp"])

        return {"user_id": user_id, "history": history, "total_found": len(user_chats)}

    except Exception as e:
        # 대안: ChromaDB에서만 조회
        try:
            print(f"Firestore 조회 실패, ChromaDB로 대체: {str(e)}")

            # ChromaDB에서 사용자 데이터 조회
            results = collection.get(where={"user_id": user_id})

            if results and results["ids"]:
                history = []
                for i, doc_id in enumerate(results["ids"]):
                    history.append(
                        {
                            "id": doc_id,
                            "message": results["documents"][i],
                            "timestamp": results["metadatas"][i].get(
                                "timestamp", "N/A"
                            ),
                            "chroma_id": doc_id,
                        }
                    )

                # 최근 순으로 제한
                history = history[-limit:] if len(history) > limit else history
                history.reverse()  # 최신 순으로

                return {
                    "user_id": user_id,
                    "history": history,
                    "source": "ChromaDB (Firestore 대체)",
                    "total_found": len(history),
                }
            else:
                return {
                    "user_id": user_id,
                    "history": [],
                    "message": "저장된 대화가 없습니다.",
                }

        except Exception as chroma_error:
            raise HTTPException(
                status_code=500,
                detail=f"기록 조회 실패: Firestore({str(e)}) ChromaDB({str(chroma_error)})",
            )
