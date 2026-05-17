import json
import subprocess

MP4_IN = "1.mp4"
MP3_IN = "1.mp3"
MP4_OUT = "2.mp4"

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed:\n{' '.join(cmd)}\n\nSTDERR:\n{p.stderr}")
    return p.stdout

def get_duration_seconds(path: str) -> float:
    out = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        path
    ])
    data = json.loads(out)
    return float(data["format"]["duration"])

def main():
    v_dur = get_duration_seconds(MP4_IN)
    a_dur = get_duration_seconds(MP3_IN)

    common = ["ffmpeg", "-y"]

    # MP3 길이에 맞춰 비디오를 반복(길면) 또는 트림(짧으면)
    if a_dur > v_dur:
        cmd = common + [
            "-stream_loop", "-1", "-i", MP4_IN,  # 비디오 무한 반복
            "-i", MP3_IN,                        # 새 오디오
            "-t", f"{a_dur:.6f}",                # 오디오 길이만큼 결과 길이 고정
            "-map", "0:v:0",                     # 원본 비디오만
            "-map", "1:a:0",                     # mp3 오디오만
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",                       # mp4 호환성 좋게 AAC 권장
            "-b:a", "192k",
            "-movflags", "+faststart",
            MP4_OUT
        ]
    else:
        cmd = common + [
            "-i", MP4_IN,
            "-i", MP3_IN,
            "-t", f"{a_dur:.6f}",                # 비디오를 오디오 길이만큼 자름
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            MP4_OUT
        ]

    print("Running:", " ".join(cmd))
    run(cmd)
    print(f"✅ Done: {MP4_OUT}")

if __name__ == "__main__":
    main()
