import chromadb
from sentence_transformers import SentenceTransformer
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from typing import Optional

load_dotenv()
firebase_key_path = os.getenv("FIREBASE_CREDENTIALS")

# ChromaDB 초기화
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("chat_memory")

# 임베딩 모델
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Firebase 초기화
cred = credentials.Certificate(firebase_key_path)
firebase_admin.initialize_app(
    cred, {"storageBucket": "my-ai-friend-d27f7.firebasestorage.app"}
)
db = firestore.client()
bucket = storage.bucket()

print("storage bucket:", bucket.name)


# 데이터 모델 정의
class ChatData(BaseModel):
    user_id: str
    message: str


class QueryData(BaseModel):
    user_id: str
    query: str
    limit: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.3
    include_scores: Optional[bool] = True


class ChatResponse(BaseModel):
    id: str
    message: str
    similarity_score: float
    similarity_grade: str
    timestamp: Optional[str] = None


def get_similarity_grade(score: float) -> str:
    if score >= 0.8:
        return "매우 높음"
    elif score >= 0.6:
        return "높음"
    elif score >= 0.4:
        return "보통"
    elif score >= 0.2:
        return "낮음"
    else:
        return "매우 낮음"


def normalize_similarity_score(distance: float) -> float:
    return max(0, 1 - (distance / 2))
    # ChromaDB의 거리 값을 0-1 사이의 유사도 점수로 변환
    # 코사인 거리를 유사도로 변환 (0에 가까울수록 유사함)
    # 거리가 0이면 유사도 1, 거리가 2면 유사도 0
