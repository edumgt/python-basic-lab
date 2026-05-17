import os
import subprocess

def merge_videos(video_files, output_file):
    """
    여러 MP4 파일을 concat 방식으로 병합합니다.

    :param video_files: 병합할 파일들의 리스트
    :param output_file: 병합된 출력 파일명
    """
    # 1. 파일 목록을 임시 텍스트로 저장
    list_filename = "file_list.txt"
    with open(list_filename, 'w', encoding='utf-8') as f:
        for file in video_files:
            f.write(f"file '{os.path.abspath(file)}'\n")

    # 2. ffmpeg 명령 실행 (concat demuxer 방식)
    try:
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", list_filename,
            "-c", "copy",
            output_file
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ 병합 완료: {output_file}")
    except subprocess.CalledProcessError as e:
        print("❌ ffmpeg 실행 오류:", e)
    finally:
        # 3. 임시 파일 삭제
        if os.path.exists(list_filename):
            os.remove(list_filename)

if __name__ == "__main__":
    # 예시 파일 목록
    input_files = ["1.mp4", "2.mp4"]
    output = "merged_output.mp4"
    merge_videos(input_files, output)
