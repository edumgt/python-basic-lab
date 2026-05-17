# pip install -U moviepy

from moviepy import VideoFileClip, concatenate_videoclips

def cut(clip, start, end):
    # moviepy 버전에 따라 subclip / subclipped 지원이 다를 수 있어 둘 다 대응
    if hasattr(clip, "subclip"):
        return clip.subclip(start, end)
    return clip.subclipped(start, end)

def main():
    clip2 = VideoFileClip("2.mp4")
    clip1 = VideoFileClip("1.mp4")

    # 2.mp4 앞 8초
    t2_end = min(8, clip2.duration)
    part2 = cut(clip2, 0, t2_end)

    # 1.mp4 뒤 8초
    t1_start = max(0, clip1.duration - 8)
    part1 = cut(clip1, t1_start, clip1.duration)

    final = concatenate_videoclips([part2, part1], method="compose")
    final.write_videofile("out.mp4", codec="libx264", audio_codec="aac")

    clip2.close(); clip1.close(); final.close()

if __name__ == "__main__":
    main()
