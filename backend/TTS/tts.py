import requests

group_id = "请填写您的group_id"
api_key = "请填写您的api_key"

url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
  "model": "speech-02-hd",
  "text": "안녕, 오늘 만나서 반가워! 나는 너의 AI 친구미나야, 어떻게지내고있어?",
  "timber_weights": [
    {
      "voice_id": "Boyan_new_platform",
      "weight": 100
    }
  ],
  "voice_setting": {
    "voice_id": "",
    "speed": 1,
    "pitch": 0,
    "vol": 1,
    "latex_read": False
  },
  "audio_setting": {
    "sample_rate": 32000,
    "bitrate": 128000,
    "format": "mp3"
  },
  "language_boost": "Korean"
}

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(response.text)
