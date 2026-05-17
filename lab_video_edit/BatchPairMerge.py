import os
import subprocess

# 경로 설정
input_folder = "javamp3"
output_prefix = "Cloud_"

# 오디오 길이 구하기
def get_audio_duration(audio_file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

# text 폴더 내 파일 리스트 가져오기
files = os.listdir(input_folder)

# 파일 이름 기준 분리
mp4_files = [f for f in files if f.endswith(".mp4")]
mp3_files = [f for f in files if f.endswith(".mp3")]

# 공통 이름 추출
common_names = set(os.path.splitext(f)[0] for f in mp4_files) & set(os.path.splitext(f)[0] for f in mp3_files)

# 병합 처리
for name in common_names:
    input_video = os.path.join(input_folder, f"{name}.mp4")
    input_audio = os.path.join(input_folder, f"{name}.mp3")
    output_video = os.path.join(input_folder, f"{output_prefix}{name}.mp4")

    try:
        audio_duration = get_audio_duration(input_audio)
        print(f"🎵 [{name}] mp3 길이: {audio_duration:.2f}초")

        command = [
            "ffmpeg",
            "-stream_loop", "-1",
            "-i", input_video,
            "-i", input_audio,
            "-t", str(audio_duration),
            "-c:v", "copy",
            "-c:a", "aac",
            output_video
        ]

        subprocess.run(command, check=True)
        print(f"✅ 병합 완료: {output_video}")

    except Exception as e:
        print(f"❌ [{name}] 병합 실패: {e}")
