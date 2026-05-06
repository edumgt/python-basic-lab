"""
Lab: 화면 녹화 — 기본 버전 (TTS 음성 설명 포함)
================================================
전역 단축키로 화면을 녹화하고 TTS 음성을 합쳐 mp4로 저장합니다.

단축키:
    Ctrl+1 → 녹화 시작
    Ctrl+3 → 녹화 종료 및 후처리 (TTS 합성)
    Ctrl+5 → 프로그램 종료

의존성: opencv-python, mss, pillow, pynput, gtts, numpy, ffmpeg-python
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime
from typing import Any

import cv2
import numpy as np
from gtts import gTTS
from mss import mss
from PIL import Image
from pynput import keyboard

# === 설정 ===
FPS = 15
RESOLUTION = (720, 1080)   # (너비, 높이)

# === 전역 상태 ===
RECORDING = False
VIDEO_NAME = ""
frames: list[Any] = []


# === 유틸 함수 ===
def center_crop(
    width: int, height: int, target_res: tuple[int, int]
) -> tuple[int, int, int, int]:
    """화면 중앙에서 target_res 크기만큼 크롭하는 좌표를 반환합니다."""
    tw, th = target_res
    x1 = (width - tw) // 2
    y1 = (height - th) // 2
    return x1, y1, x1 + tw, y1 + th


# === 화면 녹화 루프 ===
def record_screen() -> None:
    """스크린 캡처 루프. 별도 스레드에서 실행됩니다."""
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


# === 영상 저장 ===
def save_video() -> None:
    """frames 를 VIDEO_NAME 파일로 저장합니다."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(VIDEO_NAME, fourcc, FPS, RESOLUTION)
    for frame in frames:
        out.write(frame)
    out.release()
    print(f"💾 저장 완료: {VIDEO_NAME}")


# === TTS + 영상 합성 ===
def analyze_and_add_audio(video_file: str) -> None:
    """TTS로 설명 음성을 생성하고 FFmpeg로 영상에 합칩니다."""
    description = "이 영상은 사용자 화면을 녹화한 것입니다. 주요 작업이 진행되었습니다."
    print("🎙️ 설명 생성 중...")

    tts = gTTS(text=description, lang="ko")
    tts_file = "tts.mp3"
    tts.save(tts_file)

    output_final = f"final_{video_file}"
    cmd = [
        "ffmpeg", "-y",
        "-i", video_file, "-i", tts_file,
        "-c:v", "copy", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", output_final,
    ]
    subprocess.run(cmd, check=False)
    print(f"✅ 최종 영상 생성: {output_final}")


# === 후처리 ===
def post_process() -> None:
    """녹화 종료 후 영상 저장 및 TTS 합성을 수행합니다."""
    time.sleep(10)
    save_video()
    analyze_and_add_audio(VIDEO_NAME)
    os._exit(0)


# === 단축키 핸들러 ===
def on_activate_start() -> None:
    global RECORDING, VIDEO_NAME
    if not RECORDING:
        VIDEO_NAME = f"record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        RECORDING = True
        threading.Thread(target=record_screen, daemon=True).start()


def on_activate_stop() -> None:
    global RECORDING
    if RECORDING:
        RECORDING = False
        print("⏳ 후처리 준비 중...")
        threading.Thread(target=post_process, daemon=True).start()


def on_activate_exit() -> None:
    print("🛑 강제 종료")
    os._exit(0)


# === 진입점 ===
def main() -> None:
    print("⌨️ Ctrl+1 → 녹화 시작 / Ctrl+3 → 녹화 종료 / Ctrl+5 → 종료")
    with keyboard.GlobalHotKeys({
        "<ctrl>+1": on_activate_start,
        "<ctrl>+3": on_activate_stop,
        "<ctrl>+5": on_activate_exit,
    }) as h:
        h.join()


if __name__ == "__main__":
    main()
