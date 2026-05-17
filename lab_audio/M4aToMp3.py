from pydub import AudioSegment
from pathlib import Path

src = Path("1.m4a")
dst = src.with_suffix(".mp3")

audio = AudioSegment.from_file(src, format="m4a")
audio.export(dst, format="mp3", bitrate="192k")

print("OK:", dst)
