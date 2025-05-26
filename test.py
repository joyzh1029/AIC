import os
import requests
from langchain.agents import initialize_agent, Tool
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

# Gemini API 설정
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# 🌐 위치 정보 가져오기 함수 (Open-Meteo의 geocoding API 사용)
def get_coordinates(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "ko", "format": "json"}
    response = requests.get(url, params=params)
    data = response.json()
    results = data.get("results", [])
    if not results:
        return None, None
    lat = results[0]["latitude"]
    lon = results[0]["longitude"]
    return lat, lon

# 🌦️ 날씨 정보 가져오기
def get_weather(city: str) -> str:
    lat, lon = get_coordinates(city)
    if lat is None:
        return f"도시 '{city}'의 위치를 찾을 수 없습니다."
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "timezone": "Asia/Seoul"
    }
    response = requests.get(url, params=params)
    data = response.json()
    weather = data.get("current_weather", {})
    temperature = weather.get("temperature")
    windspeed = weather.get("windspeed")
    weather_code = weather.get("weathercode")

    return f"{city}의 현재 기온은 {temperature}°C이고, 풍속은 {windspeed} km/h입니다. (날씨 코드: {weather_code})"

# LangChain 툴로 등록 (옵션)
weather_tool = Tool(
    name="GetWeather",
    func=get_weather,
    description="입력한 도시의 현재 날씨를 알려줍니다."
)

# 🌟 사용자 입력
city = input("도시명을 입력하세요: ")

# 🧠 Gemini 응답 (단순 호출, LangChain과 연동하려면 추가 로직 필요)
response = get_weather(city)
print(response)
