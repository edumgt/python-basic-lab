import cv2
import os
from rembg import remove
from PIL import Image

# 1. 프레임 추출
video = cv2.VideoCapture("1.mp4")
os.makedirs("frames", exist_ok=True)
frame_count = 0

while True:
    ret, frame = video.read()
    if not ret:
        break
    cv2.imwrite(f"frames/frame_{frame_count:05d}.png", frame)
    frame_count += 1

video.release()

# 2. 자막 위치 영역을 마스킹 후 제거 (예: 하단 중앙 영역만 제거)
def inpaint_subtitles(img_path):
    img = cv2.imread(img_path)
    mask = img.copy()
    h, w, _ = img.shape

    # 자막 위치 추정 (하단 15% 가운데 60%)
    subtitle_area = (int(w*0.2), int(h*0.85), int(w*0.8), int(h*0.98))
    cv2.rectangle(mask, (subtitle_area[0], subtitle_area[1]), (subtitle_area[2], subtitle_area[3]), (255, 255, 255), -1)

    # 텍스트 제거 (inpainting)
    inpainted = cv2.inpaint(img, cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY), 3, cv2.INPAINT_TELEA)
    return inpainted

# 3. 인페인팅 적용
os.makedirs("cleaned_frames", exist_ok=True)
for i in range(frame_count):
    path = f"frames/frame_{i:05d}.png"
    cleaned = inpaint_subtitles(path)
    cv2.imwrite(f"cleaned_frames/frame_{i:05d}.png", cleaned)

# 4. 프레임 → 동영상 조립
os.system("ffmpeg -framerate 30 -i cleaned_frames/frame_%05d.png -c:v libx264 -pix_fmt yuv420p output_cleaned.mp4")
