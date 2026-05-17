import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import time  # ⬅️ sleep을 위해 추가

# OAuth 인증
def get_authenticated_service():
    credentials = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        credentials = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(credentials, token)

    return build("youtube", "v3", credentials=credentials)

# 제목 포맷팅 함수
def format_title(filename, index):
    name = filename.replace(".mp4", "").replace("_", " ").title()
    return f"{name}"

# 개별 동영상 업로드 함수
def upload_video(youtube, file_path, title, description, tags):
    print(f"🚀 업로드 시작: {file_path}")
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public"  # ✅ 공개 업로드로 변경
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"✅ 업로드 완료: https://youtu.be/{response['id']}\n")

if __name__ == "__main__":
    youtube = get_authenticated_service()

    # ✅ Java_로 시작하는 mp4 파일들 업로드
    java_files = sorted([f for f in os.listdir(".") if f.endswith(".mp4")])
    
    for idx, filename in enumerate(java_files, start=1):
        title = format_title(filename, idx)
        upload_video(
            youtube,
            file_path=filename,
            title=title,
description = "Midjourney is an AI image synthesis platform that transforms natural language prompts into cinematic, fantastical visuals—robot armies, futuristic wars, and epic sci-fi concept art—powered by diffusion-based generative models. Ideal for visual storytelling, key art, worldbuilding, and high-impact creative production.",
tags = ["Fantastic", "Robot", "Futuristic War", "Sci-Fi", "Concept Art", "Cinematic", "Diffusion", "Worldbuilding"]

        )
        if idx < len(java_files):  # 마지막 파일이 아니면 딜레이
            print("⏳ 다음 업로드까지 5분 대기 중...\n")
            time.sleep(2080)  
