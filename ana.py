import argparse
import os
from datetime import datetime
from glob import glob

import cv2
import ffmpeg
import numpy as np
import torch
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from transformers import BlipForConditionalGeneration, BlipProcessor


def parse_args():
    parser = argparse.ArgumentParser(description="Video caption + TTS pipeline.")
    parser.add_argument("video_path", nargs="?", help="Input mp4 path")
    parser.add_argument("--frame-interval", type=float, default=2.0, help="Seconds per caption sample")
    parser.add_argument("--font-path", default="malgun.ttf", help="Font file for subtitle text")
    parser.add_argument("--font-size", type=int, default=32, help="Subtitle font size")
    parser.add_argument("--tts-lang", default="ko", help="gTTS language code")
    return parser.parse_args()


def find_latest_video():
    candidates = sorted(
        glob("z_*.mp4") + glob("record_*.mp4"),
        key=os.path.getmtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_font(font_path, font_size):
    try:
        return ImageFont.truetype(font_path, font_size)
    except OSError:
        print(f"[WARN] Font not found: {font_path}. Falling back to default font.")
        return ImageFont.load_default()


def generate_captioned_video(video_path, frame_interval, font):
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
        frame_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
        count += 1

    cap.release()
    out.release()
    return temp_video, captions


def merge_audio_video(temp_video, temp_audio, output_video):
    video_stream = ffmpeg.input(temp_video)
    audio_stream = ffmpeg.input(temp_audio)
    (
        ffmpeg.output(
            video_stream,
            audio_stream,
            output_video,
            vcodec="copy",
            acodec="aac",
            shortest=None,
        )
        .overwrite_output()
        .run()
    )


def run():
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

    unique_captions = list(dict.fromkeys(captions))
    summary = ". ".join(unique_captions).replace("Scene:", "").strip()
    if not summary:
        summary = "No scene summary could be generated."
    tts = gTTS(f"{summary}.", lang=args.tts_lang)
    tts.save(temp_audio)
    print(f"[INFO] tts summary: {summary}")

    merge_audio_video(temp_video, temp_audio, output_video)

    if os.path.exists(temp_video):
        os.remove(temp_video)
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    print(f"[DONE] {output_video}")


if __name__ == "__main__":
    run()
