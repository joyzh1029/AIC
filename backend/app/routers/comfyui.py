from fastapi import APIRouter, UploadFile, File
import base64
import io

from comfyui_utils import (
    load_workflow,
    encode_image_to_base64,
    update_workflow_with_image,
    queue_prompt,
    get_image,
)

# 프론트엔드가 /wanna-image/로 호출하므로 prefix 제거
router = APIRouter(tags=["comfyui"])


# ==================== ComfyUI 이미지 처리 ====================
@router.post("/wanna-image/")  # prefix 없이 /wanna-image/
async def upload_image(image: UploadFile = File(...)):
    print(">>> /api/wanna-image/ 요청 도착!")
    try:
        image_bytes = await image.read()
        base64_image = encode_image_to_base64(image_bytes)
        workflow = load_workflow()
        workflow = update_workflow_with_image(workflow, base64_image)
        response = queue_prompt(workflow)
        prompt_id = response["prompt_id"]

        image_result = get_image(prompt_id)

        if image_result:
            buffered = io.BytesIO()
            image_result.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return {"base64_image": img_base64}
        else:
            return {"error": "ComfyUI로부터 이미지를 받지 못했습니다."}

    except Exception as e:
        return {"error": f"이미지 처리 중 오류 발생: {str(e)}"}
