import requests
from utils.constants import GNEWS_URL, DEFAULT_PARAMS, CATEGORY_MAP
from config import GNEWS_API_KEY

def fetch_news(**kwargs):
    params = {**DEFAULT_PARAMS, **kwargs, "apikey": GNEWS_API_KEY}
    return requests.get(GNEWS_URL, params=params).json().get("articles", [])

def detect_category(query):
    return next((v for k, v in CATEGORY_MAP.items() if k in query), "general")