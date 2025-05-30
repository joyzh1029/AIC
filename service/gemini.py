# Google Gemini-2.0-Flash API를 호출 후 뉴스 요약 결과 받아옴

import requests
from config import GEMINI_API_KEY

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "topK": 1, "topP": 1}
    }
    try:
        r = requests.post(url, json=body)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "❌ Gemini API 오류"