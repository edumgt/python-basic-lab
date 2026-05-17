# mix.py - 1.mp4, 2.mp4, 3.mp4 를 2초씩 교차해서 mixed.mp4 생성

from moviepy import VideoFileClip, concatenate_videoclips

INPUT_FILES = ["1.mp4", "2.mp4", "3.mp4"]
SEGMENT_DURATION = 3.0
OUTPUT_FILE = "mixed.mp4"


def main():
    print("🎬 원본 파일 로드 중...")
    clips = []
    for f in INPUT_FILES:
        print(f"  - {f} 로드")
        clips.append(VideoFileClip(f))

    positions = [0.0 for _ in clips]
    segments = []

    print("✂️  교차 편집용 세그먼트 생성 중...")

    while True:
        all_done = True

        # 1 → 2 → 3 순서로 세그먼트 잘라 붙이기
        for idx, clip in enumerate(clips):
            start = positions[idx]

            # 아직 남은 구간이 있으면
            if start + 0.1 < clip.duration:
                all_done = False
                end = min(start + SEGMENT_DURATION, clip.duration)

                print(f"  - {INPUT_FILES[idx]}: {start:.2f}s ~ {end:.2f}s 추가")

                # ✅ MoviePy 2.x: subclipped 사용
                seg = clip.subclipped(start, end)
                segments.append(seg)

                positions[idx] = end

        if all_done:
            break

    if not segments:
        print("❌ 붙일 세그먼트가 없습니다.")
        return

    print(f"📽  총 {len(segments)}개의 세그먼트를 이어 붙이는 중...")

    final_clip = concatenate_videoclips(segments, method="compose")

    print(f"💾 결과 영상 저장: {OUTPUT_FILE}")
    final_clip.write_videofile(
        OUTPUT_FILE,
        codec="libx264",
        audio_codec="aac",
        fps=final_clip.fps or 30,
    )

    final_clip.close()
    for c in clips:
        c.close()

    print("✅ 완료!")


if __name__ == "__main__":
    main()
