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

from __future__ import annotations  # 최신 타입 힌트 문법을 안전하게 사용합니다.

import argparse  # CLI 인자 파싱을 담당합니다.
import os  # 파일 존재 확인과 경로 처리에 사용합니다.
from datetime import datetime  # 출력 파일명 타임스탬프 생성에 사용합니다.
from glob import glob  # 패턴 기반으로 최신 영상 파일을 탐색합니다.
from typing import Any  # 폰트 객체 등 유연한 타입 힌트가 필요한 곳에 사용합니다.

import cv2  # 영상 읽기/쓰기와 색상 변환에 사용합니다.
import ffmpeg  # 영상+오디오 합성 명령을 파이썬으로 구성합니다.
import numpy as np  # PIL 이미지를 OpenCV 배열로 변환합니다.
import torch  # GPU 사용 가능 여부 확인 및 모델 디바이스 이동에 사용합니다.
from gtts import gTTS  # 요약 텍스트를 음성(mp3)으로 합성합니다.
from PIL import Image, ImageDraw, ImageFont  # 자막 텍스트 렌더링을 위해 PIL 도구를 사용합니다.
from transformers import BlipForConditionalGeneration, BlipProcessor  # BLIP 캡션 생성 모델과 전처리기를 로드합니다.


# === 인자 파싱 ===
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Video caption + TTS pipeline.")  # 프로그램 설명이 포함된 인자 파서를 생성합니다.
    parser.add_argument("video_path", nargs="?", help="Input mp4 path")  # 선택 인자로 입력 영상 경로를 받습니다.
    parser.add_argument("--frame-interval", type=float, default=2.0, help="Seconds per caption sample")  # 캡션을 갱신할 프레임 샘플 간격(초)을 받습니다.
    parser.add_argument("--font-path", default="malgun.ttf", help="Font file for subtitle text")  # 자막 폰트 파일 경로를 받습니다.
    parser.add_argument("--font-size", type=int, default=32, help="Subtitle font size")  # 자막 폰트 크기를 받습니다.
    parser.add_argument("--tts-lang", default="ko", help="gTTS language code")  # TTS 언어 코드를 받습니다.
    return parser.parse_args()  # 파싱된 인자 네임스페이스를 반환합니다.


# === 유틸 함수 ===
def find_latest_video() -> str | None:
    """현재 디렉터리에서 가장 최근 z_*.mp4 또는 record_*.mp4를 반환합니다."""
    candidates = sorted(  # 두 패턴의 파일 목록을 수정 시간 기준으로 정렬합니다.
        glob("z_*.mp4") + glob("record_*.mp4"),  # 두 가지 녹화 파일명 패턴을 모두 후보에 포함합니다.
        key=os.path.getmtime,  # 파일 수정 시간을 정렬 기준으로 사용합니다.
        reverse=True,  # 가장 최근 파일이 앞에 오도록 내림차순 정렬합니다.
    )
    return candidates[0] if candidates else None  # 후보가 있으면 최신 파일을 반환하고 없으면 None을 반환합니다.


def load_font(font_path: str, font_size: int) -> Any:
    """폰트를 로드합니다. 실패 시 기본 폰트를 사용합니다."""
    try:  # 지정한 폰트 파일이 존재하는 정상 경로를 먼저 시도합니다.
        return ImageFont.truetype(font_path, font_size)  # 사용자 지정 폰트를 크기와 함께 로드합니다.
    except OSError:  # 폰트 파일이 없거나 손상된 경우 예외가 발생합니다.
        print(f"[WARN] Font not found: {font_path}. Falling back to default font.")  # 폴백 발생 사실을 경고로 알립니다.
        return ImageFont.load_default()  # PIL 기본 폰트를 로드해 파이프라인이 계속 동작하도록 합니다.


