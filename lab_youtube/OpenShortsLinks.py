import webbrowser
import time

filename = "youtube_shorts_links.txt"

try:
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
except FileNotFoundError:
    raise SystemExit(f"{filename} 파일을 찾을 수 없습니다. 먼저 목록 생성 스크립트를 실행하세요.")

urls = [
    line.strip()
    for line in lines
    if line.strip().startswith("https://www.youtube.com/shorts/")
]

if not urls:
    raise SystemExit("TXT 파일에 유효한 URL이 없습니다.")

# ✅ 탭 열기 간격(초) — 너무 짧으면 브라우저가 팝업/탭 오픈을 제한할 수 있음
OPEN_DELAY_SEC = 0.7

print(f"{len(urls)}개의 Shorts를 Enter 없이 순차 오픈합니다.")
print(f"탭 오픈 간격: {OPEN_DELAY_SEC}s\n")
time.sleep(1)

for i, url in enumerate(urls, 1):
    print(f"{i:02d}. 열리는 중: {url}")
    webbrowser.open_new_tab(url)
    time.sleep(OPEN_DELAY_SEC)

print("\n✅ 완료: 모든 Shorts 탭을 열었습니다.")
