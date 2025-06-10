import google.generativeai as genai
from openai import OpenAI
import os
import base64
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import logging

load_dotenv()

# ========== 성능 모니터링 클래스 ========== #
@dataclass
class PerformanceMetrics:
    """성능 지표를 추적하는 데이터 클래스"""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    cost_estimate: Optional[float] = None
    image_size: Optional[str] = None
    model_used: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def finish(self, success: bool = True, error_message: str = None):
        """작업 완료 시 호출"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message

class PerformanceLogger:
    """성능 로깅 및 분석 클래스"""
    
    def __init__(self, log_file: str = "avatar_performance.json"):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        self.session_metrics = []
        
    def start_operation(self, operation_name: str, model_used: str = None) -> PerformanceMetrics:
        """작업 시작 추적"""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            model_used=model_used
        )
        self.logger.info(f"🚀 Starting {operation_name} with model: {model_used}")
        return metrics
    
    def log_token_usage(self, metrics: PerformanceMetrics, token_data: Dict[str, Any]):
        """토큰 사용량 로깅"""
        if token_data:
            metrics.token_usage = token_data
            self.logger.info(f"📊 Token Usage for {metrics.operation_name}:")
            for key, value in token_data.items():
                self.logger.info(f"   {key}: {value}")
    
    def estimate_cost(self, metrics: PerformanceMetrics):
        """비용 추정 (OpenAI 기준)"""
        if not metrics.token_usage and not metrics.model_used:
            return
            
        # OpenAI 가격 (2025년 기준, USD)
        pricing = {
            "gpt-4-vision-preview": {
                "input": 0.01 / 1000,  # per 1K tokens
                "output": 0.03 / 1000
            },
            "gpt-image-1": {
                "1024x1024": 0.040,
                "1024x1536": 0.060,
                "1024x1792": 0.080,
                "1792x1024": 0.080,
                "1536x1024": 0.060
            }
        }
        
        cost = 0.0
        if metrics.model_used and "gpt-image" in metrics.model_used.lower():
            # GPT-Image-1 이미지 생성 비용
            if metrics.image_size:
                size_key = metrics.image_size
                if size_key in pricing["gpt-image-1"]:
                    cost = pricing["gpt-image-1"][size_key]
                else:
                    # 기본 크기로 추정
                    cost = pricing["gpt-image-1"].get("1024x1536", 0.060)
        elif metrics.token_usage:
            # GPT 모델 토큰 비용 (Gemini 등)
            input_tokens = metrics.token_usage.get("prompt_tokens", 0) or metrics.token_usage.get("estimated_input_tokens", 0)
            output_tokens = metrics.token_usage.get("completion_tokens", 0) or metrics.token_usage.get("estimated_output_tokens", 0)
            
            model_pricing = pricing.get("gpt-4-vision-preview", {})
            cost = (input_tokens * model_pricing.get("input", 0) + 
                   output_tokens * model_pricing.get("output", 0))
        
        metrics.cost_estimate = cost
        self.logger.info(f"💰 Estimated cost for {metrics.operation_name}: ${cost:.6f}")
    
    def finish_operation(self, metrics: PerformanceMetrics, success: bool = True, error_message: str = None):
        """작업 완료 및 로깅"""
        metrics.finish(success, error_message)
        
        # 성능 정보 로깅
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.logger.info(f"{status} - {metrics.operation_name}")
        self.logger.info(f"⏱️  Duration: {metrics.duration:.3f} seconds")
        
        if metrics.cost_estimate:
            self.logger.info(f"💰 Cost: ${metrics.cost_estimate:.6f}")
        
        if error_message:
            self.logger.error(f"🚨 Error: {error_message}")
            
        # 세션 메트릭스에 추가
        self.session_metrics.append(metrics)
        
        # 파일에 저장
        self._save_to_file(metrics)
    
    def _save_to_file(self, metrics: PerformanceMetrics):
        """메트릭스를 JSON 파일에 저장"""
        try:
            # 기존 데이터 로드
            data = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # 새 데이터 추가
            data.append(asdict(metrics))
            
            # 파일에 저장
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save metrics to file: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """현재 세션의 성능 요약"""
        if not self.session_metrics:
            return {}
        
        total_duration = sum(m.duration for m in self.session_metrics if m.duration)
        total_cost = sum(m.cost_estimate for m in self.session_metrics if m.cost_estimate)
        success_rate = sum(1 for m in self.session_metrics if m.success) / len(self.session_metrics)
        
        summary = {
            "total_operations": len(self.session_metrics),
            "total_duration": total_duration,
            "total_cost": total_cost,
            "success_rate": success_rate,
            "operations": [
                {
                    "name": m.operation_name,
                    "duration": m.duration,
                    "cost": m.cost_estimate,
                    "success": m.success
                }
                for m in self.session_metrics
            ]
        }
        
        return summary
    
    def print_session_summary(self):
        """세션 요약 출력"""
        summary = self.get_session_summary()
        if not summary:
            self.logger.info("No operations recorded in this session.")
            return
        
        self.logger.info("\n" + "="*50)
        self.logger.info("📈 SESSION PERFORMANCE SUMMARY")
        self.logger.info("="*50)
        self.logger.info(f"Total Operations: {summary['total_operations']}")
        self.logger.info(f"Total Duration: {summary['total_duration']:.3f} seconds")
        self.logger.info(f"Total Cost: ${summary['total_cost']:.6f}")
        self.logger.info(f"Success Rate: {summary['success_rate']:.1%}")
        self.logger.info("\n📋 Operation Details:")
        
        for op in summary['operations']:
            status = "✅" if op['success'] else "❌"
            self.logger.info(f"  {status} {op['name']}: {op['duration']:.3f}s, ${op['cost']:.6f}")
        
        self.logger.info("="*50)

# ========== 전역 성능 로거 인스턴스 ========== #
perf_logger = PerformanceLogger()

# ========== API 설정 ========== #
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
openai_client = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)

def extract_features(image_path: str) -> str:
    """이미지에서 인물 특징 추출 (성능 모니터링 포함)"""
    logger = logging.getLogger(__name__)
    logger.info(f"Extracting features from image: {image_path}")
    
    # 성능 추적 시작
    metrics = perf_logger.start_operation("Feature Extraction", "gemini-1.5-flash")
    
    try:
        # 이미지 읽기
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        logger.info(f"Successfully read image file: {len(image_bytes)} bytes")

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
        
        logger.info("Using feature extraction prompt")
        logger.info(f"GOOGLE_API_KEY available: {GOOGLE_API_KEY is not None}")
        logger.info("Calling Gemini model for feature extraction...")
        
        # API 호출 시간 측정
        api_start_time = time.time()
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, image_part])
        api_duration = time.time() - api_start_time
        
        logger.info(f"⚡ Gemini API call duration: {api_duration:.3f} seconds")
        
        # 토큰 사용량 정보 (Gemini는 현재 토큰 정보를 직접 제공하지 않음)
        # 대략적인 추정치 로깅
        estimated_input_tokens = len(prompt.split()) * 1.3  # 대략적 추정
        estimated_output_tokens = len(response.text.split()) * 1.3
        
        token_info = {
            "estimated_input_tokens": int(estimated_input_tokens),
            "estimated_output_tokens": int(estimated_output_tokens),
            "api_call_duration": api_duration
        }
        
        perf_logger.log_token_usage(metrics, token_info)
        
        # 결과 로깅
        extracted_features = response.text
        logger.info("Feature extraction successful")
        logger.info(f"Extracted features length: {len(extracted_features)} characters")
        
        # 성공적으로 완료
        perf_logger.finish_operation(metrics, success=True)
        
        return extracted_features

    except Exception as e:
        error_msg = f"특징 추출 실패: {str(e)}"
        logger.error(f"Feature extraction failed: {str(e)}", exc_info=True)
        perf_logger.finish_operation(metrics, success=False, error_message=error_msg)
        raise RuntimeError(error_msg)


def generate_avatar(feature_desc: str, output_path: str) -> str:
    """OpenAI를 사용해 아바타 생성 (성능 모니터링 포함)"""
    logger = logging.getLogger(__name__)
    
    # 성능 추적 시작
    metrics = perf_logger.start_operation("Avatar Generation", "gpt-image-1")
    metrics.image_size = "1024x1536"  # 설정된 이미지 크기
    
    try:
        # 입력된 특징 로깅
        logger.info("=== RECEIVED FEATURE DESCRIPTION ===")
        logger.info(f"\n{feature_desc}")
        logger.info("=== END OF FEATURE DESCRIPTION ===")
        
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

        # 생성된 프롬프트 로깅
        logger.info("=== GENERATED PROMPT FOR AVATAR ===")
        logger.info(f"Prompt length: {len(dynamic_prompt)} characters")
        logger.info(f"Estimated tokens: ~{len(dynamic_prompt.split()) * 1.3:.0f}")
        logger.info("=== END OF PROMPT ===")
        
        # 환경 변수 확인 로깅
        logger.info(f"OPENAI_API_KEY available: {OPENAI_API_KEY is not None}")
        logger.info(f"OPENAI_ORG_ID available: {OPENAI_ORG_ID is not None}")
        
        # OpenAI API가 없는 경우 예제 이미지 사용
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found. Using example avatar instead.")
            frontend_example_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                             "frontend", "public", "example_avatar_profile.png")
            
            if os.path.exists(frontend_example_path):
                import shutil
                shutil.copy(frontend_example_path, output_path)
                logger.info(f"Example avatar copied from {frontend_example_path} to {output_path}")
            else:
                logger.warning(f"Example avatar not found at {frontend_example_path}, creating empty file")
                with open(output_path, "wb") as f:
                    f.write(b"")
            
            # 성능 메트릭스 완료 (예제 이미지 사용)
            perf_logger.finish_operation(metrics, success=True)
            return output_path
        
        # OpenAI API 호출
        logger.info("🎨 Calling OpenAI GPT-Image-1 API to generate avatar...")
        
        # API 호출 시간 측정
        api_start_time = time.time()
        
        try:
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
            
            api_duration = time.time() - api_start_time
            logger.info(f"⚡ OpenAI GPT-Image-1 API call duration: {api_duration:.3f} seconds")
            
            # GPT-Image-1 비용 정보 로깅
            cost_info = {
                "model": "gpt-image-1",
                "size": "1024x1536",
                "quality": "high",
                "api_call_duration": api_duration,
                "images_generated": 1,
                "output_format": "png"
            }
            
            perf_logger.log_token_usage(metrics, cost_info)
            perf_logger.estimate_cost(metrics)
            
            # 이미지 저장
            image_data = base64.b64decode(response.data[0].b64_json)
            
            # 파일 쓰기 시간 측정
            write_start_time = time.time()
            with open(output_path, "wb") as f:
                f.write(image_data)
            write_duration = time.time() - write_start_time
            
            logger.info(f"💾 File write duration: {write_duration:.3f} seconds")
            logger.info(f"📁 Generated image size: {len(image_data)} bytes")
            logger.info("OpenAI GPT-Image-1 avatar generation successful")
            
        except Exception as api_error:
            api_duration = time.time() - api_start_time
            logger.error(f"OpenAI API error after {api_duration:.3f}s: {str(api_error)}")
            
            # API 오류 발생 시 예제 이미지 사용
            logger.warning("Falling back to example avatar due to API error")
            frontend_example_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                             "frontend", "public", "example_avatar_profile.png")
            
            if os.path.exists(frontend_example_path):
                import shutil
                shutil.copy(frontend_example_path, output_path)
                logger.info(f"Example avatar copied from {frontend_example_path} to {output_path}")
            else:
                error_msg = f"Failed to generate avatar and example avatar not found: {str(api_error)}"
                perf_logger.finish_operation(metrics, success=False, error_message=error_msg)
                raise RuntimeError(error_msg)
        
        # 이미지가 성공적으로 저장되었는지 확인
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Avatar successfully saved to {output_path} ({file_size} bytes)")
        else:
            error_msg = f"Failed to save avatar to {output_path}"
            logger.error(error_msg)
            perf_logger.finish_operation(metrics, success=False, error_message=error_msg)
            raise RuntimeError(error_msg)
        
        # 성공적으로 완료
        perf_logger.finish_operation(metrics, success=True)
        return output_path

    except Exception as e:
        error_msg = f"생성 실패: {str(e)}"
        logger.error(f"Avatar generation failed: {str(e)}", exc_info=True)
        perf_logger.finish_operation(metrics, success=False, error_message=error_msg)
        raise RuntimeError(error_msg)

def test_avatar_generation(test_image: str, output_path: str):
    """테스트용 함수 (전체 프로세스 성능 모니터링)"""
    logger = logging.getLogger(__name__)
    
    # 전체 프로세스 성능 추적
    total_metrics = perf_logger.start_operation("Complete Avatar Generation Process", "gemini+gpt-image-1")
    
    try:
        logger.info("\n" + "="*60)
        logger.info("🚀 STARTING AVATAR GENERATION PROCESS")
        logger.info("="*60)
        
        # 특징 추출
        print(f"\n🔍 분석 중...")
        features = extract_features(test_image)
        print("✅ 특징 추출 완료")

        # 아바타 생성
        print("🎨 아바타 생성 중...")
        generate_avatar(features, output_path)
        print(f"💾 저장 완료: {output_path}")
        
        # 전체 프로세스 완료
        perf_logger.finish_operation(total_metrics, success=True)
        
        # 세션 요약 출력
        perf_logger.print_session_summary()

    except Exception as e:
        error_msg = f"처리 실패: {str(e)}"
        print(f"❌ {error_msg}")
        perf_logger.finish_operation(total_metrics, success=False, error_message=error_msg)
        perf_logger.print_session_summary()
        raise

def analyze_performance_history(log_file: str = "avatar_performance.json"):
    """성능 히스토리 분석"""
    if not os.path.exists(log_file):
        print(f"로그 파일이 존재하지 않습니다: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("로그 데이터가 비어있습니다.")
            return
        
        # 작업별 성능 분석
        operations = {}
        for record in data:
            op_name = record['operation_name']
            if op_name not in operations:
                operations[op_name] = []
            operations[op_name].append(record)
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE HISTORY ANALYSIS")
        print("="*60)
        
        for op_name, records in operations.items():
            durations = [r['duration'] for r in records if r['duration']]
            costs = [r['cost_estimate'] for r in records if r['cost_estimate']]
            success_count = sum(1 for r in records if r['success'])
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)
                
                print(f"\n🔧 {op_name}:")
                print(f"   Total runs: {len(records)}")
                print(f"   Success rate: {success_count/len(records):.1%}")
                print(f"   Avg duration: {avg_duration:.3f}s")
                print(f"   Min duration: {min_duration:.3f}s")
                print(f"   Max duration: {max_duration:.3f}s")
                
                if costs:
                    avg_cost = sum(costs) / len(costs)
                    total_cost = sum(costs)
                    print(f"   Avg cost: ${avg_cost:.6f}")
                    print(f"   Total cost: ${total_cost:.6f}")
        
        print("="*60)
        
    except Exception as e:
        print(f"성능 히스토리 분석 실패: {e}")

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('avatar_generation.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 테스트 실행
    test_image_path = "test_image.jpg"
    output_avatar_path = "generated_avatar.png"
    
    if os.path.exists(test_image_path):
        test_avatar_generation(test_image_path, output_avatar_path)
    else:
        print(f"테스트 이미지가 없습니다: {test_image_path}")
    
    # 성능 히스토리 분석
    analyze_performance_history()