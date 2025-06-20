# test.py
import torch

def check_cuda_available():
    print("🔍 CUDA 사용 여부 확인 중...")
    if torch.cuda.is_available():
        print("✅ CUDA 사용 가능")
        print(f" - 장치 수: {torch.cuda.device_count()}")
        print(f" - 현재 장치: {torch.cuda.current_device()}")
        print(f" - 장치 이름: {torch.cuda.get_device_name(torch.cuda.current_device())}")
    else:
        print("❌ CUDA 사용 불가 (GPU 사용 불가 또는 드라이버 문제)")

if __name__ == "__main__":
    check_cuda_available()
