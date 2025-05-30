# 뉴스 캐싱 모듈 (파일 기반) - 캐싱 처리 및 로딩 기능
# 뉴스 데이터를 파일에 저장하고 불러오는 기능을 제공

import json
from pathlib import Path
from utils.constants import CACHE_FILE, TODAY_STR

def load_cache():
    if not Path(CACHE_FILE).exists():
        return None
    data = json.loads(Path(CACHE_FILE).read_text(encoding="utf-8"))
    return data["articles"] if data.get("date") == TODAY_STR else None

def save_cache(articles):
    Path(CACHE_FILE).write_text(
        json.dumps({"date": TODAY_STR, "articles": articles}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )