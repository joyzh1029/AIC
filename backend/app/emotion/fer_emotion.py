import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from app.emotion.models.resnet_lstm import ResNet50, LSTMPyTorch

DICT_EMO = {0: 'Neutral', 1: 'Happiness', 2: 'Sadness', 3: 'Surprise', 4: 'Fear', 5: 'Disgust', 6: 'Anger'}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 모델 로드
import os

# 현재 파일이 있는 디렉토리의 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))
# 모델 파일의 절대 경로 생성
static_model_path = os.path.join(current_dir, 'models', 'FER_static_ResNet50_AffectNet.pt')
dynamic_model_path = os.path.join(current_dir, 'models', 'FER_dinamic_LSTM_Aff-Wild2.pt')

pth_backbone_model = ResNet50().to(device)
pth_backbone_model.load_state_dict(torch.load(static_model_path, map_location=device))
pth_backbone_model.eval()

pth_LSTM_model = LSTMPyTorch().to(device)
pth_LSTM_model.load_state_dict(torch.load(dynamic_model_path, map_location=device))
pth_LSTM_model.eval()

# 전처리
class PreprocessInput(torch.nn.Module):
    def forward(self, x):
        x = x.to(torch.float32)
        x = torch.flip(x, dims=(0,))
        x[0, :, :] -= 91.4953
        x[1, :, :] -= 103.8827
        x[2, :, :] -= 131.0912
        return x

transform = transforms.Compose([
    transforms.PILToTensor(),
    PreprocessInput()
])

lstm_features = []

def analyze_facial_expression(image: Image.Image) -> str:
    global lstm_features

    if image.mode == "RGBA":
        image = image.convert("RGB")
        
    image = image.resize((224, 224), Image.Resampling.NEAREST)
    input_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        features = torch.relu(pth_backbone_model.extract_features(input_tensor)).cpu().numpy()

    if not lstm_features:
        lstm_features = [features] * 10
    else:
        lstm_features = lstm_features[1:] + [features]

    lstm_input = torch.from_numpy(np.vstack(lstm_features)).unsqueeze(0).to(device)

    with torch.no_grad():
        output = pth_LSTM_model(lstm_input).cpu().numpy()

    pred = np.argmax(output)
    return DICT_EMO[pred]
