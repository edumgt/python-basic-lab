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

from __future__ import annotations  # 최신 타입 힌트 문법을 안전하게 사용합니다.

import sys  # 프로그램 종료 코드 처리와 프로세스 종료에 사용합니다.
import threading  # 녹화 루프를 백그라운드 스레드로 실행하기 위해 사용합니다.
import time  # 녹화 프레임 간격 제어와 시작 지연에 사용합니다.
from collections import deque  # 프레임을 빠르게 append/pop 하기 위한 큐 자료구조입니다.
from datetime import datetime  # 파일명 타임스탬프 생성에 사용합니다.
from typing import Any  # 프레임 리스트 타입 힌트를 유연하게 유지하기 위해 사용합니다.

import cv2  # 영상 인코딩과 색상 변환, 커서 표시 도형 그리기에 사용합니다.
import numpy as np  # PIL 이미지를 OpenCV 배열로 변환할 때 사용합니다.
import pyautogui  # 현재 마우스 커서 좌표를 읽기 위해 사용합니다.
from mss import mss  # 화면 캡처를 위한 고속 스크린샷 라이브러리입니다.
from PIL import Image  # 캡처 버퍼를 PIL 이미지로 변환해 크롭/리사이즈에 사용합니다.
from pynput import keyboard  # 전역 단축키를 등록해 녹화 시작/종료를 제어합니다.

# === 설정 ===
FPS = 24  # 초당 캡처 프레임 수를 정의합니다.
RESOLUTION = (768, 1366)  # 출력 영상 해상도(가로, 세로)를 고정합니다.
TRIM_TAIL_SEC = 5  # 녹화 종료 시 마지막 N초를 제거하기 위한 기준 시간입니다.

# === 전역 상태 ===
RECORDING = False  # 현재 녹화 루프 실행 여부를 나타내는 상태 플래그입니다.
FRAME_QUEUE: deque = deque()  # 캡처된 프레임을 순서대로 누적하는 버퍼입니다.
VIDEO_NAME = ""  # 저장될 출력 파일명을 런타임에 동적으로 채웁니다.


# === 유틸 함수 ===
def center_crop(
    width: int, height: int, target_res: tuple[int, int]
) -> tuple[int, int, int, int]:
    """화면 중앙에서 target_res 크기만큼 크롭하는 좌표를 반환합니다."""
    tw, th = target_res  # 목표 해상도의 가로/세로를 분리합니다.
    x1 = (width - tw) // 2  # 중앙 정렬된 좌측 시작 x 좌표를 계산합니다.
    y1 = (height - th) // 2  # 중앙 정렬된 상단 시작 y 좌표를 계산합니다.
    return x1, y1, x1 + tw, y1 + th  # 크롭 박스의 (좌,상,우,하) 좌표를 반환합니다.


def save_video(frames: list[Any]) -> None:
    """frames 리스트를 VIDEO_NAME 파일로 저장합니다."""
    if not frames:  # 저장할 프레임이 하나도 없는 예외 상황을 방어합니다.
        print("⚠️ 저장할 프레임이 없습니다.")  # 사용자에게 저장 불가 사유를 안내합니다.
        return  # 빈 영상 생성을 막기 위해 함수를 조기 종료합니다.
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # mp4 컨테이너에서 사용할 비디오 코덱 코드를 생성합니다.
    out = cv2.VideoWriter(VIDEO_NAME, fourcc, FPS, RESOLUTION)  # 지정한 파일명/FPS/해상도로 VideoWriter를 엽니다.
    for f in frames:  # 누적된 프레임을 순서대로 순회합니다.
        out.write(f)  # 각 프레임을 비디오 스트림에 기록합니다.
    out.release()  # 파일 핸들을 닫아 mp4 파일을 정상 완료합니다.
    print(f"✅ 동영상 저장 완료: {VIDEO_NAME}")  # 결과 파일 경로를 사용자에게 출력합니다.


