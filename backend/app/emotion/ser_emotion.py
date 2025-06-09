# import subprocess
# import os
# import torch
# import torchaudio
# import matplotlib.pyplot as plt
# from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor

# # 모델 불러오기
# model_name = "jungjongho/wav2vec2-xlsr-korean-speech-emotion-recognition"
# model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
# extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# model.to(device)
# model.eval()

# def convert_webm_to_wav(input_path, output_path):
#     command = [
#         "ffmpeg", "-y", "-i", input_path, "-ar", "16000", output_path
#     ]
#     subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# def analyze_voice_emotion_korean(file_path: str) -> str:
#     wav_path = "converted_temp.wav"
#     convert_webm_to_wav(file_path, wav_path)

#     # WAV 로딩
#     speech_array, sampling_rate = torchaudio.load(wav_path)
#     print("🎧 [INFO] Sampling rate:", sampling_rate)
#     print("🎧 [INFO] Wave shape:", speech_array.shape)
#     print("🎧 [INFO] 첫 10개 샘플:", speech_array[0][:10])

#     # waveform 시각화
#     plt.figure(figsize=(10, 3))
#     plt.plot(speech_array[0].numpy())
#     plt.title("📈 Waveform (Debug)")
#     plt.savefig("waveform_debug.png")
#     plt.close()

#     # 모델 입력 준비
#     inputs = extractor(
#         speech_array.squeeze(), 
#         sampling_rate=sampling_rate, 
#         return_tensors="pt", 
#         padding=True
#     )
#     inputs = inputs.to(device)

#     # 추론
#     with torch.no_grad():
#         logits = model(**inputs).logits
#         predicted = torch.argmax(logits, dim=-1)

#     print("📊 [LOGITS]", logits.cpu().numpy())
#     print("🔎 [PREDICTED]", predicted.item())

#     label = model.config.id2label[predicted.item()]

#     # 청소
#     if os.path.exists(wav_path):
#         os.remove(wav_path)

#     return label

import subprocess
import os
import torchaudio
import matplotlib.pyplot as plt

# 1. 모델 로드
from funasr import AutoModel

# ✅ 정확한 모델 경로로 수정
model_dir = "FunAudioLLM/SenseVoiceSmall"


model = AutoModel(
    model=model_dir,
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
    device="cuda:0",
    hub="hf",
)

print("🧠 [INFO] sensevoice_small 모델 로딩 완료")

# 2. webm → wav 변환
def convert_webm_to_wav(input_path, output_path):
    command = [
        "ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 3. 감정 분석 함수
def analyze_voice_emotion_korean(file_path: str) -> str:
    wav_path = "converted_temp.wav"
    convert_webm_to_wav(file_path, wav_path)

    # 디버깅용 waveform 시각화
    waveform, sr = torchaudio.load(wav_path)
    print("🎧 [INFO] Sampling rate:", sr)
    plt.figure(figsize=(10, 3))
    plt.plot(waveform[0].numpy())
    plt.title("📈 Waveform (Debug)")
    plt.savefig("waveform_debug.png")
    plt.close()

    # 4. FunASR 모델로 추론
    result = model.generate(input=wav_path)
    print("🔍 [MODEL RESULT]", result)

    # 5. 리스트 반환 대응
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
    elif not isinstance(result, dict):
        result = {}

    # 6. 감정 결과 추출
    emotion = result.get("emotion", "unknown")
    # env_text = result.get("text", "unknown")  # 사용하지 않을 경우 생략 가능

    # 7. 임시 파일 정리
    if os.path.exists(wav_path):
        os.remove(wav_path)

    return emotion  # 또는 return emotion, env_text