# === 캡션 생성 + 자막 삽입 ===
def generate_captioned_video(
    video_path: str, frame_interval: float, font: Any
) -> tuple[str, list[str]]:
    """
    BLIP 모델로 영상 장면을 캡션하고 자막이 삽입된 임시 영상을 생성합니다.
    반환값: (임시 영상 경로, 캡션 리스트)
    """
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")  # 이미지 전처리/토큰 변환을 담당하는 BLIP 프로세서를 로드합니다.
    model = BlipForConditionalGeneration.from_pretrained(  # 캡션 문장을 생성하는 BLIP 모델 가중치를 로드합니다.
        "Salesforce/blip-image-captioning-base"
    ).to("cuda" if torch.cuda.is_available() else "cpu")  # GPU가 가능하면 CUDA로, 아니면 CPU로 모델을 이동합니다.

    temp_video = "temp_video.mp4"  # 자막이 합성된 중간 영상 파일명을 고정합니다.
    cap = cv2.VideoCapture(video_path)  # 입력 영상을 열어 프레임 단위로 읽습니다.
    fps = cap.get(cv2.CAP_PROP_FPS) or 24  # 원본 FPS를 읽고 실패 시 24fps를 기본값으로 사용합니다.
    frame_gap = max(1, int(fps * frame_interval))  # 캡션 재생성을 위한 프레임 간격을 계산하되 최소 1프레임으로 보정합니다.
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # 입력 영상 가로 해상도를 읽습니다.
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 입력 영상 세로 해상도를 읽습니다.
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # 임시 출력 영상 코덱 식별자를 생성합니다.
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))  # 원본과 동일한 해상도/FPS로 임시 영상 writer를 엽니다.

    captions = []  # 샘플링 시점마다 생성된 캡션 텍스트를 누적 저장합니다.
    count = 0  # 현재까지 처리한 프레임 인덱스를 추적합니다.
    current_caption = ""  # 최근 생성된 캡션을 프레임 사이에서 재사용합니다.

    print("[INFO] generating captions...")  # 캡션 생성 루프 시작을 로그로 알립니다.
    while True:  # 영상 끝까지 프레임을 반복 처리합니다.
        ret, frame = cap.read()  # 다음 프레임을 읽고 성공 여부를 함께 받습니다.
        if not ret:  # 더 이상 프레임이 없으면 루프를 종료합니다.
            break

        if count % frame_gap == 0:  # 샘플링 간격에 도달한 프레임에서만 새 캡션을 생성합니다.
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # OpenCV BGR 프레임을 모델 입력용 RGB로 변환합니다.
            inputs = processor(images=rgb, return_tensors="pt").to(model.device)  # 프레임 이미지를 모델이 사용하는 디바이스 텐서로 변환합니다.
            out_ids = model.generate(**inputs)  # BLIP 모델로 캡션 토큰 시퀀스를 생성합니다.
            caption_en = processor.decode(out_ids[0], skip_special_tokens=True)  # 생성 토큰을 사람이 읽을 수 있는 문자열로 디코딩합니다.
            current_caption = f"Scene: {caption_en}"  # 자막 표시 형식에 맞춰 현재 캡션 문자열을 구성합니다.
            captions.append(current_caption)  # 최종 요약 TTS 생성을 위해 캡션을 목록에 저장합니다.

        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # 프레임을 PIL 이미지로 변환해 텍스트 렌더링 준비를 합니다.
        draw = ImageDraw.Draw(img_pil)  # PIL 이미지 위에 글자를 그릴 드로우 객체를 생성합니다.
        draw.text((40, height - 80), current_caption, font=font, fill=(255, 255, 255))  # 화면 하단 좌측에 현재 캡션을 흰색으로 그립니다.
        out.write(cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR))  # 자막이 그려진 PIL 이미지를 다시 OpenCV BGR로 바꿔 출력 영상에 기록합니다.
        count += 1  # 다음 프레임 처리를 위해 카운터를 증가시킵니다.

    cap.release()  # 입력 비디오 캡처 핸들을 닫아 리소스를 해제합니다.
    out.release()  # 임시 출력 비디오 writer를 닫아 파일 저장을 완료합니다.
    return temp_video, captions  # 후속 단계가 사용할 임시 영상 경로와 캡션 목록을 반환합니다.


