import subprocess

# 파일 이름 설정
input_video = "record_20250607_150856.mp4"               # 원본 동영상
input_audio = "Java_Example9.mp3"               # 붙일 mp3 음성
output_video = "record_20250607_150856_01.mp4"             # 최종 결과 파일

# mp3 길이 구하기 (ffprobe 사용)
def get_audio_duration(audio_file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    duration = float(result.stdout)
    return duration

# mp3 길이 가져오기
audio_duration = get_audio_duration(input_audio)
print(f"✅ mp3 길이 (초): {audio_duration}")

# ffmpeg 명령어: mp4를 loop, mp3에 맞춰 자르기
command = [
    "ffmpeg",
    "-stream_loop", "-1",           # 무한 반복
    "-i", input_video,
    "-i", input_audio,
    "-t", str(audio_duration),      # mp3 길이만큼 출력
    "-c:v", "copy",
    "-c:a", "aac",
    output_video
]

# ffmpeg 실행
try:
    subprocess.run(command, check=True)
    print(f"✅ mp4 + mp3 합치기 완료! 결과: {output_video}")
except subprocess.CalledProcessError as e:
    print("❌ ffmpeg 실행 중 오류 발생:", e)
