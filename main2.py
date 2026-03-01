import os
import subprocess
import sys
import time
from glob import glob


def find_latest_video():
    patterns = ["z_*.mp4", "record_*.mp4"]
    candidates = []
    for pattern in patterns:
        candidates.extend(glob(pattern))
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0] if candidates else None


print("[INFO] launching cap.py...")
cap_process = subprocess.Popen([sys.executable, "cap.py"])

cap_process.wait()
print("[INFO] cap.py finished. waiting 2 seconds for file flush...")
time.sleep(2)

latest_video = find_latest_video()
if not latest_video:
    print("[ERROR] no recorded mp4 found.")
    sys.exit(1)

print(f"[INFO] analyzing: {latest_video}")
subprocess.run([sys.executable, "ana.py", latest_video], check=False)

print("[DONE] pipeline finished.")
