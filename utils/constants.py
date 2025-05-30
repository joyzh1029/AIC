# constants.py
# 공통 상수 정의 파일

from datetime import datetime

GNEWS_URL = "https://gnews.io/api/v4/top-headlines"
DEFAULT_PARAMS = {"lang": "ko", "country": "kr", "max": 20}
CACHE_FILE = "news_cache.json"
TODAY_STR = datetime.now().strftime("%Y-%m-%d")

CATEGORY_MAP = {
    "정치": "politics", "경제": "business", "금융": "business",
    "과학": "science", "기술": "technology", "스포츠": "sports",
    "연예": "entertainment", "건강": "health", "사회": "general"
}