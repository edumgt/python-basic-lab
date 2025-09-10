import cv2
import numpy as np
import threading
import time
from pynput import keyboard
from mss import mss
from PIL import Image
from collections import deque
import pyautogui
import sys
from datetime import datetime

# === 설정 ===
FPS = 24
RESOLUTION = (768, 1366)
RECORDING = False
FRAME_QUEUE = deque()
VIDEO_NAME = ""  # 저장 파일명 (시간 기반으로 결정)

# === 중앙 크롭 좌표 계산 ===
def center_crop(width, height, target_res):
    tw, th = target_res
    x1 = (width - tw) // 2
    y1 = (height - th) // 2
    x2 = x1 + tw
    y2 = y1 + th
    return (x1, y1, x2, y2)

# === 영상 저장 ===
def save_video(frames):
    if not frames:
        print("⚠️ 저장할 프레임이 없습니다.")
        return
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(VIDEO_NAME, fourcc, FPS, RESOLUTION)
    for f in frames:
        out.write(f)
    out.release()
    print(f"✅ 동영상 저장 완료: {VIDEO_NAME}")

# === 녹화 함수 ===
def record_screen():
    global RECORDING, FRAME_QUEUE, VIDEO_NAME
    VIDEO_NAME = f"z_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    print("⏱️ 5초 후 녹화 시작...")
    time.sleep(5)

    sct = mss()
    monitor = sct.monitors[1]
    FRAME_QUEUE = deque()

    print("🎥 녹화 중... Ctrl+3 누르면 종료")
    while RECORDING:
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        img = img.crop(center_crop(sct_img.width, sct_img.height, RESOLUTION))
        img = img.resize(RESOLUTION)

        frame = np.array(img)
        x, y = pyautogui.position()
        x_crop = x - (sct_img.width - RESOLUTION[0]) // 2
        y_crop = y - (sct_img.height - RESOLUTION[1]) // 2
        if 0 <= x_crop < RESOLUTION[0] and 0 <= y_crop < RESOLUTION[1]:
            cv2.circle(frame, (x_crop, y_crop), 6, (0, 255, 0), -1)

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        FRAME_QUEUE.append(frame_bgr)

        time.sleep(1 / FPS)

    print("🛑 녹화 중지됨. 마지막 5초 제외 중...")
    cutoff = int(FPS * 5)
    if len(FRAME_QUEUE) > cutoff:
        FRAME_QUEUE = deque(list(FRAME_QUEUE)[:-cutoff])

    save_video(list(FRAME_QUEUE))
    sys.exit(0)

# === 핫키 함수 정의 ===
def start_recording():
    global RECORDING
    if not RECORDING:
        RECORDING = True
        threading.Thread(target=record_screen, daemon=True).start()

def stop_recording():
    global RECORDING
    if RECORDING:
        RECORDING = False

def force_quit():
    print("💥 프로그램 강제 종료")
    sys.exit(1)

# === 실행 ===
print("⌨️ Ctrl+1 → 녹화 시작 (5초 후)")
print("⌨️ Ctrl+3 → 녹화 종료 (마지막 5초 제외 + 저장)")
print("⌨️ Ctrl+5 → 프로그램 종료")

with keyboard.GlobalHotKeys({
    '<ctrl>+1': start_recording,
    '<ctrl>+3': stop_recording,
    '<ctrl>+5': force_quit
}) as h:
    h.join()
