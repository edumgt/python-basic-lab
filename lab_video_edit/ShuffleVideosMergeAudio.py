import subprocess
import os
import random

# 입력 파일 설정
mp4_files = ["1.mp4", "2.mp4", "3.mp4"]   # 합칠 MP4 파일 목록 (원하는 대로 수정)
input_audio = "back.mp3"                    # 합칠 MP3 오디오
output_video = "output_shuffled.mp4"        # 최종 출력 파일명

# Step 1: mp4 순서 랜덤 섞기
random.shuffle(mp4_files)
print(f"✅ 랜덤 섞은 순서: {mp4_files}")

# Step 2: concat용 텍스트 파일 만들기
concat_list = "videos_to_concat.txt"
with open(concat_list, "w") as f:
    for mp4_file in mp4_files:
        f.write(f"file '{os.path.abspath(mp4_file)}'\n")

# Step 3: mp4들 합친 임시 파일 생성
temp_merged_video = "merged_temp.mp4"
concat_command = [
    "ffmpeg",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_list,
    "-c", "copy",
    temp_merged_video
]

try:
    subprocess.run(concat_command, check=True)
    print(f"✅ mp4 합치기 완료 → {temp_merged_video}")
except subprocess.CalledProcessError as e:
    print("❌ mp4 합치기 중 오류 발생:", e)
    exit(1)

# Step 4: mp3 길이 가져오기
def get_audio_duration(audio_file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    duration = float(result.stdout)
    return duration

audio_duration = get_audio_duration(input_audio)
print(f"✅ mp3 길이 (초): {audio_duration}")

# Step 5: mp4 + mp3 합치기 (mp3 길이에 맞춰 잘라내기, 필요 시 mp4 반복)
final_command = [
    "ffmpeg",
    "-stream_loop", "-1",
    "-i", temp_merged_video,
    "-i", input_audio,
    "-t", str(audio_duration),
    "-c:v", "copy",
    "-c:a", "aac",
    output_video
]

try:
    subprocess.run(final_command, check=True)
    print(f"✅ 최종 mp4 + mp3 합치기 완료! 결과: {output_video}")
except subprocess.CalledProcessError as e:
    print("❌ 최종 합치기 중 오류 발생:", e)
    exit(1)

# Step 6: 임시 파일 정리
os.remove(concat_list)
os.remove(temp_merged_video)
print("🧹 임시 파일 정리 완료")
