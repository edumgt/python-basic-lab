# 커리큘럼

docs 학습 문서와 lab 실습 파일을 단계적으로 연결한 학습 경로입니다.

---

## Phase 1 — 개발 환경 & 기초 규칙

| 순서 | 문서 | 내용 |
|------|------|------|
| 1 | [docs/001.md](docs/001.md) | PyPI — 패키지 설치·관리 |
| 2 | [docs/002.md](docs/002.md) | 들여쓰기(Indentation) |
| 3 | [docs/003.md](docs/003.md) | PEP 8 코딩 스타일 |
| 4 | [docs/004.md](docs/004.md) | Mypy 정적 타입 검사 |

---

## Phase 2 — 파이썬 문법 심화

| 순서 | 문서 | 내용 |
|------|------|------|
| 5 | [docs/024.md](docs/024.md) | 튜플, 딕셔너리, 집합 기초 |
| 6 | [docs/005.md](docs/005.md) | 리스트·딕셔너리 컴프리헨션 |
| 7 | [docs/006.md](docs/006.md) | Python 내장 함수 |
| 8 | [docs/007.md](docs/007.md) | `*args`, `**kwargs` |
| 9 | [docs/008.md](docs/008.md) | 람다 표현식 |
| 10 | [docs/009.md](docs/009.md) | 중첩 함수 |
| 11 | [docs/010.md](docs/010.md) | 클로저 |
| 12 | [docs/011.md](docs/011.md) | 데코레이터 |
| 13 | [docs/012.md](docs/012.md) | `match` 패턴 매칭 심화 |
| 14 | [docs/013.md](docs/013.md) | 예외 처리 |
| 15 | [docs/014.md](docs/014.md) | 이터레이터 |
| 16 | [docs/015.md](docs/015.md) | 제너레이터 |

---

## Phase 3 — 객체 지향 프로그래밍 (OOP)

| 순서 | 문서 | 내용 |
|------|------|------|
| 17 | [docs/016.md](docs/016.md) | OOP 기초 — 클래스와 객체 |
| 18 | [docs/017.md](docs/017.md) | 생성자와 인스턴스 속성 (`__init__`) |
| 19 | [docs/018.md](docs/018.md) | 상속과 메서드 오버라이딩 |
| 20 | [docs/019.md](docs/019.md) | 다형성, 덕 타이핑, 추상 클래스 |
| 21 | [docs/020.md](docs/020.md) | 캡슐화와 `property` |
| 22 | [docs/021.md](docs/021.md) | `@classmethod`와 `@staticmethod` |
| 23 | [docs/022.md](docs/022.md) | 특수 메서드와 `dataclass` |

---

## Phase 4 — 수학·통계 & 데이터 시각화

| 순서 | 문서 | 실습 파일 | 내용 |
|------|------|-----------|------|
| 24 | [docs/027.md](docs/027.md) | — | 거듭제곱, 지수, 제곱근, 선형대수 기초 |
| 25 | [docs/028.md](docs/028.md) | — | 이차방정식, 근의 공식 |
| 26 | [docs/029.md](docs/029.md) | — | 일차함수, 그래프, 기울기, 절편 |
| 27 | [docs/023.md](docs/023.md) | [lab_stats/statistics_basics.py](lab_stats/statistics_basics.py) | 편차, 분산, 표준편차 |
| 28 | [docs/030.md](docs/030.md) | — | 도수분포표, 스터지스 공식, 히스토그램 |
| 29 | [docs/031.md](docs/031.md) | [lab_stats/probability_basics.py](lab_stats/probability_basics.py) | 경우의 수, 확률의 덧셈·곱셈 |
| 30 | [docs/025.md](docs/025.md) | — | matplotlib 기초 |
| 31 | [docs/026.md](docs/026.md) | — | pandas 기초와 Series |

---

## Phase 5 — PDF 처리 실습

