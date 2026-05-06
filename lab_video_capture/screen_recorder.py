"""
Lab: 화면 녹화 — 고급 버전 (커서 시각화, 딜레이, 자동 트림)
=============================================================
전역 단축키로 화면을 녹화하고 mp4로 저장합니다.
마지막 5초는 자동으로 제거됩니다.

단축키:
    Ctrl+1 → 5초 뒤 녹화 시작
    Ctrl+3 → 녹화 종료 후 저장
    Ctrl+5 → 프로그램 강제 종료

의존성: opencv-python, mss, pillow, pynput, pyautogui, numpy
"""

import sys
import threading
import time
from collections import deque
from datetime import datetime

import cv2
import numpy as np
import pyautogui
from mss import mss
from PIL import Image
from pynput import keyboard

# === 설정 ===
FPS = 24
RESOLUTION = (768, 1366)   # (너비, 높이)
TRIM_TAIL_SEC = 5           # 종료 전 마지막 N초 제거

# === 전역 상태 ===
RECORDING = False
FRAME_QUEUE: deque = deque()
VIDEO_NAME = ""


# === 유틸 함수 ===
def center_crop(width, height, target_res):
    """화면 중앙에서 target_res 크기만큼 크롭하는 좌표를 반환합니다."""
    tw, th = target_res
    x1 = (width - tw) // 2
    y1 = (height - th) // 2
    return x1, y1, x1 + tw, y1 + th


def save_video(frames):
    """frames 리스트를 VIDEO_NAME 파일로 저장합니다."""
    if not frames:
        print("⚠️ 저장할 프레임이 없습니다.")
        return
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(VIDEO_NAME, fourcc, FPS, RESOLUTION)
    for f in frames:
        out.write(f)
    out.release()
    print(f"✅ 동영상 저장 완료: {VIDEO_NAME}")


# === 녹화 루프 ===
def record_screen():
    """스크린 캡처 루프. 별도 스레드에서 실행됩니다."""
    global RECORDING, FRAME_QUEUE, VIDEO_NAME

    VIDEO_NAME = f"z_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    print(f"⏱️ {TRIM_TAIL_SEC}초 후 녹화 시작...")
    time.sleep(TRIM_TAIL_SEC)

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

        # 마우스 커서 시각화
        x, y = pyautogui.position()
        x_crop = x - (sct_img.width - RESOLUTION[0]) // 2
        y_crop = y - (sct_img.height - RESOLUTION[1]) // 2
        if 0 <= x_crop < RESOLUTION[0] and 0 <= y_crop < RESOLUTION[1]:
            cv2.circle(frame, (x_crop, y_crop), 6, (0, 255, 0), -1)

        FRAME_QUEUE.append(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        time.sleep(1 / FPS)

    # 마지막 N초 제거
    print(f"🛑 녹화 중지됨. 마지막 {TRIM_TAIL_SEC}초 제외 중...")
    cutoff = int(FPS * TRIM_TAIL_SEC)
    for _ in range(min(cutoff, len(FRAME_QUEUE))):
        FRAME_QUEUE.pop()

    save_video(list(FRAME_QUEUE))
    sys.exit(0)


# === 단축키 핸들러 ===
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


# === 진입점 ===
def main():
    print("⌨️ Ctrl+1 → 녹화 시작 (5초 후)")
    print("⌨️ Ctrl+3 → 녹화 종료 (마지막 5초 제외 + 저장)")
    print("⌨️ Ctrl+5 → 프로그램 종료")

    with keyboard.GlobalHotKeys({
        "<ctrl>+1": start_recording,
        "<ctrl>+3": stop_recording,
        "<ctrl>+5": force_quit,
    }) as h:
        h.join()


if __name__ == "__main__":
    main()
