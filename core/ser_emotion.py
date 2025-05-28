from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import torch
import torchaudio

model_name = "jungjongho/wav2vec2-xlsr-korean-speech-emotion-recognition"
model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

def analyze_voice_emotion_korean(file_path):
    speech_array, sampling_rate = torchaudio.load(file_path)
    inputs = extractor(speech_array.squeeze(), sampling_rate=sampling_rate, return_tensors="pt", padding=True)

    with torch.no_grad():
        logits = model(**inputs.to(device)).logits
        predicted = torch.argmax(logits, dim=-1)

    label = model.config.id2label[predicted.item()]
    return label
