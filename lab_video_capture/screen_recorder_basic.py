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

from __future__ import annotations  # 최신 타입 힌트 문법을 안전하게 사용합니다.

import os  # 프로세스 종료와 파일 경로 관련 작업에 사용합니다.
import subprocess  # ffmpeg 외부 명령 실행에 사용합니다.
import threading  # 녹화 루프/후처리를 백그라운드 스레드로 실행합니다.
import time  # FPS 제어와 후처리 지연 대기에 사용합니다.
from datetime import datetime  # 출력 파일명에 타임스탬프를 넣기 위해 사용합니다.
from typing import Any  # 프레임 리스트 타입 힌트를 유연하게 지정하기 위해 사용합니다.

import cv2  # 영상 저장과 색상 변환에 사용합니다.
import numpy as np  # PIL 이미지를 배열로 바꿀 때 사용합니다.
from gtts import gTTS  # 텍스트를 음성 mp3로 합성합니다.
from mss import mss  # 화면 캡처를 수행합니다.
from PIL import Image  # 캡처된 raw 버퍼를 이미지로 다룹니다.
from pynput import keyboard  # 전역 단축키 입력을 처리합니다.

# === 설정 ===
FPS = 15  # 기본 녹화 프레임레이트를 15fps로 설정합니다.
RESOLUTION = (720, 1080)  # 출력 영상 해상도(가로, 세로)를 고정합니다.

# === 전역 상태 ===
RECORDING = False  # 녹화 루프 동작 여부를 제어하는 상태 값입니다.
VIDEO_NAME = ""  # 녹화 시작 시 생성될 출력 파일명을 저장합니다.
frames: list[Any] = []  # 캡처된 프레임들을 메모리에 누적 저장합니다.


# === 유틸 함수 ===
def center_crop(
    width: int, height: int, target_res: tuple[int, int]
) -> tuple[int, int, int, int]:
    """화면 중앙에서 target_res 크기만큼 크롭하는 좌표를 반환합니다."""
    tw, th = target_res  # 목표 해상도 가로/세로 값을 분리합니다.
    x1 = (width - tw) // 2  # 중앙 기준 크롭 박스의 시작 x 좌표를 계산합니다.
    y1 = (height - th) // 2  # 중앙 기준 크롭 박스의 시작 y 좌표를 계산합니다.
    return x1, y1, x1 + tw, y1 + th  # (좌,상,우,하) 좌표 튜플을 반환합니다.


# === 화면 녹화 루프 ===
def record_screen() -> None:
    """스크린 캡처 루프. 별도 스레드에서 실행됩니다."""
    global RECORDING, frames  # 전역 상태와 프레임 버퍼를 함수 내부에서 갱신합니다.
    sct = mss()  # 화면 캡처 세션을 초기화합니다.
    monitor = sct.monitors[1]  # 주 모니터를 녹화 대상으로 선택합니다.
    print("🎥 녹화 시작")  # 녹화 시작 메시지를 출력합니다.

    while RECORDING:  # 녹화 상태가 켜져 있는 동안 프레임을 반복 수집합니다.
        sct_img = sct.grab(monitor)  # 현재 모니터 화면을 캡처합니다.
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)  # raw RGB 버퍼를 PIL 이미지로 변환합니다.
        img = img.crop(center_crop(sct_img.width, sct_img.height, RESOLUTION))  # 목표 해상도 기준 중앙 영역만 크롭합니다.
        frame = cv2.cvtColor(np.array(img.resize(RESOLUTION)), cv2.COLOR_RGB2BGR)  # 최종 해상도로 맞춘 뒤 OpenCV BGR 포맷으로 변환합니다.
        frames.append(frame)  # 변환된 프레임을 버퍼에 순서대로 추가합니다.
        time.sleep(1 / FPS)  # 목표 FPS를 유지하도록 프레임 간 간격을 둡니다.

    print("🛑 녹화 종료")  # 루프 종료 시 사용자에게 녹화 종료를 알립니다.


