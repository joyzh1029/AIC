import requests
import os
from dotenv import load_dotenv
load_dotenv()
# ⚙️ Kakao REST API 키
KAKAO_API_KEY = os.getenv("kakao_API_KEY")

# 🧠 주소 자동 보정 함수 (선택사항)
def preprocess_address(address: str) -> str:
    if "서울" in address and "시" not in address:
        return "서울특별시 " + address
    return address

# 📍 카카오 주소 → 좌표 변환
def get_coordinates_kakao(address: str):
    address = preprocess_address(address)
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # 👉 디버깅: 응답 내용 출력
    if not data.get("documents"):
        print("[DEBUG] 주소 검색 실패: ", response.text)

    documents = data.get("documents", [])
    if not documents:
        return None, None
    lat = float(documents[0]["y"])
    lon = float(documents[0]["x"])
    return lat, lon

# 날씨 코드 해석
def interpret_weather_code(code: int) -> str:
    if code == 0:
        return "맑음"
    elif code == 1:
        return "대체로 맑음"
    elif code == 2:
        return "부분적으로 흐림"
    elif code == 3:
        return "흐림"
    elif code in [45, 48]:
        return "안개"
    elif 51 <= code <= 55:
        return "이슬비"
    elif 61 <= code <= 65:
        return "비"
    elif 66 <= code <= 67:
        return "어는 비"
    elif 71 <= code <= 75:
        return "눈"
    elif 80 <= code <= 82:
        return "소나기"
    elif code == 95:
        return "천둥 번개"
    else:
        return "알 수 없음"

# 날씨 정보 가져오기
def get_weather(address: str) -> str:
    lat, lon = get_coordinates_kakao(address)
    if lat is None:
        return f"주소 '{address}'의 위치를 찾을 수 없습니다."

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
    weather_desc = interpret_weather_code(weather_code)

    return f"{address}의 현재 날씨는 '{weather_desc}'이며, 기온은 {temperature}°C, 풍속은 {windspeed} km/h입니다."

# ▶️ 실행
if __name__ == "__main__":
    address = input("주소를 입력하세요 (예: 서울 신림동): ")
    print(get_weather(address))
