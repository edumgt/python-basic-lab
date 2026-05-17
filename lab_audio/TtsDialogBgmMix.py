from google.cloud import texttospeech
from pydub import AudioSegment
import os

# === 서비스 계정 경로 설정 ===
CREDENTIAL_PATH = "my-project.json"  # 🔐 서비스 계정 키 파일
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIAL_PATH

# === ~ 를 억양용 SSML로 자동 변환하는 함수 ===
def replace_tilde_with_ssml(text):
    return text.replace("~", "</prosody><break time=\"300ms\"/><prosody rate=\"slow\">")

# === 캐릭터별 원본 대사 (물결표 포함) ===
bear_raw = """
<speak><prosody rate="slow">
여우야~ 어디 가~?
<break time="800ms"/>
조심~ 넘어지면 안 돼~  
<break time="600ms"/>
짠! 손~ 잡았지롱!
<break time="800ms"/>
우와~ 빨간 나뭇잎!
<break time="400ms"/>
이건 무슨 색~일까?
<break time="800ms"/>
맞아! 우리 색깔 친구~ 많이 찾자!
<break time="700ms"/>
여우야, 나 배고파~
<break time="500ms"/>
우와~ 도토리 맛있다~ 우물우물~
<break time="800ms"/>
여우야도~ 귀여워~
<break time="600ms"/>
오늘 즐거웠다~
<break time="500ms"/>
안녕~ 빠이빠이~!
</prosody></speak>
"""

fox_raw = """
<speak><prosody rate="slow">
곰돌이~! 나 나뭇잎 따라 갔어!
<break time="600ms"/>
응~ 곰돌이 손~ 잡아줘~!
<break time="700ms"/>
히히~ 고마워~
<break time="800ms"/>
나는 노~란 거!
<break time="400ms"/>
주~황색!
<break time="500ms"/>
좋아~ 좋아~!
<break time="700ms"/>
우리 도토리~ 먹자!
<break time="600ms"/>
히히~ 곰돌이 귀여워~
<break time="600ms"/>
응~ 내일 또 놀자~!
<break time="500ms"/>
안녕~ 빠이빠이~!
</prosody></speak>
"""

# === Google TTS 함수 ===
def synthesize_ssml_to_mp3(ssml_text, output_file, voice_name):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.MALE if "B" in voice_name else texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f"✅ {output_file} 생성 완료")

# === 음성 + 배경음악 믹싱 함수 ===
def mix_voices_with_bgm(bear_path, fox_path, bgm_path, output_path):
    bear = AudioSegment.from_file(bear_path)
    fox = AudioSegment.from_file(fox_path)
    bgm = AudioSegment.from_file(bgm_path)

    # 기본 순서대로 이어 붙이기
    timeline = AudioSegment.empty()
    timeline += bear[0:5000]
    timeline += AudioSegment.silent(duration=600)
    timeline += fox[0:4000]
    timeline += AudioSegment.silent(duration=600)
    timeline += bear[5000:]
    timeline += AudioSegment.silent(duration=600)
    timeline += fox[4000:]

    # BGM 자르고 볼륨 줄이기
    bgm = bgm[:len(timeline)]
    bgm = bgm - 18  # 볼륨 낮추기

    final = bgm.overlay(timeline)
    final.export(output_path, format="mp3")
    print(f"🎵 최종 믹스 완료: {output_path}")

# === 실행 ===
if __name__ == "__main__":
    bear_ssml = replace_tilde_with_ssml(bear_raw)
    fox_ssml = replace_tilde_with_ssml(fox_raw)

    synthesize_ssml_to_mp3(bear_ssml, "bear.mp3", "ko-KR-Wavenet-B")
    synthesize_ssml_to_mp3(fox_ssml, "fox.mp3", "ko-KR-Wavenet-C")
    mix_voices_with_bgm("bear.mp3", "fox.mp3", "back.mp3", "final_mix.mp3")
