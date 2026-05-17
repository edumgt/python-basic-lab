import subprocess

# 파일 경로 설정
video_file = "final_output.mp4"
bgm_file = "1.mp3"
output_file = "output_with_bgm.mp4"

# BGM 볼륨 비율 (0.0 ~ 1.0): 낮을수록 배경음이 작아짐
bgm_volume = 0.3

# FFmpeg 명령 구성
command = [
    "ffmpeg",
    "-i", video_file,
    "-i", bgm_file,
    "-filter_complex",
    f"[1:a]volume={bgm_volume}[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=3",
    "-c:v", "copy",
    "-c:a", "aac",
    "-strict", "experimental",
    output_file
]

try:
    subprocess.run(command, check=True)
    print(f"✅ 배경음 믹싱 완료: {output_file}")
except subprocess.CalledProcessError as e:
    print("❌ ffmpeg 실행 오류:", e)