| 실습 파일 | 내용 | 핵심 도구 |
|-----------|------|-----------|
| [lab_pdf/pdf_cropmark.py](lab_pdf/pdf_cropmark.py) | PDF 크롭마크 삽입 (로컬 CLI) | `PyMuPDF`, `reportlab` |
| [lab_pdf/PdfToDocx.py](lab_pdf/PdfToDocx.py) | PDF → DOCX 변환 | `pdf2docx` |
| [lab_pdf/pdf_cropmark_lambda.py](lab_pdf/pdf_cropmark_lambda.py) | S3 이벤트 기반 Lambda 크롭마크 (클라우드) | `boto3` |

```bash
python lab_pdf/pdf_cropmark.py
python lab_pdf/PdfToDocx.py
```

---

## Phase 6 — 이미지 처리 실습

| 실습 파일 | 내용 | 핵심 도구 |
|-----------|------|-----------|
| [lab_image/id_masker.py](lab_image/id_masker.py) | OCR로 주민번호 탐지 후 뒷자리 마스킹 | `pytesseract`, `opencv` |
| [lab_image/subtitle_remover.py](lab_image/subtitle_remover.py) | 영상 하단 자막 인페인팅 제거 | `opencv`, `ffmpeg` |

```bash
python lab_image/id_masker.py
python lab_image/subtitle_remover.py
```

---

## Phase 7 — 오디오·TTS 실습

포맷 변환 → 단순 TTS → 번역 TTS → 믹싱 순으로 학습합니다.

| 실습 파일 | 내용 | 핵심 도구 |
|-----------|------|-----------|
| [lab_audio/WavToMp3.py](lab_audio/WavToMp3.py) | WAV → MP3 변환 | `pydub` |
| [lab_audio/M4aToMp3.py](lab_audio/M4aToMp3.py) | M4A → MP3 변환 | `pydub` |
| [lab_audio/KoreanTts.py](lab_audio/KoreanTts.py) | 한국어 TTS | `gTTS` |
| [lab_audio/BatchTextToMp3.py](lab_audio/BatchTextToMp3.py) | 텍스트 파일 일괄 TTS → MP3 | `google-cloud-tts` |
| [lab_audio/TranslateAndTts.py](lab_audio/TranslateAndTts.py) | 번역 + TTS | `googletrans`, `gTTS` |
| [lab_audio/JavaCodeToTts.py](lab_audio/JavaCodeToTts.py) | 자바 소스 코드 낭독 TTS | `gTTS` |
| [lab_audio/GeneratePianoBgm.py](lab_audio/GeneratePianoBgm.py) | 피아노 BGM 생성 | `numpy`, `pydub` |
| [lab_audio/MeditationAudioMix.py](lab_audio/MeditationAudioMix.py) | 명상 오디오 믹싱 | `pydub` |
| [lab_audio/TtsDialogBgmMix.py](lab_audio/TtsDialogBgmMix.py) | TTS 대화 + BGM 믹싱 | `pydub` |
| [lab_audio/TtsNarrationBgmMix.py](lab_audio/TtsNarrationBgmMix.py) | TTS 나레이션 + BGM 믹싱 | `pydub` |

```bash
python lab_audio/KoreanTts.py
python lab_audio/TranslateAndTts.py
```

---

## Phase 8 — 영상 편집 실습

기본 자르기/연결 → 오디오 합성 → 고급 편집 순으로 학습합니다.

| 실습 파일 | 내용 |
|-----------|------|
| [lab_video_edit/CutVideo.py](lab_video_edit/CutVideo.py) | 구간 자르기 |
| [lab_video_edit/ConcatMp4.py](lab_video_edit/ConcatMp4.py) | MP4 파일 단순 연결 |
| [lab_video_edit/ConcatClipParts.py](lab_video_edit/ConcatClipParts.py) | 클립 파트 순차 연결 |
| [lab_video_edit/TrimHalfAndConcat.py](lab_video_edit/TrimHalfAndConcat.py) | 절반 트림 후 연결 |
| [lab_video_edit/AddBgmToVideo.py](lab_video_edit/AddBgmToVideo.py) | 영상에 BGM 삽입 |
| [lab_video_edit/ReplaceVideoAudio.py](lab_video_edit/ReplaceVideoAudio.py) | 영상 음원 교체 |
| [lab_video_edit/ConcatVideosWithAudio.py](lab_video_edit/ConcatVideosWithAudio.py) | 영상 연결 + 오디오 합성 |
| [lab_video_edit/LoopVideoMergeAudio.py](lab_video_edit/LoopVideoMergeAudio.py) | 영상 루프 + 오디오 합성 |
| [lab_video_edit/FolderVideoAudioMerge.py](lab_video_edit/FolderVideoAudioMerge.py) | 폴더 단위 영상+오디오 병합 |
| [lab_video_edit/BatchPairMerge.py](lab_video_edit/BatchPairMerge.py) | 영상-오디오 쌍 일괄 병합 |
| [lab_video_edit/ShuffleVideosMergeAudio.py](lab_video_edit/ShuffleVideosMergeAudio.py) | 영상 랜덤 셔플 + 오디오 합성 |
| [lab_video_edit/CrossEditVideos.py](lab_video_edit/CrossEditVideos.py) | 교차 편집 |
| [lab_video_edit/VideoOverlay.py](lab_video_edit/VideoOverlay.py) | 영상 오버레이 합성 |

