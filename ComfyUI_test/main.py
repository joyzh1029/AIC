from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from ComfyUI_test.workflow_runner import run_workflow
import os
from pathlib import Path

app = FastAPI(title="ComfyUI Image Generator", version="1.0.0")

# 정적 파일 서비스를 위한 디렉토리 설정
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

# 정적 파일 마운트 (생성된 이미지들을 웹에서 볼 수 있도록)
app.mount("/static", StaticFiles(directory=str(output_dir)), name="static")

@app.get("/") #연결
def root():
    return {
        "message": "ComfyUI 연결 성공!",
        "endpoints": {
            "generate": "/generate-image/",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health") #서버 상태
def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "service": "ComfyUI Image Generator"}

@app.post("/generate-image/") #이미지 생성 API (포스트)
async def generate_image():
    """이미지 생성 API"""
    try:
        # 워크플로우 실행
        output_path = run_workflow()
        
        # 파일 존재 확인
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="생성된 이미지를 찾을 수 없습니다")
        
        # 파일 이름 추출
        filename = os.path.basename(output_path)
        
        # 이미지 파일 반환
        return FileResponse(
            path=output_path,
            media_type="image/png",
            filename=filename,
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {str(e)}")

@app.get("/generate-image/") #이미지 생성 (get)방식
async def generate_image_get():
    """GET 방식으로도 이미지 생성 가능"""
    return await generate_image()

@app.get("/latest-image/") #최근에 생성된 이미지 반환
def get_latest_image():
    """가장 최근에 생성된 이미지 반환"""
    try:
        output_dir = Path(__file__).parent / "output"
        
        if not output_dir.exists():
            raise HTTPException(status_code=404, detail="출력 디렉토리가 없습니다")
        
        # 가장 최근 파일 찾기
        image_files = list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
        
        if not image_files:
            raise HTTPException(status_code=404, detail="생성된 이미지가 없습니다")
        
        latest_file = max(image_files, key=os.path.getctime)
        
        return FileResponse(
            path=str(latest_file),
            media_type="image/png",
            filename=latest_file.name,
            headers={
                "Content-Disposition": f"inline; filename={latest_file.name}",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images/") #생성된 모든 이미지 목록 확인
def list_images():
    """생성된 모든 이미지 목록 반환"""
    try:
        output_dir = Path(__file__).parent / "output"
        
        if not output_dir.exists():
            return {"images": [], "count": 0}
        
        image_files = []
        for ext in ["*.png", "*.jpg", "*.jpeg"]:
            image_files.extend(output_dir.glob(ext))
        
        images_info = []
        for img_file in sorted(image_files, key=os.path.getctime, reverse=True):
            stat = img_file.stat()
            images_info.append({
                "filename": img_file.name,
                "url": f"/static/{img_file.name}",
                "size": stat.st_size,
                "created": stat.st_ctime
            })
        
        return {
            "images": images_info,
            "count": len(images_info)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)