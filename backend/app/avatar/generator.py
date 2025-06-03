import google.generativeai as genai
from openai import OpenAI
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# ========== API 설정 ========== #
# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# OpenAI 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG = os.getenv("ORGANIZATION_ID")
openai_client = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG)

def extract_features(image_path: str) -> str:
    """
    이미지에서 인물 특징 추출
    :param image_path: 이미지 파일 경로
    :return: 특징 설명 텍스트
    """
    try:
        # 이미지 읽기
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 이미지 파트 구성
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_bytes
        }

        # 특징 추출 프롬프트
        prompt = """사진 속 인물 특징을 상세히 분석하세요:
- 성별 및 연령대
- 헤어스타일, 머리색 및 얼굴 특징
- 의상 스타일(색상, 패턴 등 세부사항)
- 액세서리 특징(안경, 주얼리 등)
- 표정과 자세 특성"""

        # Gemini 모델 호출
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, image_part])

        return response.text

    except Exception as e:
        raise RuntimeError(f"특징 추출 실패: {str(e)}")


def generate_avatar(feature_desc: str, output_path: str) -> str:
    """OpenAI를 사용해 아바타 생성"""
    try:
        # 동적 프롬프트 생성
        dynamic_prompt = f"""
다음 인물 특징을 기반으로 3D 큐판 캐릭터를 생성하세요:
{feature_desc}

생성 요구사항:
1. 특징 식별성 유지
2. 팝마트 블라인드 박스 스타일 적용
3. 1:2 두신비율의 귀여운 프로포션
4. 반투명 배경 프레임 추가
5. 캐릭터 일부가 프레임 밖으로 나오도록
"""

        # GPT-Image-1 API 호출
        response = openai_client.images.generate(
            model="gpt-image-1",
            prompt=dynamic_prompt,
            background="opaque",
            n=1,
            quality="high",
            size="1024x1536",
            output_format="png",
            moderation="auto"
        )
        
        # 이미지 저장
        image_data = base64.b64decode(response.data[0].b64_json)
        with open(output_path, "wb") as f:
            f.write(image_data)
            
        return output_path

    except Exception as e:
        raise RuntimeError(f"생성 실패: {str(e)}")

def test_avatar_generation(test_image: str, output_path: str):
    """테스트용 함수"""
    try:
        # 특징 추출
        print(f"\n🔍 분석 중...")
        features = extract_features(test_image)
        print("✅ 특징 추출 완료")

        # 아바타 생성
        print("🎨 아바타 생성 중...")
        generate_avatar(features, output_path)
        print(f"💾 저장 완료: {output_path}")

    except Exception as e:
        print(f"❌ 처리 실패: {str(e)}")
