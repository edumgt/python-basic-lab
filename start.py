import cv2
import numpy as np
import threading
import time
import os

from pynput import keyboard
from mss import mss
from PIL import Image
from gtts import gTTS
import subprocess
from datetime import datetime

# === 설정 ===
FPS = 15
RECORDING = False
RESOLUTION = (720, 1080)
VIDEO_NAME = f"record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

frames = []

# === 화면 녹화 ===
def record_screen():
    global RECORDING, frames
    sct = mss()
    monitor = sct.monitors[1]
    print("🎥 녹화 시작")

    while RECORDING:
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        img = img.crop(center_crop(sct_img.width, sct_img.height, RESOLUTION))
        frame = cv2.cvtColor(np.array(img.resize(RESOLUTION)), cv2.COLOR_RGB2BGR)
        frames.append(frame)
        time.sleep(1 / FPS)

    print("🛑 녹화 종료")

# === 중앙 크롭 계산 ===
def center_crop(width, height, target_res):
    tw, th = target_res
    x1 = (width - tw) // 2
    y1 = (height - th) // 2
    return (x1, y1, x1 + tw, y1 + th)

# === mp4 저장 ===
def save_video():
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(VIDEO_NAME, fourcc, FPS, RESOLUTION)
    for frame in frames:
        out.write(frame)
    out.release()
    print(f"💾 저장 완료: {VIDEO_NAME}")

# === 자막 + 음성 추가 ===
def analyze_and_add_audio(video_file):
    description = "이 영상은 사용자 화면을 녹화한 것입니다. 주요 작업이 진행되었습니다."
    print("🎙️ 설명 생성 중...")

    # TTS
    tts = gTTS(text=description, lang="ko")
    tts_file = "tts.mp3"
    tts.save(tts_file)

    # FFmpeg 자막+음성 병합
    output_final = f"final_{video_file}"
    cmd = [
        "ffmpeg", "-y", "-i", video_file, "-i", tts_file,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", output_final
    ]
    subprocess.run(cmd)
    print(f"✅ 최종 영상 생성: {output_final}")

# === 키보드 이벤트 ===
def on_activate_start():
    global RECORDING
    if not RECORDING:
        RECORDING = True
        threading.Thread(target=record_screen, daemon=True).start()

def on_activate_stop():
    global RECORDING
    if RECORDING:
        RECORDING = False
        print("⏳ 후처리 준비 중...")
        threading.Thread(target=post_process, daemon=True).start()

def on_activate_exit():
    print("🛑 강제 종료")
    os._exit(0)

# === 후처리 ===
def post_process():
    time.sleep(10)
    save_video()
    analyze_and_add_audio(VIDEO_NAME)
    os._exit(0)

# === 핫키 등록 ===
print("⌨️ Ctrl+1 → 녹화 시작 / Ctrl+3 → 녹화 종료 / Ctrl+5 → 종료")
with keyboard.GlobalHotKeys({
    '<ctrl>+1': on_activate_start,
    '<ctrl>+3': on_activate_stop,
    '<ctrl>+5': on_activate_exit
}) as h:
    h.join()
