import subprocess

def blend_with_overlay(input_path, overlay_path, output_path):
    filter_complex = (
        "[1:v]crop=480:854:(in_w-480)/2:(in_h-854)/2,"
        "format=rgba,colorchannelmixer=aa=0.5[ov];"
        "[0:v]format=rgba[base];"
        "[base][ov]overlay=format=auto:shortest=1[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-stream_loop", "-1", "-i", overlay_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "copy",
        "-preset", "fast",
        "-crf", "22",
        "-shortest",
        output_path
    ]

    subprocess.run(cmd, check=True)

# 사용 예
blend_with_overlay("1.mp4", "2.mp4", "3.mp4")
