import os
import re
import time
import argparse
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build

from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드

api_key = os.getenv("YT_API_KEY")

def iso8601_duration_to_seconds(dur: str) -> int:
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur or "")
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mm = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mm * 60 + s

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def utc_rfc3339_days_ago(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def unique_keep_order(items):
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="최근 N일 (기본: 7)")
    parser.add_argument("--region", default="KR", help="regionCode (기본: KR)")
    parser.add_argument("--lang", default="ko", help="relevanceLanguage (기본: ko)")
    parser.add_argument("--pages_per_query", type=int, default=2, help="키워드당 페이지 수 (기본: 2)")
    parser.add_argument("--max_like", type=int, default=10, help="최대 좋아요 수 (기본: 10)")
    parser.add_argument("--max_seconds", type=int, default=60, help="최대 길이(초) (기본: 60)")
    parser.add_argument("--sleep", type=float, default=0.25, help="API 호출 딜레이(초) (기본: 0.25)")
    parser.add_argument("--limit", type=int, default=30, help="TXT에 저장할 최대 개수 (기본: 30)")
    args = parser.parse_args()

    if not api_key:
        raise SystemExit("환경변수 YT_API_KEY에 YouTube Data API Key를 설정하세요.")

    yt = build("youtube", "v3", developerKey=api_key)

    base_queries = [
        "AI", "인공지능", "생성형 AI", "챗GPT", "ChatGPT", "GPT", "LLM",
        "대규모 언어모델", "머신러닝", "딥러닝", "AI 툴", "AI 도구", "AI 뉴스", "AI 트렌드",
    ]

    published_after = utc_rfc3339_days_ago(args.days)
    search_queries = [f'{q} (shorts OR "#shorts")' for q in base_queries]

    video_ids = []
    for q in search_queries:
        next_token = None
        for _ in range(args.pages_per_query):
            resp = yt.search().list(
                part="id", q=q, type="video", maxResults=50, order="date",
                regionCode=args.region, relevanceLanguage=args.lang,
                publishedAfter=published_after, pageToken=next_token
            ).execute()

            for item in resp.get("items", []):
                vid = item.get("id", {}).get("videoId")
                if vid:
                    video_ids.append(vid)

            next_token = resp.get("nextPageToken")
            if not next_token:
                break
            time.sleep(args.sleep)
        time.sleep(args.sleep)

    video_ids = unique_keep_order(video_ids)
    if not video_ids:
        raise SystemExit("검색 결과가 없습니다.")

    matches = []
    unknown_like = 0

    for batch in chunks(video_ids, 50):
        resp = yt.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(batch),
            maxResults=50
        ).execute()

        for item in resp.get("items", []):
            vid = item["id"]
            title = item.get("snippet", {}).get("title", "")
            dur = item.get("contentDetails", {}).get("duration", "")
            secs = iso8601_duration_to_seconds(dur)

            like_raw = item.get("statistics", {}).get("likeCount")
            if like_raw is None:
                unknown_like += 1
                continue

            likes = int(like_raw)

            if secs <= args.max_seconds and likes <= args.max_like:
                url = f"https://www.youtube.com/shorts/{vid}"
                matches.append((likes, secs, title, url))

        time.sleep(args.sleep)

    matches.sort(key=lambda x: (x[0], x[1]))
    matches = matches[:args.limit]  # 상위 30개 제한

    # TXT 파일 저장
    filename = "youtube_shorts_links.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"[YouTube Shorts 링크 목록 - 최근 {args.days}일, 좋아요 ≤{args.max_like}, 길이 ≤{args.max_seconds}s | 상위 {len(matches)}개]\n\n")
        for i, (likes, secs, title, url) in enumerate(matches, 1):
            f.write(f"{i:02d}. 👍{likes:>3} | {secs:>2}s | {title}\n")
            f.write(f"    {url}\n\n")

    print(f"\n✅ {filename} 파일에 {len(matches)}개 링크 저장 완료.")
    if unknown_like:
        print(f"⚠️ 좋아요 수 미제공으로 제외: {unknown_like}개")

if __name__ == "__main__":
    main()