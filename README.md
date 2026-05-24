# python-basic-lab

파이썬 기초 학습을 중심으로, **영상 편집·오디오 TTS·PDF/이미지 처리·통계 실습·게임 프로토타입·FastAPI 실행 오케스트레이션**을 함께 다루는 실습형 저장소입니다.

## 프로젝트 개요

- 학습 문서(`docs/001.md` ~ `docs/031.md`)로 파이썬 기초/수학/통계 개념을 단계적으로 학습
- 실습 스크립트(`lab_*`)로 영상 편집·오디오 생성·파일 처리·AI 분석 같은 자동화 작업 체험
- `game/` 하위 프로젝트로 pygame/asyncio/socket 기반 게임 구조와 실시간 상호작용 예제 학습
- `backend` + `frontend` + `docker-compose.yml`로 스크립트 실행을 API/UI 형태로 실습 가능

## 저장소 구조

```text
.
├─ lab_video_edit/              # 영상 편집 랩
│  ├─ AddBgmToVideo.py          # 영상에 BGM 추가
│  ├─ BatchPairMerge.py         # 영상-오디오 쌍 일괄 병합
│  ├─ ConcatClipParts.py        # 클립 파트 순차 연결
│  ├─ ConcatMp4.py              # MP4 파일 연결
│  ├─ ConcatVideosWithAudio.py  # 영상 연결 + 오디오 합성
│  ├─ CrossEditVideos.py        # 영상 교차 편집
│  ├─ CutVideo.py               # 구간 자르기
│  ├─ FolderVideoAudioMerge.py  # 폴더 단위 영상+오디오 병합
│  ├─ LoopVideoMergeAudio.py    # 영상 루프 + 오디오 합성
│  ├─ ReplaceVideoAudio.py      # 영상 음원 교체
│  ├─ ShuffleVideosMergeAudio.py# 영상 랜덤 셔플 + 오디오 합성
│  ├─ TrimHalfAndConcat.py      # 절반 트림 후 연결
│  └─ VideoOverlay.py           # 영상 오버레이 합성
├─ lab_audio/                   # 오디오·TTS 랩
│  ├─ BatchTextToMp3.py         # 텍스트 일괄 TTS → MP3
│  ├─ GeneratePianoBgm.py       # 피아노 BGM 생성
│  ├─ JavaCodeToTts.py          # 자바 코드 → TTS 낭독
│  ├─ KoreanTts.py              # 한국어 TTS
│  ├─ M4aToMp3.py               # M4A → MP3 변환
│  ├─ MeditationAudioMix.py     # 명상 오디오 믹싱
│  ├─ TranslateAndTts.py        # 번역 + TTS
│  ├─ TtsDialogBgmMix.py        # TTS 대화 + BGM 믹싱
│  ├─ TtsNarrationBgmMix.py     # TTS 나레이션 + BGM 믹싱
│  └─ WavToMp3.py               # WAV → MP3 변환
├─ lab_youtube/                 # YouTube 자동화 랩
│  ├─ CollectShortsAndOpen.py   # Shorts 수집 + 브라우저 열기
│  ├─ OpenShortsLinks.py        # Shorts 링크 일괄 열기
│  └─ YouTubeUpload.py          # YouTube 업로드 자동화
├─ lab_video_capture/           # 화면 녹화 랩
│  ├─ screen_recorder.py        # 고급 녹화 (커서 시각화, 자동 트림)
│  └─ screen_recorder_basic.py  # 기본 녹화 (TTS 후처리 포함)
├─ lab_video_analysis/          # AI 영상 분석 랩
│  ├─ video_captioner.py        # BLIP 캡션 + TTS 합성
│  ├─ video_pipeline.py         # 녹화 → 분석 파이프라인
│  └─ CheckGpu.py               # GPU/CUDA 상태 확인
├─ lab_image/                   # 이미지 처리 랩
│  ├─ id_masker.py              # OCR 기반 주민번호 마스킹
│  └─ subtitle_remover.py       # 영상 자막 인페인팅 제거
├─ lab_pdf/                     # PDF 처리 랩
│  ├─ pdf_cropmark.py           # 로컬 CLI: 크롭마크 추가
│  ├─ pdf_cropmark_lambda.py    # AWS Lambda: S3 이벤트 기반 크롭마크
│  └─ PdfToDocx.py              # PDF → DOCX 변환
├─ lab_stats/                   # 통계 기초 랩
│  ├─ statistics_basics.py      # 편차/분산/표준편차 실습
│  └─ probability_basics.py     # 경우의 수/확률 실습
├─ game/                        # 게임 프로토타입 모음
│  ├─ shooting/                 # asyncio WebSocket 슈팅 + pygame 싱글 버전
│  ├─ tetris/                   # 방 생성/채팅/대전 테트리스
│  ├─ jang-gi/                  # 한국 장기 규칙 구현
│  └─ rpg/                      # 2D RPG 프로토타입
├─ backend/                     # FastAPI 백엔드
│  └─ app/main.py               # 스크립트 실행 API
├─ frontend/                    # Nginx 정적 UI
├─ docs/                        # 학습 문서 (001 ~ 031)
├─ mypy.ini
├─ docker-compose.yml
├─ requirements.txt             # PDF 최소 의존성
└─ requirements.full.txt        # 전체 의존성
```

