"""
Lab: 동영상 자막 제거 (인페인팅)
==================================
영상에서 프레임을 추출하고, 화면 하단 자막 영역을 인페인팅으로
제거한 뒤 새 영상으로 재조립합니다.

사용법:
    python subtitle_remover.py                   # 기본값: 1.mp4 입력
    python subtitle_remover.py <input_video>

출력 파일: output_cleaned.mp4

의존성: opencv-python, rembg, pillow, ffmpeg (시스템 설치 필요)
"""

from __future__ import annotations  # 최신 타입 힌트 문법을 안정적으로 사용합니다.

import os  # 폴더 생성과 경로 문자열 처리에 사용합니다.
import subprocess  # ffmpeg 명령 실행에 사용합니다.
import sys  # CLI 인자 파싱에 사용합니다.
from typing import Any  # OpenCV 반환 타입이 유동적이라 보수적 타입 힌트를 위해 사용합니다.

import cv2  # 프레임 추출, 마스크 생성, 인페인팅 처리에 사용합니다.


# === 프레임 추출 ===
def extract_frames(video_path: str, frames_dir: str = "frames") -> int:
    """video_path 의 모든 프레임을 frames_dir 에 PNG로 저장합니다."""
    os.makedirs(frames_dir, exist_ok=True)  # 프레임 저장 폴더가 없으면 생성합니다.
    video = cv2.VideoCapture(video_path)  # 입력 영상을 열어 순차적으로 프레임을 읽습니다.
    count = 0  # 저장한 프레임 개수를 카운트합니다.

    while True:  # 영상 끝까지 프레임을 반복 읽습니다.
        ret, frame = video.read()  # 다음 프레임을 읽고 성공 여부를 함께 받습니다.
        if not ret:  # 더 이상 읽을 프레임이 없으면 루프를 종료합니다.
            break
        cv2.imwrite(f"{frames_dir}/frame_{count:05d}.png", frame)  # 프레임 번호를 0패딩해 정렬 가능한 파일명으로 저장합니다.
        count += 1  # 다음 프레임 번호를 위해 카운터를 증가시킵니다.

    video.release()  # 비디오 핸들을 해제해 리소스 누수를 방지합니다.
    print(f"[INFO] {count}개 프레임 추출 완료 → {frames_dir}/")  # 추출 결과를 로그로 알려줍니다.
    return count  # 후속 처리에 필요한 총 프레임 수를 반환합니다.


# === 자막 인페인팅 ===
def inpaint_subtitles(img_path: str) -> Any:
    """
    이미지 하단 중앙 자막 영역(하단 15%, 가로 20~80%)을
    인페인팅으로 제거한 결과를 반환합니다.
    """
    img = cv2.imread(img_path)  # 처리할 프레임 이미지를 읽습니다.
    h, w, _ = img.shape  # 영상 높이/너비를 가져와 자막 영역 좌표 계산에 사용합니다.

    x1, y1 = int(w * 0.2), int(h * 0.85)  # 자막 박스의 좌상단 좌표를 경험적 비율로 계산합니다.
    x2, y2 = int(w * 0.8), int(h * 0.98)  # 자막 박스의 우하단 좌표를 경험적 비율로 계산합니다.

    mask = img.copy()  # 마스크 생성을 위해 원본과 같은 크기의 이미지 버퍼를 만듭니다.
    cv2.rectangle(mask, (x1, y1), (x2, y2), (255, 255, 255), -1)  # 자막 추정 영역을 흰색으로 채워 인페인팅 타깃을 지정합니다.

    gray_mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)  # 인페인팅 API 입력 형식에 맞춰 단일 채널 마스크로 변환합니다.
    return cv2.inpaint(img, gray_mask, 3, cv2.INPAINT_TELEA)  # Telea 알고리즘으로 마스크 영역을 주변 픽셀로 복원합니다.


# === 인페인팅 일괄 적용 ===
def clean_frames(
    frame_count: int,
    frames_dir: str = "frames",
    cleaned_dir: str = "cleaned_frames",
) -> None:
    """frames_dir 의 프레임 전체에 자막 인페인팅을 적용합니다."""
    os.makedirs(cleaned_dir, exist_ok=True)  # 정제된 프레임 저장 폴더를 준비합니다.

    for i in range(frame_count):  # 추출된 프레임 번호를 처음부터 끝까지 순회합니다.
        src = f"{frames_dir}/frame_{i:05d}.png"  # 원본 프레임 파일 경로를 구성합니다.
        dst = f"{cleaned_dir}/frame_{i:05d}.png"  # 인페인팅 결과 프레임 저장 경로를 구성합니다.
        cleaned = inpaint_subtitles(src)  # 단일 프레임 자막 제거 함수를 호출합니다.
        cv2.imwrite(dst, cleaned)  # 처리된 프레임을 결과 폴더에 저장합니다.

    print(f"[INFO] 인페인팅 완료 → {cleaned_dir}/")  # 전체 프레임 처리 완료 로그를 출력합니다.


# === 영상 재조립 ===
def assemble_video(
    cleaned_dir: str = "cleaned_frames", output: str = "output_cleaned.mp4"
) -> None:
    """정리된 프레임을 FFmpeg로 영상으로 조립합니다."""
    subprocess.run(  # ffmpeg 커맨드를 실행해 연속 이미지 시퀀스를 mp4로 인코딩합니다.
        [
            "ffmpeg", "-y",  # 기존 출력 파일이 있어도 덮어쓰도록 지정합니다.
            "-framerate", "30",  # 프레임 시퀀스의 재생 FPS를 30으로 설정합니다.
            "-i", f"{cleaned_dir}/frame_%05d.png",  # 0패딩 번호 패턴의 입력 프레임 시퀀스를 지정합니다.
            "-c:v", "libx264",  # H.264 코덱으로 인코딩해 범용 호환성을 높입니다.
            "-pix_fmt", "yuv420p",  # 플레이어 호환성이 높은 픽셀 포맷을 사용합니다.
            output,  # 최종 출력 파일명을 지정합니다.
        ],
        check=False,  # ffmpeg 오류 발생 시 예외 대신 종료 코드로 처리합니다.
    )
    print(f"[DONE] 저장 완료: {output}")  # 결과 영상 생성 완료를 알립니다.


# === 메인 파이프라인 ===
def run(video_path: str = "1.mp4") -> None:
    """프레임 추출 → 자막 제거 → 영상 재조립 파이프라인을 실행합니다."""
    print(f"[INFO] 입력 영상: {video_path}")  # 처리 시작 시 입력 파일 정보를 기록합니다.
    frame_count = extract_frames(video_path)  # 원본 영상에서 모든 프레임을 추출합니다.
    clean_frames(frame_count)  # 추출된 프레임 전체에 인페인팅을 적용합니다.
    assemble_video()  # 정제된 프레임을 다시 하나의 mp4로 합칩니다.


# === 진입점 ===
if __name__ == "__main__":  # 파일 직접 실행 시에만 CLI 파이프라인을 수행합니다.
    input_video = sys.argv[1] if len(sys.argv) > 1 else "1.mp4"  # 인자가 있으면 사용자 입력 파일을, 없으면 기본 파일명을 사용합니다.
    run(input_video)  # 선택된 입력 영상으로 전체 파이프라인을 실행합니다.
