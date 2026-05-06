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

import os
import sys

import cv2


# === 프레임 추출 ===
def extract_frames(video_path, frames_dir="frames"):
    """video_path 의 모든 프레임을 frames_dir 에 PNG로 저장합니다."""
    os.makedirs(frames_dir, exist_ok=True)
    video = cv2.VideoCapture(video_path)
    count = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break
        cv2.imwrite(f"{frames_dir}/frame_{count:05d}.png", frame)
        count += 1

    video.release()
    print(f"[INFO] {count}개 프레임 추출 완료 → {frames_dir}/")
    return count


# === 자막 인페인팅 ===
def inpaint_subtitles(img_path):
    """
    이미지 하단 중앙 자막 영역(하단 15%, 가로 20~80%)을
    인페인팅으로 제거한 결과를 반환합니다.
    """
    img = cv2.imread(img_path)
    h, w, _ = img.shape

    # 자막 위치 추정 (하단 15% 가운데 60%)
    x1, y1 = int(w * 0.2), int(h * 0.85)
    x2, y2 = int(w * 0.8), int(h * 0.98)

    mask = img.copy()
    cv2.rectangle(mask, (x1, y1), (x2, y2), (255, 255, 255), -1)

    gray_mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    return cv2.inpaint(img, gray_mask, 3, cv2.INPAINT_TELEA)


# === 인페인팅 일괄 적용 ===
def clean_frames(frame_count, frames_dir="frames", cleaned_dir="cleaned_frames"):
    """frames_dir 의 프레임 전체에 자막 인페인팅을 적용합니다."""
    os.makedirs(cleaned_dir, exist_ok=True)

    for i in range(frame_count):
        src = f"{frames_dir}/frame_{i:05d}.png"
        dst = f"{cleaned_dir}/frame_{i:05d}.png"
        cleaned = inpaint_subtitles(src)
        cv2.imwrite(dst, cleaned)

    print(f"[INFO] 인페인팅 완료 → {cleaned_dir}/")


# === 영상 재조립 ===
def assemble_video(cleaned_dir="cleaned_frames", output="output_cleaned.mp4"):
    """정리된 프레임을 FFmpeg로 영상으로 조립합니다."""
    cmd = (
        f"ffmpeg -y -framerate 30 -i {cleaned_dir}/frame_%05d.png "
        f"-c:v libx264 -pix_fmt yuv420p {output}"
    )
    os.system(cmd)
    print(f"[DONE] 저장 완료: {output}")


# === 메인 파이프라인 ===
def run(video_path="1.mp4"):
    """프레임 추출 → 자막 제거 → 영상 재조립 파이프라인을 실행합니다."""
    print(f"[INFO] 입력 영상: {video_path}")
    frame_count = extract_frames(video_path)
    clean_frames(frame_count)
    assemble_video()


# === 진입점 ===
if __name__ == "__main__":
    input_video = sys.argv[1] if len(sys.argv) > 1 else "1.mp4"
    run(input_video)
