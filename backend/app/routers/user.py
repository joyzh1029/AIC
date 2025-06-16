from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Query

from db_utils import db, bucket

# ✨ 두 개의 라우터 생성 - 기존 경로와 새 경로 모두 지원
router = APIRouter(tags=["user"])
api_router = APIRouter(prefix="/api", tags=["user"])


# ==================== 사용자 관련 엔드포인트 ====================
user_id = ("abc123",)
email = ("user@email.com",)
nickname = ("홍길동",)
profile_image_url = ("https://example.com/profile.png",)
auth_provider = "google"


# 기존 경로용 엔드포인트 (프론트엔드 호환성)
@router.post("/save_ai_friend_image/")  # /save_ai_friend_image/
@api_router.post("/save_ai_friend_image/")  # /api/save_ai_friend_image/
async def save_ai_friend_image(
    user_id: str = Form(...), name: str = Form(...), image: UploadFile = File(...)
):

    image_bytes = await image.read()
    blob_name = f"generated_images/{user_id}.png"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type="image/png")
    blob.make_public()

    image_url = blob.public_url
    print("✅ Firebase 이미지 URL:", image_url)
    print("user_id:", user_id)
    print("name:", name)
    user_data = {
        "user_id": user_id,
        "email": email,
        "nickname": name,
        "created_at": datetime.utcnow().isoformat(),
        "last_login": datetime.utcnow().isoformat(),
        "profile_image_url": image_url,
        "auth_provider": auth_provider,
        "ai_friends": [],
        "settings": {"theme": "light", "language": "ko"},
        "usage_stats": {"total_chats": 0, "last_chat_at": None},
    }

    db.collection("users").document(user_id).set(user_data)


@router.get("/get_user_data")  # /get_user_data (기존 경로)
@api_router.get("/get_user_data")  # /api/get_user_data (새 경로)
async def get_user_data(user_id: str = Query(...)):
    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        print("사용자 데이터 조회 성공:", doc.id)
        print("사용자 데이터:", doc.to_dict())
        return doc.to_dict()
    else:
        return {"error": "User not found"}
