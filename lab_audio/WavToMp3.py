from pydub import AudioSegment
import os

# 입력 WAV 파일 경로
input_wav = "smile.wav"

# 출력 MP3 파일 경로
output_mp3 = "smile.mp3"

# WAV 파일 로드
sound = AudioSegment.from_wav(input_wav)

# MP3로 내보내기
sound.export(output_mp3, format="mp3")

print(f"✅ 변환 완료: {output_mp3}")
