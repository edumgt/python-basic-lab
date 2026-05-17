import os
from google.cloud import texttospeech
from random import choice

# 서비스 계정 키 파일 경로
SERVICE_ACCOUNT_FILE = "my-project.json"

# Google TTS 클라이언트 초기화
client = texttospeech.TextToSpeechClient.from_service_account_file(SERVICE_ACCOUNT_FILE)

# 사용할 목소리 후보
voice_names = ["ko-KR-Chirp3-HD-Aoede", "ko-KR-Chirp3-HD-Kore", "ko-KR-Chirp3-HD-Leda","ko-KR-Chirp3-HD-Zephyr"]

# 오디오 설정 (1.1배속, MP3)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=1.2
)

# 텍스트 파일이 있는 디렉토리
TEXT_DIR = "text"

# 디렉토리 내 모든 .txt 파일 읽기
txt_files = [f for f in os.listdir(TEXT_DIR) if f.lower().endswith('.txt')]

if not txt_files:
    print("📁 'text/' 폴더에 .txt 파일이 없습니다.")
else:
    for txt_file in txt_files:
        txt_path = os.path.join(TEXT_DIR, txt_file)
        with open(txt_path, "r", encoding="utf-8") as file:
            text = file.read().strip()
            if not text:
                print(f"⚠️ {txt_file} 는 비어 있어 건너뜁니다.")
                continue

        # TTS 입력 구성
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # 목소리 랜덤 선택
        selected_voice = choice(voice_names)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name=selected_voice,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        # 출력 파일명 생성
        base_name = os.path.splitext(txt_file)[0]
        output_path = os.path.join(TEXT_DIR, f"{base_name}.mp3")

        # TTS 요청 및 MP3 저장
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            print(f"✅ {output_path} 생성 완료 (📄 {txt_file} → 🗣️ {selected_voice})")
