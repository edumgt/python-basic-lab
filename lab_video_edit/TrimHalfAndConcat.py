import subprocess
import os

start_num = 11
end_num = 19
trimmed_files = []
concat_list_filename = "concat_list.txt"
output_filename = "merged_half_clips.mp4"

# 1. 각 파일 절반부터 끝까지 잘라서 저장
for i in range(start_num, end_num + 1):
    input_file = f"{i}.mp4"
    output_file = f"trimmed_{i}.mp4"

    if not os.path.exists(input_file):
        print(f"⚠️ 파일 없음: {input_file}")
        continue

    # ffprobe 로 duration 구하기
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", input_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    duration = float(result.stdout.strip())
    start_time = duration / 2

    # ffmpeg 로 후반부 자르기
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_file,
        "-ss", str(start_time),
        "-c", "copy",  # re-encoding 없이 빠르게
        output_file
    ])

    trimmed_files.append(output_file)

# 2. concat용 텍스트 파일 생성
with open(concat_list_filename, "w") as f:
    for filename in trimmed_files:
        f.write(f"file '{filename}'\n")

# 3. ffmpeg concat 수행
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_list_filename,
    "-c", "copy",
    output_filename
])

print(f"✅ 최종 파일 생성 완료: {output_filename}")
