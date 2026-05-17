import os
from google.cloud import texttospeech
from googletrans import Translator

# 1️⃣ Google 서비스 계정 키 경로
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'my-project.json'

# 2️⃣ 번역 (한글 → 영어)
korean_text = """
Java Generic은 클래스나 메서드에서 사용할 데이터 타입을 일반화해서 작성할 수 있게 해주는 문법입니다.
쉽게 말하면, 타입을 파라미터처럼 받는다고 생각하면 됩니다.
예를 들어 ArrayList<String> list = new ArrayList<>(); 이렇게 쓰면 문자열만 받을 수 있게 됩니다.
장점은 컴파일 시 타입 검사, 형변환 필요 없음, 코드 재사용성 증가입니다.
"""

translator = Translator()
translated = translator.translate(korean_text, src='ko', dest='en')
english_text = translated.text

print("✅ 번역된 영어 문장:")
print(english_text)

# 3️⃣ Google Cloud TTS 클라이언트 생성
client = texttospeech.TextToSpeechClient()

# 4️⃣ TTS 요청 설정 (영어)
synthesis_input = texttospeech.SynthesisInput(text=english_text)

voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Wavenet-F",  # 네이티브 영어 남성 목소리 (원하면 여성도 가능)
    ssml_gender=texttospeech.SsmlVoiceGender.MALE
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=1.1  # 기본 속도의 1.1배
)

# 5️⃣ TTS API 호출
response = client.synthesize_speech(
    input=synthesis_input, voice=voice, audio_config=audio_config
)

# 6️⃣ MP3로 저장
output_file = "java_generic_english.mp3"
with open(output_file, "wb") as out:
    out.write(response.audio_content)
    print(f"✅ Google TTS 영어 mp3 파일 생성 완료: {output_file}")
