import cv2
import os
import torch
import ffmpeg
import numpy as np

from PIL import ImageFont, ImageDraw, Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from gtts import gTTS
from datetime import datetime

# === 설정 ===
video_path = "record_20250607_125847.mp4"
output_video = f"captioned_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
temp_audio = "temp_audio.mp3"
temp_video = "temp_video.mp4"
caption_font_path = "malgun.ttf"  # Windows 한글 폰트 경로 (필요시 변경)
frame_interval = 2  # 초마다 한 장면 설명

# === BLIP 모델 로드
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to("cuda" if torch.cuda.is_available() else "cpu")

# === 프레임 캡처 및 설명 생성
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_gap = int(fps * frame_interval)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(temp_video, fourcc, fps, (w, h))

font = ImageFont.truetype(caption_font_path, 32)
captions = []
frames = []
count = 0
current_caption = ""

print("📽️ 장면 분석 및 자막 생성 중...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if count % frame_gap == 0:
        # 새로운 설명 생성
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inputs = processor(images=rgb, return_tensors="pt").to(model.device)
        out_ids = model.generate(**inputs)
        caption_en = processor.decode(out_ids[0], skip_special_tokens=True)
        current_caption = f"장면 설명: {caption_en}"  # 나중에 번역 API 넣어도 됨
        captions.append(current_caption)

    # 자막 입히기
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text((50, h - 80), current_caption, font=font, fill=(255, 255, 255, 0))
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    out.write(frame)

    count += 1

cap.release()
out.release()

# === 전체 설명 합치기 + 음성 생성 (한국어)
summary = ". ".join(set(captions)).replace("장면 설명:", "").strip() + "."
tts = gTTS(summary, lang="ko")
tts.save(temp_audio)
print(f"🗣️ 생성된 음성 텍스트: {summary}")

# === 영상 + 음성 병합
ffmpeg.input(temp_video).output(temp_audio, output_video, vcodec='copy', acodec='aac', shortest=None).run()

# === 정리
os.remove(temp_video)
os.remove(temp_audio)
print(f"✅ 완료: {output_video}")
