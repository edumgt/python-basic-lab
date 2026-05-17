import torch
print("CUDA Available:", torch.cuda.is_available())
print("GPU 개수:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("GPU 이름:", torch.cuda.get_device_name(0))
