# 감정 데이터 통합 개선 문서

## 개요

이번 개선에서는 하드코딩된 감정 데이터를 실제 감지된 감정 데이터로 교체하고, 날씨, 수면, 스트레스 등의 환경 데이터에 랜덤 생성 기능을 추가했습니다.

## 주요 수정사항

### 1. 범용 데이터 생성 모듈 생성

**파일**: `backend/app/core/data_generator.py`

새로운 기능:
- `generate_random_weather()`: 랜덤 날씨 데이터 생성 (온도 범위: -5°C에서 35°C)
- `generate_random_sleep()`: 랜덤 수면 데이터 생성 (4-10시간, 품질 평가 포함)
- `generate_random_stress()`: 랜덤 스트레스 데이터 생성 (1-10점, 등급 설명 포함)
- `generate_emotion_history()`: 실제 감지된 감정을 기반으로 히스토리 데이터 생성
- `generate_environment_context()`: 완전한 환경 컨텍스트 데이터 생성

### 2. 라우터 파일 업데이트

#### `backend/app/routers/audio.py`
- 하드코딩된 환경 데이터 제거
- 실제 감지된 음성 감정 데이터 사용
- 랜덤 생성된 환경 데이터 통합

#### `backend/app/routers/emotion.py`
- 하드코딩된 환경 데이터 제거
- 실제 감지된 얼굴과 음성 감정 데이터 사용
- 랜덤 생성된 환경 데이터 통합

#### `backend/app/routers/conversation.py`
- 하드코딩된 환경 데이터 제거
- 실제 감지된 얼굴과 음성 감정 데이터 사용
- 랜덤 생성된 환경 데이터 통합

## 감정 매핑

시스템은 다음 감정 라벨의 자동 변환을 지원합니다:

| 영어 라벨 | 한국어 라벨 |
|---------|---------|
| Neutral | 평온 |
| Happiness | 기쁨 |
| Sadness | 슬픔 |
| Anger | 분노 |
| Fear | 두려움 |
| Surprise | 놀람 |
| Disgust | 혐오 |

## 데이터 생성 예시

### 날씨 데이터
```
맑음 25°C
구름 많음 15°C
가벼운 비 18°C
눈 -2°C
```

### 수면 데이터
```
7.5시간 (매우 좋음)
6.2시간 (보통)
8.9시간 (나쁨)
```

### 스트레스 데이터
```
매우 낮음 (2/10)
보통 (5/10)
높음 (7/10)
매우 높음 (9/10)
```

### 감정 히스토리
```
입력: face_emotion="Neutral", voice_emotion="Happiness"
출력: ["평온", "기쁨", "평온"]
```

## 테스트 검증

기능을 검증하기 위한 테스트 스크립트 실행:
```bash
cd backend
python test_data_generator.py
```

## 장점

1. **실제 데이터**: 실제 감지된 감정 데이터를 사용하여 응답 정확도 향상
2. **동적 환경**: 랜덤 생성된 환경 데이터로 대화가 더 자연스러워짐
3. **코드 재사용**: 통일된 데이터 생성 모듈로 코드 중복 방지
4. **유지보수 용이성**: 데이터 생성 로직을 중앙에서 관리
5. **확장성**: 새로운 데이터 소스 추가나 생성 로직 수정이 용이

## 사용 방법

라우터 파일에서 다음을 호출하기만 하면 됩니다:
```python
from app.core.data_generator import generate_environment_context

# 완전한 환경 컨텍스트 생성
context_data = generate_environment_context(
    face_emotion=face_emotion, 
    voice_emotion=voice_emotion
)
```

시스템이 자동으로:
1. 영어 감정 라벨을 한국어로 변환
2. 실제 감정을 기반으로 합리적인 히스토리 데이터 생성
3. 랜덤 날씨, 수면, 스트레스 데이터 생성
4. 완전한 컨텍스트 딕셔너리 반환 
 