# === 오디오 + 영상 합성 ===
def merge_audio_video(temp_video: str, temp_audio: str, output_video: str) -> None:
    """FFmpeg로 영상과 오디오를 합칩니다."""
    (
        ffmpeg.output(  # ffmpeg 입력 스트림들을 결합해 출력 스트림을 정의합니다.
            ffmpeg.input(temp_video),  # 자막이 삽입된 임시 영상을 첫 입력으로 사용합니다.
            ffmpeg.input(temp_audio),  # TTS로 생성한 임시 오디오를 두 번째 입력으로 사용합니다.
            output_video,  # 최종 출력 파일명을 지정합니다.
            vcodec="copy",  # 영상 스트림은 재인코딩 없이 복사해 속도와 화질을 유지합니다.
            acodec="aac",  # 오디오 스트림은 AAC로 인코딩해 호환성을 높입니다.
            shortest=None,  # 더 짧은 스트림 길이에 맞춰 출력 길이를 자동 조정합니다.
        )
        .overwrite_output()  # 기존 동일 파일이 있으면 덮어쓰도록 설정합니다.
        .run()  # 구성한 ffmpeg 파이프라인을 실제로 실행합니다.
    )


# === 메인 파이프라인 ===
def run() -> None:
    """전체 캡션 + TTS 파이프라인을 실행합니다."""
    args = parse_args()  # CLI 인자를 파싱해 실행 설정을 가져옵니다.
    video_path = args.video_path or find_latest_video()  # 사용자 입력 경로가 없으면 최신 녹화 파일을 자동 탐색합니다.
    if not video_path:  # 자동 탐색 포함해서도 입력 영상을 찾지 못한 경우입니다.
        raise FileNotFoundError("No input video found. Pass a path or create z_*.mp4 / record_*.mp4.")  # 명확한 에러 메시지로 실패 원인을 전달합니다.
    if not os.path.exists(video_path):  # 전달된 경로의 파일이 실제로 존재하는지 검증합니다.
        raise FileNotFoundError(f"Video not found: {video_path}")  # 잘못된 경로인 경우 즉시 예외를 발생시킵니다.

    stem = os.path.splitext(os.path.basename(video_path))[0]  # 입력 파일의 확장자를 제외한 이름(stem)을 추출합니다.
    output_video = f"captioned_{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"  # 결과 파일명을 입력 stem+현재 시각 기반으로 생성합니다.
    temp_audio = "temp_audio.mp3"  # TTS 중간 산출물 파일명을 고정합니다.
    font = load_font(args.font_path, args.font_size)  # 사용자 지정 또는 기본 폰트를 로드합니다.

    temp_video, captions = generate_captioned_video(  # 캡션 생성과 자막 삽입을 수행해 중간 영상과 캡션 목록을 얻습니다.
        video_path=video_path,
        frame_interval=args.frame_interval,
        font=font,
    )

    unique_captions = list(dict.fromkeys(captions))  # 중복 캡션을 제거하되 등장 순서는 유지합니다.
    summary = ". ".join(unique_captions).replace("Scene:", "").strip()  # 캡션들을 하나의 문장 요약 텍스트로 합칩니다.
    if not summary:  # 캡션이 비어 요약 텍스트가 생성되지 않은 경우입니다.
        summary = "No scene summary could be generated."  # TTS 실패를 막기 위한 기본 문장을 사용합니다.
    tts = gTTS(f"{summary}.", lang=args.tts_lang)  # 요약 문장을 선택 언어로 음성 합성합니다.
    tts.save(temp_audio)  # 생성된 음성을 임시 mp3 파일로 저장합니다.
    print(f"[INFO] tts summary: {summary}")  # 어떤 요약 문장이 음성화되었는지 로그로 확인합니다.

    merge_audio_video(temp_video, temp_audio, output_video)  # 자막 영상과 TTS 오디오를 합쳐 최종 결과물을 생성합니다.

    for tmp in (temp_video, temp_audio):  # 중간 산출물 파일들을 순회합니다.
        if os.path.exists(tmp):  # 파일이 실제로 존재할 때만 삭제를 시도합니다.
            os.remove(tmp)  # 임시 파일을 제거해 작업 디렉터리를 정리합니다.

    print(f"[DONE] {output_video}")  # 최종 결과 파일명을 사용자에게 출력합니다.


# === 진입점 ===
if __name__ == "__main__":  # 파일이 직접 실행될 때만 파이프라인을 시작합니다.
    run()  # 캡션 생성, TTS 합성, 영상 병합까지 전체 과정을 실행합니다.
