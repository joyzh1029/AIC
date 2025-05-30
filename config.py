# .env 파일에서 API 키를 안전하게 불러옴
# 프로젝트 전체에서 필요한 import를 공유합니다.

import os
from dotenv import load_dotenv

load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")