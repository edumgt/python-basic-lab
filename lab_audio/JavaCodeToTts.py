import os
import re
import random
from google.cloud import texttospeech
from datetime import timedelta

# Google TTS 설정
SERVICE_ACCOUNT_FILE = "my-project.json"  # 본인의 JSON 인증파일 경로
client = texttospeech.TextToSpeechClient.from_service_account_file(SERVICE_ACCOUNT_FILE)
voice_names = ["ko-KR-Wavenet-A", "ko-KR-Wavenet-B", "ko-KR-Wavenet-C", "ko-KR-Wavenet-D"]
selected_voice = random.choice(voice_names)

# 자바 코드 파일
JAVA_FILE = "CollectionExample.java"

# 자바 설명 변환 함수 (간단한 룰 기반 설명 예시)
def explain_java_code(code: str) -> list:
    explanations = []
    lines = code.strip().splitlines()
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        elif re.search(r"public\s+class\s+(\w+)", line):
            classname = re.findall(r"public\s+class\s+(\w+)", line)[0]
            explanations.append((f"{idx+1}", f"이 코드는 {classname}라는 클래스를 정의하고 있습니다."))
        elif "String[]" in line:
            explanations.append((f"{idx+1}", "이 줄에서는 문자열 배열을 선언하고 있습니다."))
        elif "new" in line and "(" in line:
            explanations.append((f"{idx+1}", "이 줄에서는 객체를 생성하고 있습니다."))
        elif "=" in line:
            explanations.append((f"{idx+1}", "이 줄은 변수에 값을 할당하고 있습니다."))
        else:
            explanations.append((f"{idx+1}", f"{line}에 대한 구체적인 설명은 추후에 추가됩니다."))
    return explanations

# 자막(SRT) 생성
def write_srt(explanations: list, filename="output.srt", duration_per_line=3):
    with open(filename, "w", encoding="utf-8") as f:
        for i, (line_no, text) in enumerate(explanations):
            start_time = timedelta(seconds=i * duration_per_line)
            end_time = timedelta(seconds=(i + 1) * duration_per_line)
            f.write(f"{i + 1}\n")
            f.write(f"{str(start_time)[:10].replace('.', ',')} --> {str(end_time)[:10].replace('.', ',')}\n")
            f.write(f"{text}\n\n")

# MP3 생성
def text_to_mp3(texts: list, output_file="Java_설명.mp3"):
    full_text = " ".join(text for _, text in texts)

    synthesis_input = texttospeech.SynthesisInput(text=full_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name=selected_voice,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.1,
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f"✅ MP3 저장 완료: {output_file}")

# === 실행 ===
if not os.path.exists(JAVA_FILE):
    print(f"❌ Java 파일이 존재하지 않습니다: {JAVA_FILE}")
    exit(1)

with open(JAVA_FILE, "r", encoding="utf-8") as f:
    java_code = f.read()

explains = explain_java_code(java_code)
text_to_mp3(explains, "Java_설명_출력.mp3")
write_srt(explains, "Java_설명_출력.srt")

print("✅ 전체 분석 및 음성/자막 생성 완료.")
