import subprocess
import os

input_audio = "back.mp3"
input_folder = "champmp4"
output_suffix = "_0613.mp4"

# MP3 길이 구하기
def get_audio_duration(audio_file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    try:
        duration = float(result.stdout.decode().strip())
        return duration
    except ValueError:
        print("❌ MP3 길이를 읽을 수 없습니다.")
        return None

# mp3 길이 가져오기
audio_duration = get_audio_duration(input_audio)
if audio_duration is None:
    exit()


for filename in os.listdir(input_folder):
    if filename.endswith(".mp4"):
        input_video_path = os.path.join(input_folder, filename)
        base_name = os.path.splitext(filename)[0]
        output_video = os.path.join(input_folder, f"{base_name}{output_suffix}")

        print(f"🎞️ {input_video_path} + {input_audio} → {output_video}")

        command = [
            "ffmpeg",
            "-y",                         # 기존 파일 덮어쓰기
            "-stream_loop", "-1",         # 영상 반복
            "-i", input_video_path,
            "-i", input_audio,
            "-t", str(audio_duration),    # mp3 길이만큼 자르기
            "-c:v", "copy",               # 비디오 코덱 그대로 복사
            "-c:a", "aac",                # 오디오 코덱 설정
            output_video
        ]

        try:
            subprocess.run(command, check=True)
            print(f"✅ 생성 완료: {output_video}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 오류 발생: {input_video_path} 처리 중 실패\n{e}")