# === 영상 저장 ===
def save_video() -> None:
    """frames 를 VIDEO_NAME 파일로 저장합니다."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # mp4v 코덱 식별자를 생성합니다.
    out = cv2.VideoWriter(VIDEO_NAME, fourcc, FPS, RESOLUTION)  # 출력 파일/코덱/FPS/해상도를 지정해 writer를 생성합니다.
    for frame in frames:  # 메모리에 모아둔 프레임을 순회합니다.
        out.write(frame)  # 각 프레임을 비디오 파일에 기록합니다.
    out.release()  # 파일 핸들을 닫아 비디오 저장을 완료합니다.
    print(f"💾 저장 완료: {VIDEO_NAME}")  # 저장 완료 메시지를 출력합니다.


# === TTS + 영상 합성 ===
def analyze_and_add_audio(video_file: str) -> None:
    """TTS로 설명 음성을 생성하고 FFmpeg로 영상에 합칩니다."""
    description = "이 영상은 사용자 화면을 녹화한 것입니다. 주요 작업이 진행되었습니다."  # 영상에 붙일 고정 설명 문장을 정의합니다.
    print("🎙️ 설명 생성 중...")  # 음성 합성 시작 로그를 출력합니다.

    tts = gTTS(text=description, lang="ko")  # 한글 설명 문장을 한국어 TTS 엔진으로 합성 준비합니다.
    tts_file = "tts.mp3"  # 임시 음성 파일명을 지정합니다.
    tts.save(tts_file)  # 합성된 음성을 mp3 파일로 저장합니다.

    output_final = f"final_{video_file}"  # 최종 결과물 파일명(원본 앞에 final_)을 생성합니다.
    cmd = [  # ffmpeg 명령 인자 목록을 구성합니다.
        "ffmpeg", "-y",  # 기존 결과 파일이 있어도 덮어쓰도록 지정합니다.
        "-i", video_file, "-i", tts_file,  # 원본 영상과 생성된 TTS 오디오를 입력으로 지정합니다.
        "-c:v", "copy", "-c:a", "aac",  # 영상은 재인코딩 없이 복사하고 오디오는 AAC로 인코딩합니다.
        "-map", "0:v:0", "-map", "1:a:0",  # 영상은 첫 입력에서, 오디오는 두 번째 입력에서 가져오도록 스트림 매핑합니다.
        "-shortest", output_final,  # 더 짧은 스트림 길이에 맞춰 종료하며 출력 파일명을 지정합니다.
    ]
    subprocess.run(cmd, check=False)  # ffmpeg 명령을 실행하고 실패 시 예외 대신 종료 코드로 처리합니다.
    print(f"✅ 최종 영상 생성: {output_final}")  # 최종 파일 생성 완료 로그를 출력합니다.


# === 후처리 ===
def post_process() -> None:
    """녹화 종료 후 영상 저장 및 TTS 합성을 수행합니다."""
    time.sleep(10)  # 마지막 프레임이 충분히 수집되도록 짧은 대기 시간을 둡니다.
    save_video()  # 누적된 프레임을 mp4 파일로 저장합니다.
    analyze_and_add_audio(VIDEO_NAME)  # 저장된 영상에 TTS 오디오를 합쳐 최종 파일을 생성합니다.
    os._exit(0)  # 백그라운드 스레드 환경에서 프로세스를 즉시 종료합니다.


# === 단축키 핸들러 ===
def on_activate_start() -> None:
    global RECORDING, VIDEO_NAME  # 녹화 상태와 파일명을 갱신하기 위해 전역 변수를 선언합니다.
    if not RECORDING:  # 이미 녹화 중이면 중복 시작을 방지합니다.
        VIDEO_NAME = f"record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"  # 현재 시각 기반 출력 파일명을 생성합니다.
        RECORDING = True  # 녹화 상태를 활성화합니다.
        threading.Thread(target=record_screen, daemon=True).start()  # 녹화 루프를 데몬 스레드로 시작합니다.


def on_activate_stop() -> None:
    global RECORDING  # 전역 녹화 상태를 갱신합니다.
    if RECORDING:  # 녹화 중일 때만 정지 로직을 수행합니다.
        RECORDING = False  # 녹화 루프를 종료 상태로 전환합니다.
        print("⏳ 후처리 준비 중...")  # 저장/합성 작업 시작 예정 로그를 출력합니다.
        threading.Thread(target=post_process, daemon=True).start()  # 후처리 작업을 별도 스레드에서 비동기로 실행합니다.


def on_activate_exit() -> None:
    print("🛑 강제 종료")  # 즉시 종료 요청 로그를 출력합니다.
    os._exit(0)  # 프로그램을 강제로 종료합니다.


# === 진입점 ===
def main() -> None:
    print("⌨️ Ctrl+1 → 녹화 시작 / Ctrl+3 → 녹화 종료 / Ctrl+5 → 종료")  # 사용자에게 단축키 조작법을 안내합니다.
    with keyboard.GlobalHotKeys({  # 전역 단축키와 콜백 함수를 매핑합니다.
        "<ctrl>+1": on_activate_start,  # Ctrl+1 입력 시 녹화를 시작합니다.
        "<ctrl>+3": on_activate_stop,  # Ctrl+3 입력 시 녹화를 멈추고 후처리를 시작합니다.
        "<ctrl>+5": on_activate_exit,  # Ctrl+5 입력 시 프로그램을 종료합니다.
    }) as h:
        h.join()  # 키 리스너를 메인 스레드에서 유지합니다.


if __name__ == "__main__":  # 파일 직접 실행 시에만 main을 호출합니다.
    main()  # 전역 단축키 기반 녹화 프로그램을 시작합니다.