핵심 도구: `ffmpeg`

---

## Phase 9 — 화면 녹화 실습

| 실습 파일 | 내용 | 핵심 도구 |
|-----------|------|-----------|
| [lab_video_capture/screen_recorder_basic.py](lab_video_capture/screen_recorder_basic.py) | 화면 녹화 + TTS 설명 합성 | `mss`, `gTTS` |
| [lab_video_capture/screen_recorder.py](lab_video_capture/screen_recorder.py) | 핫키 기반 고급 녹화 (커서 표시, 자동 트림) | `mss`, `pynput`, `opencv` |

> 데스크톱 환경(키보드·마우스 훅)이 필요하므로 로컬에서 실행합니다.

```bash
python lab_video_capture/screen_recorder.py
```

---

## Phase 10 — AI 영상 분석 실습

| 실습 파일 | 내용 | 핵심 도구 |
|-----------|------|-----------|
| [lab_video_analysis/CheckGpu.py](lab_video_analysis/CheckGpu.py) | GPU/CUDA 상태 확인 | `torch` |
| [lab_video_analysis/video_captioner.py](lab_video_analysis/video_captioner.py) | 프레임 샘플링 → BLIP 캡션 → TTS 합성 | `torch`, `transformers`, `gTTS` |
| [lab_video_analysis/video_pipeline.py](lab_video_analysis/video_pipeline.py) | 녹화 종료 후 자동 분석 파이프라인 | `subprocess` |

```bash
python lab_video_analysis/CheckGpu.py
python lab_video_analysis/video_captioner.py sample.mp4 --frame-interval 2
python lab_video_analysis/video_pipeline.py
```

---

## Phase 11 — YouTube 자동화 실습

| 실습 파일 | 내용 | 핵심 도구 |
|-----------|------|-----------|
| [lab_youtube/OpenShortsLinks.py](lab_youtube/OpenShortsLinks.py) | Shorts 링크 목록 일괄 열기 | `webbrowser` |
| [lab_youtube/CollectShortsAndOpen.py](lab_youtube/CollectShortsAndOpen.py) | Shorts URL 수집 + 브라우저 열기 | `requests` |
| [lab_youtube/YouTubeUpload.py](lab_youtube/YouTubeUpload.py) | YouTube Data API로 자동 업로드 | `google-api-python-client` |

---

## Phase 12 — API 서비스 구축

FastAPI + Nginx + Docker Compose로 위 스크립트들을 웹 서비스로 묶습니다.

| 파일 | 내용 |
|------|------|
| [backend/app/main.py](backend/app/main.py) | FastAPI — 스크립트 실행 API |
| [frontend/index.html](frontend/index.html) | 작업 선택·실행·로그 조회 UI |
| [docker-compose.yml](docker-compose.yml) | backend + frontend 통합 실행 |

```bash
docker compose up -d --build
# FE: http://localhost:8080
# API: http://localhost:8000/api/health
```

| 엔드포인트 | 설명 |
|---|---|
| `GET /api/health` | 헬스체크 |
| `GET /api/tasks` | 실행 가능한 스크립트 목록 |
| `POST /api/jobs` | 작업 실행 (비동기) |
| `GET /api/jobs/{job_id}` | 작업 상태·로그 조회 |