## 랩별 파일 안내

### 영상 편집 (`lab_video_edit`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `AddBgmToVideo.py` | 영상에 BGM 삽입 | `ffmpeg` |
| `BatchPairMerge.py` | 영상-오디오 쌍 일괄 병합 | `ffmpeg` |
| `ConcatClipParts.py` | 클립 파트 순차 연결 | `ffmpeg` |
| `ConcatMp4.py` | MP4 파일 단순 연결 | `ffmpeg` |
| `ConcatVideosWithAudio.py` | 영상 연결 + 오디오 합성 | `ffmpeg` |
| `CrossEditVideos.py` | 교차 편집 (A/B 클립 번갈아) | `ffmpeg` |
| `CutVideo.py` | 구간 자르기 | `ffmpeg` |
| `FolderVideoAudioMerge.py` | 폴더 단위 영상+오디오 병합 | `ffmpeg` |
| `LoopVideoMergeAudio.py` | 영상 루프 + 오디오 합성 | `ffmpeg` |
| `ReplaceVideoAudio.py` | 기존 영상 음원 교체 | `ffmpeg` |
| `ShuffleVideosMergeAudio.py` | 영상 랜덤 셔플 + 오디오 합성 | `ffmpeg` |
| `TrimHalfAndConcat.py` | 절반 트림 후 연결 | `ffmpeg` |
| `VideoOverlay.py` | 영상 오버레이 합성 | `ffmpeg` |

### 오디오·TTS (`lab_audio`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `BatchTextToMp3.py` | 텍스트 파일 일괄 TTS → MP3 | `google-cloud-tts` |
| `GeneratePianoBgm.py` | 피아노 음계로 BGM 생성 | `numpy`, `pydub` |
| `JavaCodeToTts.py` | 자바 소스 코드 낭독 TTS | `gTTS` |
| `KoreanTts.py` | 한국어 TTS 변환 | `gTTS` |
| `M4aToMp3.py` | M4A → MP3 포맷 변환 | `pydub` / `ffmpeg` |
| `MeditationAudioMix.py` | 명상용 오디오 트랙 믹싱 | `pydub` |
| `TranslateAndTts.py` | 텍스트 번역 후 TTS | `googletrans`, `gTTS` |
| `TtsDialogBgmMix.py` | TTS 대화 음성 + BGM 믹싱 | `pydub` |
| `TtsNarrationBgmMix.py` | TTS 나레이션 + BGM 믹싱 | `pydub` |
| `WavToMp3.py` | WAV → MP3 포맷 변환 | `pydub` / `ffmpeg` |

### YouTube 자동화 (`lab_youtube`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `CollectShortsAndOpen.py` | Shorts URL 수집 + 브라우저 열기 | `requests`, `webbrowser` |
| `OpenShortsLinks.py` | Shorts 링크 목록 일괄 열기 | `webbrowser` |
| `YouTubeUpload.py` | YouTube Data API로 자동 업로드 | `google-api-python-client` |

