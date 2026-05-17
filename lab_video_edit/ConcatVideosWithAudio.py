import subprocess
import os
import math

# 1. 영상 병합용 리스트 파일 생성
mp4_list = [f"sample{i}.mp4" for i in range(1, 10)]
concat_list_path = "concat_list.txt"

with open(concat_list_path, "w") as f:
    for file in mp4_list:
        f.write(f"file '{file}'\n")

# 2. 영상 이어붙이기
intermediate_video = "merged_video.mp4"
merge_command = [
    "ffmpeg",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_list_path,
    "-c", "copy",
    intermediate_video
]

print("🎞️ MP4 영상 병합 중...")
try:
    subprocess.run(merge_command, check=True)
    print(f"✅ 영상 병합 완료: {intermediate_video}")
except subprocess.CalledProcessError as e:
    print("❌ 영상 병합 실패:", e)
    exit(1)

# 3. 길이 측정 함수
def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout.decode().strip())

# 4. 반복 횟수 계산
mp3_file = "back.mp3"
video_duration = get_duration(intermediate_video)
audio_duration = get_duration(mp3_file)

repeat_count = math.ceil(audio_duration / video_duration)
print(f"🔁 MP4 반복 횟수: {repeat_count} (mp3: {audio_duration:.2f}s / mp4: {video_duration:.2f}s)")

# 5. 반복 리스트 생성
repeat_list_path = "repeat_list.txt"
with open(repeat_list_path, "w") as f:
    for _ in range(repeat_count):
        f.write(f"file '{intermediate_video}'\n")

# 6. 반복된 영상 병합
looped_video = "looped_video.mp4"
repeat_command = [
    "ffmpeg",
    "-f", "concat",
    "-safe", "0",
    "-i", repeat_list_path,
    "-c", "copy",
    looped_video
]

print("🔁 반복 영상 생성 중...")
try:
    subprocess.run(repeat_command, check=True)
    print(f"✅ 반복 영상 생성 완료: {looped_video}")
except subprocess.CalledProcessError as e:
    print("❌ 반복 영상 생성 실패:", e)
    exit(1)

# 7. 오디오 병합
final_output = "final_output.mp4"
audio_merge_command = [
    "ffmpeg",
    "-i", looped_video,
    "-i", mp3_file,
    "-c:v", "copy",
    "-c:a", "aac",
    "-shortest",
    final_output
]

print("🔊 오디오 병합 중...")
try:
    subprocess.run(audio_merge_command, check=True)
    print(f"🎉 최종 결과 저장 완료: {final_output}")
except subprocess.CalledProcessError as e:
    print("❌ 오디오 병합 실패:", e)

# 8. 중간 파일 정리
os.remove(concat_list_path)
os.remove(repeat_list_path)
os.remove(intermediate_video)
os.remove(looped_video)
