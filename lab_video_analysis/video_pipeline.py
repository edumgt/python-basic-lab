"""
Lab: 화면 녹화 → AI 캡션 파이프라인 (오케스트레이터)
======================================================
screen_recorder.py(cap.py)를 실행해 녹화를 마치고,
결과 mp4를 자동으로 찾아 video_captioner.py(ana.py)로 분석합니다.

사용법:
    python video_pipeline.py

흐름:
    1. screen_recorder.py 실행 → 녹화 완료 대기
    2. 가장 최근 z_*.mp4 또는 record_*.mp4 탐색
    3. video_captioner.py 로 AI 캡션 + TTS 합성
"""

import os
import subprocess
import sys
import time
from glob import glob


# === 유틸 함수 ===
def find_latest_video():
    """현재 디렉터리에서 가장 최근 녹화 영상을 반환합니다."""
    candidates = []
    for pattern in ("z_*.mp4", "record_*.mp4"):
        candidates.extend(glob(pattern))
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0] if candidates else None


# === 파이프라인 실행 ===
def run():
    """녹화 → 분석 파이프라인을 순서대로 실행합니다."""
    # 1단계: 화면 녹화
    print("[INFO] launching screen_recorder.py...")
    cap_process = subprocess.Popen([sys.executable, "screen_recorder.py"])
    cap_process.wait()
    print("[INFO] screen_recorder.py finished. waiting 2 seconds for file flush...")
    time.sleep(2)

    # 2단계: 영상 파일 탐색
    latest_video = find_latest_video()
    if not latest_video:
        print("[ERROR] no recorded mp4 found.")
        sys.exit(1)

    # 3단계: AI 캡션 + TTS 분석
    print(f"[INFO] analyzing: {latest_video}")
    subprocess.run([sys.executable, "video_captioner.py", latest_video], check=False)

    print("[DONE] pipeline finished.")


# === 진입점 ===
if __name__ == "__main__":
    run()
