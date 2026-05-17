import ffmpeg
import datetime

def prompt_and_cut():
    # 사용자 입력
    input_file = input("원본 파일 경로를 입력하세요 (예: input.mp4): ").strip()
    output_file = input("저장할 파일명을 입력하세요 (예: output.mp4): ").strip()
    start_time = input("시작 시간 (예: 00:00:10 또는 10): ").strip()
    end_time = input("종료 시간 (예: 00:00:30 또는 30): ").strip()

    # 시간 처리
    try:
        # 시간 문자열인 경우 계산
        if ":" in start_time and ":" in end_time:
            fmt = "%H:%M:%S"
            t1 = datetime.datetime.strptime(start_time, fmt)
            t2 = datetime.datetime.strptime(end_time, fmt)
            duration = (t2 - t1).total_seconds()
        else:
            # 숫자로 들어온 경우
            start_time = float(start_time)
            end_time = float(end_time)
            duration = end_time - start_time

        if duration <= 0:
            print("❌ 종료 시간은 시작 시간보다 커야 합니다.")
            return

        # ffmpeg 실행
        (
            ffmpeg
            .input(input_file, ss=start_time)
            .output(output_file, t=duration, codec='copy')
            .overwrite_output()
            .run()
        )

        print(f"✅ 성공적으로 저장되었습니다: {output_file}")

    except Exception as e:
        print("❌ 에러 발생:", e)

if __name__ == "__main__":
    prompt_and_cut()
