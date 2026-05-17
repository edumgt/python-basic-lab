import os
import random
import subprocess
from google.cloud import texttospeech
from pydub import AudioSegment

# Step 1: Google TTS 음성 생성
SERVICE_ACCOUNT_FILE = "my-project.json"
client = texttospeech.TextToSpeechClient.from_service_account_file(SERVICE_ACCOUNT_FILE)

voice_names = ["ko-KR-Wavenet-B"]
selected_voice = random.choice(voice_names)
print(f"🎙️ 선택된 목소리: {selected_voice}")

ssml_text = """
<speak> 지금, 조용히 눈을 감고 내 마음을 바라봅니다. <break time="2s"/> 한 번 깊게 숨을 들이마시며, <break time="2s"/> 내가 나에게, 그리고 세상에게 품었던 서운함을 떠올립니다. <break time="2s"/> 숨을 내쉴 때, 그 서운함과 상처를 천천히 놓아줍니다. <break time="2s"/> 나는 완벽하지 않았고, 다른 이들도 완벽하지 않았음을 인정합니다. <break time="2s"/> 내 심장은 용서의 따뜻한 울림으로 조용히 뛰고, <break time="2s"/> 내 마음은 그동안 움켜쥐었던 무거운 감정을 하나하나 풀어냅니다. <break time="2s"/> 이제 나는 나 자신을, 그리고 타인을 온전히 용서합니다. <break time="2s"/> 그 안에서, 마음은 고요한 호수처럼 잔잔해지고, <break time="2s"/> 나는 가벼워진 마음으로, 새로운 내일을 맞을 준비를 합니다. <break time="2s"/> </speak>
"""

voice = texttospeech.VoiceSelectionParams(
    language_code="ko-KR",
    name=selected_voice,
    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=0.78,
    pitch=-1.0,
    volume_gain_db=0.0
)

tts_output = "meditation_tts.mp3"
synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
response = client.synthesize_speech(
    input=synthesis_input, voice=voice, audio_config=audio_config
)

with open(tts_output, "wb") as out:
    out.write(response.audio_content)
    print(f"✅ 명상 음성 mp3 생성 완료: {tts_output}")

# Step 2: 배경 피아노 mp3 불러오기
piano_mp3 = "piano_four_finger_loop.mp3"
if not os.path.exists(piano_mp3):
    raise FileNotFoundError(f"⚠️ {piano_mp3} 파일을 먼저 생성해야 합니다!")

# Step 3: pydub로 두 mp3 로드
piano_audio = AudioSegment.from_mp3(piano_mp3)
tts_audio = AudioSegment.from_mp3(tts_output)

# Step 4: 길이 맞추기
if len(piano_audio) < len(tts_audio):
    repeat_count = int(len(tts_audio) / len(piano_audio)) + 1
    piano_audio = piano_audio * repeat_count
piano_audio = piano_audio[:len(tts_audio)]

# Step 5: 볼륨 조정
combined = piano_audio - 10  # 피아노 볼륨 낮춤
combined = combined.overlay(tts_audio)

# Step 6: 합성 mp3로 저장
base_output = "meditation_with_piano.mp3"
combined.export(base_output, format="mp3")
print(f"✅ 기본 합성 mp3 파일 생성 완료: {base_output}")

# Step 7: ffmpeg로 echo(메아리) 필터 적용
final_output = "sleep3.mp3"
ffmpeg_command = [
    "ffmpeg",
    "-y",
    "-i", base_output,
    "-af", "aecho=0.8:0.9:1000:0.08",
    final_output
]

subprocess.run(ffmpeg_command, check=True)
print(f"✅ 최종 동굴 메아리 효과 mp3 파일 생성 완료: {final_output}")