### 화면 녹화 (`lab_video_capture`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `screen_recorder.py` | 핫키 기반 녹화, 커서 표시, 마지막 5초 자동 제거 | `mss`, `pynput`, `opencv` |
| `screen_recorder_basic.py` | 화면 녹화 후 TTS 설명 음성 합성 | `gTTS`, `ffmpeg`, `mss` |

### AI 영상 분석 (`lab_video_analysis`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `video_captioner.py` | 프레임 샘플링 → BLIP 캡션 → 자막 → TTS 합성 | `torch`, `transformers(BLIP)`, `gTTS` |
| `video_pipeline.py` | 녹화 종료 후 최신 mp4 자동 탐색 → captioner 실행 | `subprocess` |
| `CheckGpu.py` | CUDA 사용 가능 여부 및 GPU 정보 출력 | `torch` |

### 이미지 처리 (`lab_image`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `id_masker.py` | OCR로 주민번호 탐지 후 뒷자리 마스킹 | `pytesseract`, `opencv` |
| `subtitle_remover.py` | 영상 하단 자막 영역 인페인팅 제거 | `opencv`, `ffmpeg` |

### PDF 처리 (`lab_pdf`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `pdf_cropmark.py` | PDF를 460×318mm 캔버스에 배치 후 크롭마크 삽입 | `PyMuPDF`, `reportlab` |
| `pdf_cropmark_lambda.py` | S3 이벤트 기반 Lambda 크롭마크 처리 | `boto3`, PDF 스택 |
| `PdfToDocx.py` | PDF → DOCX 변환 | `pdf2docx` |

### 통계 기초 (`lab_stats`)

| 파일 | 설명 | 핵심 도구 |
|---|---|---|
| `statistics_basics.py` | 편차·분산·표준편차 예제 계산 | `math` |
| `probability_basics.py` | 경우의 수, 확률, 덧셈/곱셈 정리 | `math` |

### 게임 프로토타입 (`game`)

| 프로젝트 | 주요 Python 파일 | 분석 내용 | 핵심 도구 |
|---|---|---|---|
| `shooting/` | `server.py`, `game.py` | `server.py`는 `aiohttp` 기반 2인 WebSocket 서버로 로비/레디체크/30FPS 서버 권위 물리/상태 브로드캐스트를 담당하고, `game.py`는 `pygame` 단일 플레이 버전으로 파티클·웨이브·보스·씬 전환 구조를 담습니다. | `aiohttp`, `asyncio`, `pygame` |
| `tetris/` | `main.py`, `server.py`, `tet.py` | `server.py`는 TCP 로비 서버로 방 생성·입장·채팅·ready 동기화를 관리하고, `tet.py`는 `NetworkClient`·`Board`·`PlayerState`·`TetrisRoomClient`로 대전 로직과 UI를 분리하며, `main.py`는 클라이언트/서버 실행 진입점 역할을 합니다. | `socket`, `threading`, `pygame`, `pygame_gui` |
| `jang-gi/` | `jang.py` | 단일 파일 안에서 장기판 렌더링, 기물별 이동 규칙, 장수 마주보기, 체크/체크메이트 판정, 턴 기반 입력 처리를 함께 구현한 규칙 중심 예제입니다. | `pygame` |
| `rpg/` | `gg.py` | 무작위 타일 맵 생성 후 `Tile`·`NPC`·`Monster`·`Player` 스프라이트를 구성하고, 대화 상태와 전투 상태를 플래그로 전환하는 2D RPG 프로토타입입니다. | `pygame`, `random` |

## 기술 스택

| 분류 | 라이브러리 |
|---|---|
| 영상·오디오 편집 | `ffmpeg`, `ffmpeg-python`, `pydub`, `opencv-python` |
| TTS | `gTTS`, `google-cloud-texttospeech` |
| 화면 캡처·제어 | `mss`, `pynput`, `pyautogui` |
| AI 캡션 | `torch`, `transformers` (BLIP) |
| 이미지·OCR | `Pillow`, `numpy`, `pytesseract` |
| PDF | `PyMuPDF`, `reportlab`, `PyPDF2`, `pdf2docx` |
| YouTube API | `google-api-python-client` |
| 클라우드 | `boto3` (Lambda + S3) |
| 서비스 레이어 | `FastAPI`, `Uvicorn`, `Nginx`, `Docker Compose` |
| 정적 타입 검사 | `mypy` |