# === 녹화 루프 ===
def record_screen() -> None:
    """스크린 캡처 루프. 별도 스레드에서 실행됩니다."""
    global RECORDING, FRAME_QUEUE, VIDEO_NAME  # 전역 녹화 상태와 버퍼/파일명을 함수 내에서 갱신합니다.

    VIDEO_NAME = f"z_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"  # 실행 시각 기반의 고유 파일명을 생성합니다.
    print(f"⏱️ {TRIM_TAIL_SEC}초 후 녹화 시작...")  # 지연 시작 정보를 사용자에게 안내합니다.
    time.sleep(TRIM_TAIL_SEC)  # 시작 전 지연을 줘 준비 시간을 확보합니다.

    sct = mss()  # 화면 캡처 세션을 초기화합니다.
    monitor = sct.monitors[1]  # 주 모니터(첫 번째 실제 모니터)를 캡처 대상으로 선택합니다.
    FRAME_QUEUE = deque()  # 이전 녹화 잔여 데이터를 제거하고 새 큐를 준비합니다.

    print("🎥 녹화 중... Ctrl+3 누르면 종료")  # 녹화 중 상태와 종료 단축키를 안내합니다.
    while RECORDING:  # 녹화 상태가 유지되는 동안 프레임 캡처를 반복합니다.
        sct_img = sct.grab(monitor)  # 현재 모니터 화면을 raw 버퍼로 캡처합니다.
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)  # raw RGB 버퍼를 PIL 이미지로 변환합니다.
        img = img.crop(center_crop(sct_img.width, sct_img.height, RESOLUTION))  # 중앙 기준으로 목표 해상도 영역을 크롭합니다.
        img = img.resize(RESOLUTION)  # 크롭된 이미지를 정확한 출력 해상도로 보정합니다.

        frame = np.array(img)  # PIL 이미지를 NumPy 배열로 변환해 OpenCV 처리 형식으로 맞춥니다.

        x, y = pyautogui.position()  # 현재 시스템 마우스 커서 좌표를 가져옵니다.
        x_crop = x - (sct_img.width - RESOLUTION[0]) // 2  # 전체 화면 좌표를 크롭 영역 기준 x 좌표로 변환합니다.
        y_crop = y - (sct_img.height - RESOLUTION[1]) // 2  # 전체 화면 좌표를 크롭 영역 기준 y 좌표로 변환합니다.
        if 0 <= x_crop < RESOLUTION[0] and 0 <= y_crop < RESOLUTION[1]:  # 커서가 크롭된 프레임 안에 있을 때만 표시합니다.
            cv2.circle(frame, (x_crop, y_crop), 6, (0, 255, 0), -1)  # 커서 위치에 녹색 원을 그려 시각화합니다.

        FRAME_QUEUE.append(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # OpenCV 표준 색상(BGR)으로 변환해 큐에 저장합니다.
        time.sleep(1 / FPS)  # 목표 FPS를 유지하도록 프레임 간 대기합니다.

    print(f"🛑 녹화 중지됨. 마지막 {TRIM_TAIL_SEC}초 제외 중...")  # 종료 후 자동 트림 동작을 사용자에게 안내합니다.
    cutoff = int(FPS * TRIM_TAIL_SEC)  # 제거할 마지막 프레임 수를 FPS와 시간으로 계산합니다.
    for _ in range(min(cutoff, len(FRAME_QUEUE))):  # 실제 큐 길이를 넘지 않도록 안전하게 반복합니다.
        FRAME_QUEUE.pop()  # 큐의 뒤에서부터 프레임을 제거해 마지막 구간을 삭제합니다.

    save_video(list(FRAME_QUEUE))  # 남은 프레임을 리스트로 변환해 저장 함수를 호출합니다.
    sys.exit(0)  # 녹화 스레드 종료 후 프로세스를 정상 종료합니다.


# === 단축키 핸들러 ===
def start_recording() -> None:
    global RECORDING  # 전역 녹화 상태를 갱신합니다.
    if not RECORDING:  # 이미 녹화 중이면 중복 시작을 막습니다.
        RECORDING = True  # 녹화 상태를 활성화합니다.
        threading.Thread(target=record_screen, daemon=True).start()  # 녹화 루프를 데몬 스레드로 시작합니다.


def stop_recording() -> None:
    global RECORDING  # 전역 녹화 상태를 갱신합니다.
    if RECORDING:  # 녹화 중일 때만 정지 요청을 반영합니다.
        RECORDING = False  # while 루프 조건을 해제해 녹화를 멈춥니다.


def force_quit() -> None:
    print("💥 프로그램 강제 종료")  # 강제 종료 요청을 로그로 출력합니다.
    sys.exit(1)  # 비정상 종료 코드로 즉시 프로세스를 종료합니다.


# === 진입점 ===
def main() -> None:
    print("⌨️ Ctrl+1 → 녹화 시작 (5초 후)")  # 시작 단축키 안내를 출력합니다.
    print("⌨️ Ctrl+3 → 녹화 종료 (마지막 5초 제외 + 저장)")  # 종료 단축키 안내를 출력합니다.
    print("⌨️ Ctrl+5 → 프로그램 종료")  # 강제 종료 단축키 안내를 출력합니다.

    with keyboard.GlobalHotKeys({  # 전역 단축키 매핑을 등록합니다.
        "<ctrl>+1": start_recording,  # Ctrl+1 입력 시 녹화 시작 핸들러를 호출합니다.
        "<ctrl>+3": stop_recording,  # Ctrl+3 입력 시 녹화 종료 핸들러를 호출합니다.
        "<ctrl>+5": force_quit,  # Ctrl+5 입력 시 강제 종료 핸들러를 호출합니다.
    }) as h:
        h.join()  # 키 리스너 스레드를 블로킹해 프로그램을 계속 실행 상태로 유지합니다.


if __name__ == "__main__":  # 파일 직접 실행 시에만 main 함수를 호출합니다.
    main()  # 전역 단축키 기반 녹화 프로그램을 시작합니다.
