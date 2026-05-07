"""
Lab: 화면 녹화 → AI 캡션 파이프라인 (오케스트레이터)
======================================================
screen_recorder.py를 실행해 녹화를 마치고,
결과 mp4를 자동으로 찾아 video_captioner.py로 분석합니다.

사용법:
    python video_pipeline.py

흐름:
    1. screen_recorder.py 실행 → 녹화 완료 대기
    2. 가장 최근 z_*.mp4 또는 record_*.mp4 탐색
    3. video_captioner.py 로 AI 캡션 + TTS 합성
"""

from __future__ import annotations  # 최신 타입 힌트 문법을 안전하게 사용합니다.

import os  # 파일 수정 시간 확인에 사용합니다.
import subprocess  # 하위 스크립트 실행에 사용합니다.
import sys  # 현재 파이썬 인터프리터 경로와 종료 코드 처리에 사용합니다.
import time  # 녹화 종료 후 파일 flush 대기 시간에 사용합니다.
from glob import glob  # 패턴으로 녹화 파일을 찾는 데 사용합니다.


# === 유틸 함수 ===
def find_latest_video() -> str | None:
    """현재 디렉터리에서 가장 최근 녹화 영상을 반환합니다."""
    candidates = []  # 녹화 파일 후보를 담을 리스트를 준비합니다.
    for pattern in ("z_*.mp4", "record_*.mp4"):  # 지원하는 녹화 파일명 패턴을 순회합니다.
        candidates.extend(glob(pattern))  # 각 패턴으로 검색된 파일을 후보 목록에 추가합니다.
    candidates.sort(key=os.path.getmtime, reverse=True)  # 수정 시간이 최신인 파일이 앞에 오도록 정렬합니다.
    return candidates[0] if candidates else None  # 후보가 있으면 첫 파일(최신)을, 없으면 None을 반환합니다.


# === 파이프라인 실행 ===
def run() -> None:
    """녹화 → 분석 파이프라인을 순서대로 실행합니다."""
    print("[INFO] launching screen_recorder.py...")  # 1단계 시작 로그를 출력합니다.
    cap_process = subprocess.Popen([sys.executable, "screen_recorder.py"])  # 현재 파이썬 환경으로 녹화 스크립트를 실행합니다.
    cap_process.wait()  # 녹화 프로세스가 끝날 때까지 대기합니다.
    print("[INFO] screen_recorder.py finished. waiting 2 seconds for file flush...")  # 녹화 종료 후 대기 안내를 출력합니다.
    time.sleep(2)  # 파일 시스템 반영을 위해 잠시 기다립니다.

    latest_video = find_latest_video()  # 최신 녹화 영상을 자동 탐색합니다.
    if not latest_video:  # 녹화 파일을 찾지 못한 예외 상황입니다.
        print("[ERROR] no recorded mp4 found.")  # 사용자에게 실패 원인을 알려줍니다.
        sys.exit(1)  # 오류 코드로 종료합니다.

    print(f"[INFO] analyzing: {latest_video}")  # 분석 대상 영상 파일명을 로그로 남깁니다.
    subprocess.run([sys.executable, "video_captioner.py", latest_video], check=False)  # 3단계 분석 스크립트를 실행합니다.

    print("[DONE] pipeline finished.")  # 전체 파이프라인 종료 로그를 출력합니다.


# === 진입점 ===
if __name__ == "__main__":  # 파일 직접 실행 시에만 오케스트레이션을 수행합니다.
    run()  # 녹화 후 분석 파이프라인을 시작합니다.