`requirements.txt`는 PDF 최소 의존성만 포함합니다. 전체 설치가 필요하면 `requirements.full.txt`를 사용하세요.

## 실행 방법

### 로컬 환경

시스템 의존성 설치:

```bash
# ffmpeg (영상·오디오 처리)
sudo apt install ffmpeg

# tesseract (OCR 기능 사용 시)
sudo apt install tesseract-ocr
```

Python 의존성 설치:

```bash
pip install -r requirements.full.txt
```

실행 예시:

```bash
# 영상 편집
python lab_video_edit/CutVideo.py
python lab_video_edit/ConcatMp4.py

# 오디오·TTS
python lab_audio/KoreanTts.py
python lab_audio/BatchTextToMp3.py

# AI 영상 분석
python lab_video_analysis/video_captioner.py sample.mp4 --frame-interval 2

# 화면 녹화
python lab_video_capture/screen_recorder.py

# PDF 처리
python lab_pdf/pdf_cropmark.py

# 통계 기초
python lab_stats/statistics_basics.py
python lab_stats/probability_basics.py
```

> 화면 녹화 스크립트는 데스크톱/키보드 훅이 필요해 컨테이너 환경보다 로컬 실행이 적합합니다.

### Docker 환경

```bash
docker compose up -d --build
```

| 서비스 | 접속 주소 |
|---|---|
| 프론트엔드 UI | `http://localhost:8080` |
| 백엔드 API | `http://localhost:8000/api/health` |

#### 백엔드 API 요약

| 엔드포인트 | 설명 |
|---|---|
| `GET /api/health` | 헬스체크 |
| `GET /api/tasks` | 실행 가능한 스크립트 목록 |
| `POST /api/jobs` | 작업 실행 (비동기) |
| `GET /api/jobs/{job_id}` | 작업 상태·로그 조회 |

작업 실행 예시:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"task_id": "video_caption_tts", "args": ["sample.mp4", "--frame-interval", "2"]}'
```

## Mypy 타입 검사

```bash
pip install mypy

mypy lab_pdf/ lab_video_capture/ lab_video_analysis/ lab_image/ backend/app/main.py
```

설정은 `mypy.ini`에서 관리하며, 서드파티 stubs가 없는 경우 `ignore_missing_imports = True`로 처리합니다.

## 커리큘럼

docs 학습 문서와 lab 실습 파일을 단계별로 연결한 전체 학습 경로는 [CURRICULUM.md](CURRICULUM.md)를 참고하세요.

## 학습 문서 (`docs/`)

| 번호 | 주제 |
|---|---|
| 001 | PyPI 완벽 가이드 |
| 002 | 들여쓰기(Indentation) 가이드 |
| 003 | PEP 8 코딩 스타일 가이드 |
| 004 | Mypy 정적 타입 검사 |
| 005 | 리스트/딕셔너리 컴프리헨션 |
| 006 | Python 내장 함수 |
| 007 | `*args`, `**kwargs` |
| 008 | 람다 표현식 |
| 009 | 중첩 함수 |
| 010 | 클로저 |
| 011 | 데코레이터 |
| 012 | `match` 패턴 매칭 심화 |
| 013 | 예외 처리 |
| 014 | 이터레이터 |
| 015 | 제너레이터 |
| 016 | OOP 기초 (클래스/객체) |
| 017 | 생성자와 인스턴스 속성 |
| 018 | 상속과 메서드 오버라이딩 |
| 019 | 다형성, 덕 타이핑, 추상 클래스 |
| 020 | 캡슐화와 `property` |
| 021 | `@classmethod`와 `@staticmethod` |
| 022 | 특수 메서드와 `dataclass` |
| 023 | 편차, 분산, 표준편차 |
| 024 | 튜플, 딕셔너리, 집합 기초 |
| 025 | matplotlib 기초 |
| 026 | pandas 기초와 `Series` |
| 027 | 거듭제곱, 지수, 제곱근, 선형대수 기초 |
| 028 | 이차함수·이차방정식, 근의 공식 |
| 029 | 일차함수, 그래프, 기울기, 절편 |
| 030 | 도수분포표, 스터지스 공식, 히스토그램 |
| 031 | 경우의 수, 확률의 덧셈/곱셈 |
