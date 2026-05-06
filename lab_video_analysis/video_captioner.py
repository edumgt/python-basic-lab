"""
Lab: AI 자동 캡션 + TTS 비디오 파이프라인
==========================================
입력 영상에서 N초마다 프레임을 샘플링하고 BLIP 모델로 장면 설명을 생성합니다.
설명을 자막으로 삽입하고 gTTS로 요약 음성을 합쳐 최종 영상을 출력합니다.

사용법:
    python video_captioner.py [video_path] [options]
    python video_captioner.py                     # 최신 z_*.mp4 또는 record_*.mp4 자동 탐색
    python video_captioner.py input.mp4
    python video_captioner.py input.mp4 --frame-interval 3.0 --tts-lang en

옵션:
    --frame-interval  FLOAT  캡션 샘플링 간격(초), 기본값: 2.0
    --font-path       PATH   자막 폰트 경로, 기본값: malgun.ttf
    --font-size       INT    자막 폰트 크기, 기본값: 32
    --tts-lang        CODE   gTTS 언어 코드, 기본값: ko

의존성: opencv-python, ffmpeg-python, torch, transformers, pillow, gtts, numpy
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from glob import glob
from typing import Any

import cv2
import ffmpeg
import numpy as np
import torch
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from transformers import BlipForConditionalGeneration, BlipProcessor


# === 인자 파싱 ===
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Video caption + TTS pipeline.")
    parser.add_argument("video_path", nargs="?", help="Input mp4 path")
    parser.add_argument("--frame-interval", type=float, default=2.0, help="Seconds per caption sample")
    parser.add_argument("--font-path", default="malgun.ttf", help="Font file for subtitle text")
    parser.add_argument("--font-size", type=int, default=32, help="Subtitle font size")
    parser.add_argument("--tts-lang", default="ko", help="gTTS language code")
    return parser.parse_args()


# === 유틸 함수 ===
def find_latest_video() -> str | None:
    """현재 디렉터리에서 가장 최근 z_*.mp4 또는 record_*.mp4를 반환합니다."""
    candidates = sorted(
        glob("z_*.mp4") + glob("record_*.mp4"),
        key=os.path.getmtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_font(font_path: str, font_size: int) -> Any:
    """폰트를 로드합니다. 실패 시 기본 폰트를 사용합니다."""
    try:
        return ImageFont.truetype(font_path, font_size)
    except OSError:
        print(f"[WARN] Font not found: {font_path}. Falling back to default font.")
        return ImageFont.load_default()


# === 캡션 생성 + 자막 삽입 ===
def generate_captioned_video(
    video_path: str, frame_interval: float, font: Any
) -> tuple[str, list[str]]:
    """
    BLIP 모델로 영상 장면을 캡션하고 자막이 삽입된 임시 영상을 생성합니다.
    반환값: (임시 영상 경로, 캡션 리스트)
    """
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    ).to("cuda" if torch.cuda.is_available() else "cpu")

    temp_video = "temp_video.mp4"
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    frame_gap = max(1, int(fps * frame_interval))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

    captions = []
    count = 0
    current_caption = ""

    print("[INFO] generating captions...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % frame_gap == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            inputs = processor(images=rgb, return_tensors="pt").to(model.device)
            out_ids = model.generate(**inputs)
            caption_en = processor.decode(out_ids[0], skip_special_tokens=True)
            current_caption = f"Scene: {caption_en}"
            captions.append(current_caption)

        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text((40, height - 80), current_caption, font=font, fill=(255, 255, 255))
        out.write(cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR))
        count += 1

    cap.release()
    out.release()
    return temp_video, captions


# === 오디오 + 영상 합성 ===
def merge_audio_video(temp_video: str, temp_audio: str, output_video: str) -> None:
    """FFmpeg로 영상과 오디오를 합칩니다."""
    (
        ffmpeg.output(
            ffmpeg.input(temp_video),
            ffmpeg.input(temp_audio),
            output_video,
            vcodec="copy",
            acodec="aac",
            shortest=None,
        )
        .overwrite_output()
        .run()
    )


# === 메인 파이프라인 ===
def run() -> None:
    """전체 캡션 + TTS 파이프라인을 실행합니다."""
    args = parse_args()
    video_path = args.video_path or find_latest_video()
    if not video_path:
        raise FileNotFoundError("No input video found. Pass a path or create z_*.mp4 / record_*.mp4.")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    stem = os.path.splitext(os.path.basename(video_path))[0]
    output_video = f"captioned_{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    temp_audio = "temp_audio.mp3"
    font = load_font(args.font_path, args.font_size)

    temp_video, captions = generate_captioned_video(
        video_path=video_path,
        frame_interval=args.frame_interval,
        font=font,
    )

    # 요약 TTS 생성
    unique_captions = list(dict.fromkeys(captions))
    summary = ". ".join(unique_captions).replace("Scene:", "").strip()
    if not summary:
        summary = "No scene summary could be generated."
    tts = gTTS(f"{summary}.", lang=args.tts_lang)
    tts.save(temp_audio)
    print(f"[INFO] tts summary: {summary}")

    merge_audio_video(temp_video, temp_audio, output_video)

    # 임시 파일 정리
    for tmp in (temp_video, temp_audio):
        if os.path.exists(tmp):
            os.remove(tmp)

    print(f"[DONE] {output_video}")


# === 진입점 ===
if __name__ == "__main__":
    run()
