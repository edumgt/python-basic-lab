import subprocess
import time
import os
from glob import glob

# 1. cap.py 실행 (별도 프로세스로)
print("🎬 cap.py 실행 중...")
cap_process = subprocess.Popen(["python", "cap.py"])

# 2. cap.py가 종료될 때까지 대기
cap_process.wait()
print("✅ cap.py 종료됨. 10초 대기 중...")
time.sleep(10)

# 3. 가장 최근에 생성된 mp4 파일 탐색
video_files = sorted(glob("record_*.mp4"), key=os.path.getmtime, reverse=True)
if not video_files:
    print("⚠️ 녹화된 mp4 파일이 없습니다.")
    exit(1)

latest_video = video_files[0]
print(f"📂 분석 대상 파일: {latest_video}")

# 4. ana.py 실행 (입력 파일명을 인자로 전달)
print("🧠 ana.py 실행 중...")
subprocess.run(["python", "ana.py", latest_video])

print("🎉 전체 분석 완료")
