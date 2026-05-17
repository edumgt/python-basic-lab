from google.cloud import texttospeech
from pydub import AudioSegment

# === SSML 정의 (40초 요약본) ===
ssml = """

<break time="400ms"/>
노인 여성 신화자는 안티에이징 클리닉에 들어선다.  
<break time="600ms"/>

<prosody pitch="+2st">“신화자 님, 준비되셨습니다.”</prosody>  
<break time="400ms"/>
간호 로봇의 말에, 그녀는 조용히 고개를 끄덕인다.  
<break time="600ms"/>

침대에 누우면, 미세한 나노 니들이 피부를 스치고  
<break time="300ms"/>
주름 사이로 재생 겔이 스며든다.  
<break time="700ms"/>

<prosody rate="slow">30초 후, 눈가의 주름이 사라지고  
<break time="300ms"/>
2분 뒤, 입가의 웃음선이 펼쳐진다.</prosody>  
<break time="600ms"/>

<prosody pitch="+1st">“이건 마법이 아니에요. 과학입니다.”</prosody>  
<break time="500ms"/>
치료 로봇의 말에, 그녀는 미소 짓는다.  
<break time="500ms"/>


"""

# === Google Cloud TTS로 음성 생성 ===
def synthesize_ssml_to_mp3(ssml_text, output_filename, credentials_path):
    client = texttospeech.TextToSpeechClient.from_service_account_file(credentials_path)

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Wavenet-B",  # SSML 지원 감성 여성
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    with open(output_filename, "wb") as out:
        out.write(response.audio_content)
        print(f"✅ 음성 파일 생성 완료: {output_filename}")

# === 음성과 배경음악 믹싱 ===
def mix_audio(narration_file, bgm_file, output_file, bgm_volume_db=-15):
    narration = AudioSegment.from_file(narration_file)
    bgm = AudioSegment.from_file(bgm_file)

    # 배경음악을 나레이션 길이에 맞게 자르기 or 반복
    bgm = bgm[:len(narration)]
    bgm = bgm - abs(bgm_volume_db)  # 볼륨 낮추기

    # 믹스: 나레이션을 앞에 두고 배경에 깔기
    combined = bgm.overlay(narration)

    combined.export(output_file, format="mp3")
    print(f"✅ 최종 믹싱 완료: {output_file}")

# === 실행 ===
if __name__ == "__main__":
    credentials = "my-project.json"  # 🔒 서비스 계정 키
    synthesize_ssml_to_mp3(ssml, "narration.mp3", credentials)
    mix_audio("narration.mp3", "back.mp3", "final_mix.mp3", bgm_volume_db=-18)
