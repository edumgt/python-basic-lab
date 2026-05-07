# pycap

여러 Python 스크립트로 구성된 멀티미디어 자동화 실험 저장소입니다.  
핵심 도메인은 다음 4가지입니다.

1. PDF 후처리(리사이즈 + 크롭마크)
2. 화면 녹화/영상 후처리
3. AI 캡션 + TTS 음성 합성
4. OCR 기반 개인정보 마스킹

이번 업데이트에서 아래 항목을 반영했습니다.

1. 각 `*.py` 동작 분석 정리
2. `ana.py`, `main2.py` 실행 흐름 개선
3. FastAPI 백엔드 스캐폴드 추가
4. FE 대시보드 + Docker 통합 실행 구성 추가
5. **mypy 정적 타입 검사 적용** (전체 파일 타입 어노테이션 + `mypy.ini`)

## 저장소 구조

```text
.
├─ lab_pdf/                         # PDF 후처리 랩
│  ├─ pdf_cropmark.py               # 로컬 CLI: 크롭마크 추가
│  └─ pdf_cropmark_lambda.py        # AWS Lambda: S3 이벤트 기반 크롭마크
├─ lab_video_capture/               # 화면 녹화 랩
│  ├─ screen_recorder.py            # 고급 녹화 (커서 시각화, 자동 트림)
│  └─ screen_recorder_basic.py      # 기본 녹화 (TTS 후처리 포함)
├─ lab_video_analysis/              # AI 영상 분석 랩
│  ├─ video_captioner.py            # BLIP 캡션 + TTS 합성
│  └─ video_pipeline.py             # 녹화 → 분석 파이프라인
├─ lab_image/                       # 이미지 처리 랩
│  ├─ id_masker.py                  # OCR 기반 주민번호 마스킹
│  └─ subtitle_remover.py           # 영상 자막 인페인팅 제거
├─ backend/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app/
│     ├─ __init__.py
│     └─ main.py
├─ frontend/
│  ├─ Dockerfile
│  ├─ nginx.conf
│  ├─ index.html
│  ├─ app.js
│  └─ styles.css
├─ docs/                            # 학습 문서
│  ├─ 001.md                        # PyPI 완벽 가이드
│  ├─ 002.md                        # 파이썬 들여쓰기 가이드
│  ├─ 003.md                        # PEP 8 코딩 스타일 가이드
│  ├─ 004.md                        # Mypy 정적 타입 검사 가이드
│  ├─ 005.md                        # 리스트/딕셔너리 컴프리헨션
│  ├─ 006.md                        # Python 내장 함수 정리
│  ├─ 007.md                        # *args/**kwargs
│  ├─ 008.md                        # 람다 표현식
│  ├─ 009.md                        # 중첩 함수
│  ├─ 010.md                        # 클로저
│  ├─ 011.md                        # 데코레이터
│  ├─ 012.md                        # match 패턴 심화
│  ├─ 013.md                        # 예외 처리
│  ├─ 014.md                        # 이터레이터
│  ├─ 015.md                        # 제너레이터
│  ├─ 016.md                        # OOP 기초 (클래스/객체)
│  ├─ 017.md                        # 생성자/인스턴스 속성
│  ├─ 018.md                        # 상속/오버라이딩
│  ├─ 019.md                        # 다형성/덕 타이핑/ABC
│  ├─ 020.md                        # 캡슐화/property
│  ├─ 021.md                        # classmethod/staticmethod
│  └─ 022.md                        # 특수 메서드/dataclass
├─ mypy.ini                         # mypy 설정
├─ docker-compose.yml
├─ requirements.txt
└─ requirements.full.txt
```

## 랩별 파일 안내

| 랩 | 파일 | 실행 내용 | 핵심 기술 스택 | 실행 명령 |
|---|---|---|---|---|
| `lab_pdf` | `pdf_cropmark.py` | PDF를 460×318mm 캔버스에 중앙 배치 후 크롭마크 삽입 | `PyMuPDF`, `reportlab`, `PyPDF2` | `python lab_pdf/pdf_cropmark.py` |
| `lab_pdf` | `pdf_cropmark_lambda.py` | S3 이벤트 기반 Lambda 크롭마크 처리 | `boto3`, PDF 스택 | Lambda 핸들러로 사용 |
| `lab_video_capture` | `screen_recorder.py` | 핫키 기반 화면 녹화, 커서 표시, 마지막 5초 자동 제거 | `mss`, `pynput`, `opencv`, `pyautogui` | `python lab_video_capture/screen_recorder.py` |
| `lab_video_capture` | `screen_recorder_basic.py` | 화면 녹화 후 TTS 설명 음성 합성 | `gTTS`, `ffmpeg`, `mss` | `python lab_video_capture/screen_recorder_basic.py` |
| `lab_video_analysis` | `video_captioner.py` | 프레임 샘플링 → BLIP 캡션 → 자막 → TTS 합성 | `torch`, `transformers(BLIP)`, `gTTS`, `ffmpeg-python` | `python lab_video_analysis/video_captioner.py <mp4>` |
| `lab_video_analysis` | `video_pipeline.py` | 녹화 종료 후 최신 mp4를 자동 탐색해 captioner 실행 | `subprocess`, 오케스트레이션 | `python lab_video_analysis/video_pipeline.py` |
| `lab_image` | `id_masker.py` | OCR로 주민번호 탐지 후 뒷자리 마스킹 | `pytesseract`, `opencv`, `regex` | `python lab_image/id_masker.py` |
| `lab_image` | `subtitle_remover.py` | 영상 하단 자막 영역 인페인팅 제거 후 재조립 | `opencv`, `ffmpeg` | `python lab_image/subtitle_remover.py [mp4]` |

## 기술 스택 상세

1. PDF: `PyMuPDF`, `reportlab`, `PyPDF2`
2. Video/Image: `opencv-python`, `numpy`, `Pillow`, `mss`
3. Desktop Control: `pynput`, `pyautogui`
4. AI Caption: `torch`, `transformers` (BLIP)
5. TTS/Media Merge: `gTTS`, `ffmpeg`, `ffmpeg-python`
6. OCR/PII: `pytesseract`
7. Cloud Example: `boto3` (Lambda + S3 pattern)
8. Solution Layer: `FastAPI`, `Uvicorn`, `Nginx`, `Docker Compose`
9. 정적 타입 검사: `mypy`

`requirements.txt`는 PDF 최소 의존성만 포함합니다.  
전체 의존성 설치가 필요하면 `requirements.full.txt`를 사용하세요.

## 로컬 실행

시스템 의존성:

1. `ffmpeg`
2. `tesseract-ocr` (OCR 기능 사용 시)

Python 의존성:

```bash
pip install -r requirements.full.txt
```

예시:

```bash
# 1) PDF 후처리
python lab_pdf/pdf_cropmark.py

# 2) 화면 녹화
python lab_video_capture/screen_recorder.py

# 3) 특정 영상 AI 분석
python lab_video_analysis/video_captioner.py z_20260301_120000.mp4 --frame-interval 2

# 4) 녹화 후 자동 분석 파이프라인
python lab_video_analysis/video_pipeline.py
```

## Mypy 타입 검사

프로젝트 전체에 [mypy](https://mypy-lang.org/) 정적 타입 검사가 적용되어 있습니다.  
설정은 `mypy.ini`에서 관리하며, 제3자 라이브러리 stubs가 없는 경우 `ignore_missing_imports = True`로 처리합니다.

```bash
# mypy 설치 (requirements.full.txt에 포함)
pip install mypy

# 전체 프로젝트 검사
mypy lab_pdf/ lab_video_capture/ lab_video_analysis/ lab_image/ backend/app/main.py
```

## 이번 코드 보완 사항

1. `ana.py`
2. CLI 인자 지원(`video_path`, `--frame-interval`, `--font-path`, `--tts-lang`)
3. 영상 미지정 시 최신 녹화본 자동 탐색
4. ffmpeg 병합 호출 방식 보완
5. `main2.py`
6. `z_*.mp4`/`record_*.mp4` 모두 탐색하도록 수정
7. `sys.executable` 사용으로 환경 일관성 개선

## FastAPI 백엔드 솔루션

추가된 파일: [`backend/app/main.py`](backend/app/main.py)

핵심 API:

1. `GET /api/health`: 헬스체크
2. `GET /api/tasks`: 실행 가능한 스크립트 목록/메타데이터
3. `POST /api/jobs`: 작업 실행(비동기)
4. `GET /api/jobs`: 작업 목록 조회
5. `GET /api/jobs/{job_id}`: 작업 상세(표준출력/에러 포함)

실행 요청 예시:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "video_caption_tts",
    "args": ["z_20260301_120000.mp4", "--frame-interval", "2"],
    "cwd": "."
  }'
```

`lab_pdf/pdf_cropmark.py`처럼 stdin 입력이 필요한 작업은 `stdin` 필드를 함께 전달합니다.

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "pdf_resize_cropmarks",
    "stdin": "01.pdf\n",
    "cwd": "."
  }'
```

## FE 연동 솔루션

추가된 파일: [`frontend/index.html`](frontend/index.html), [`frontend/app.js`](frontend/app.js)

기능:

1. 백엔드 작업 목록 로드
2. 스크립트 선택 + args/stdin 입력 후 실행
3. 작업 상태/로그 실시간 폴링(5초)

Nginx에서 `/api/*`를 백엔드로 프록시하여 same-origin으로 동작합니다.

## Docker 통합 구성

추가된 파일: [`docker-compose.yml`](docker-compose.yml)

서비스:

1. `backend`: FastAPI (`:8000`)
2. `frontend`: Nginx 정적 UI + API 프록시 (`:8080`)
3. 백엔드 컨테이너에는 기본적으로 `requirements.txt`(PDF 스택) + FastAPI 의존성이 설치됨

실행:

```bash
docker compose up -d --build
```

접속:

1. FE: `http://localhost:8080`
2. BE API: `http://localhost:8000/api/health`

## 학습 문서 (docs/)

### 📄 001 — PyPI (Python Package Index) 완벽 가이드

**PyPI**는 파이썬 소프트웨어 재단(PSF)에서 운영하는 파이썬 공식 제3자 소프트웨어 저장소입니다.  
약 50만 개 이상의 오픈소스 프로젝트가 등록되어 있으며, **pip**를 통해 패키지를 설치·관리합니다.

| 명령어 | 설명 |
| :--- | :--- |
| `pip install <package>` | 패키지 설치 |
| `pip install <package>==1.2.3` | 특정 버전 설치 |
| `pip uninstall <package>` | 패키지 삭제 |
| `pip list` | 설치된 패키지 목록 조회 |
| `pip freeze > requirements.txt` | 환경 의존성 저장 |

> **보안 주의:** Typosquatting 패키지를 주의하고, 반드시 가상 환경(`venv`)에서 의존성을 관리하세요.

📎 상세 내용: [`docs/001.md`](docs/001.md)

---

### 📄 002 — 파이썬 들여쓰기(Indentation) 가이드

파이썬은 중괄호(`{}`) 대신 **들여쓰기로 코드 블록을 정의**합니다. 들여쓰기를 지키지 않으면 `IndentationError`가 발생합니다.

```python
def check_weather(temperature):
    if temperature > 25:
        print("날씨가 덥습니다.")   # if문에 속함
    else:
        print("날씨가 적당합니다.") # else문에 속함
    print("검사가 완료되었습니다.") # 함수(def)에만 속함
```

📎 상세 내용: [`docs/002.md`](docs/002.md)

---

### 📄 003 — PEP 8 코딩 스타일 가이드

**PEP 8**은 파이썬 공식 코딩 스타일 가이드입니다. 핵심 규칙은 다음과 같습니다.

| 항목 | 규칙 |
| :--- | :--- |
| 들여쓰기 | 공백 4칸 사용 |
| 줄 길이 | 최대 79자 권장 |
| 변수·함수 이름 | `snake_case` |
| 클래스 이름 | `PascalCase` |
| 상수 이름 | `SCREAMING_SNAKE_CASE` |

> **💡 팁:** `flake8`, `black`, `autopep8` 같은 포매터로 자동 적용할 수 있습니다.

📎 상세 내용: [`docs/003.md`](docs/003.md)

---

### 📄 004 — Mypy 정적 타입 검사 가이드

**Mypy**는 파이썬용 정적 타입 검사기로, 타입 힌트(`->`, `: int` 등)를 활용해 코드를 실행하기 전에 타입 오류를 탐지합니다.

주요 특징:
- **실행 전 오류 탐지**: 런타임 이전에 타입 불일치를 발견합니다.
- **점진적 타이핑**: 전체 코드가 아닌 일부 파일이나 함수에만 선택적으로 적용 가능합니다.
- **성능 영향 없음**: 개발 단계에서만 동작하며 실행 속도에 영향을 주지 않습니다.

```bash
# 설치
pip install mypy

# 검사 실행
mypy <파일 또는 패키지>
```

📎 상세 내용: [`docs/004.md`](docs/004.md)

---

### 📄 005 ~ 022 — 파이썬 확장 학습 문서

문법/스타일 기초 이후 학습을 위해 다음 주제를 순차적으로 추가했습니다.

- [`docs/005.md`](docs/005.md): 리스트/딕셔너리 컴프리헨션
- [`docs/006.md`](docs/006.md): Python 내장 함수 및 유용한 기능
- [`docs/007.md`](docs/007.md): `*args`, `**kwargs`
- [`docs/008.md`](docs/008.md): 람다 표현식 (`lambda`)
- [`docs/009.md`](docs/009.md): 중첩 함수 (Nested Function)
- [`docs/010.md`](docs/010.md): 클로저 (Closure)
- [`docs/011.md`](docs/011.md): 데코레이터 (Decorator)
- [`docs/012.md`](docs/012.md): `match` 패턴 매칭 심화
- [`docs/013.md`](docs/013.md): 예외 처리 (Exception Handling)
- [`docs/014.md`](docs/014.md): 이터레이터 (Iterator)
- [`docs/015.md`](docs/015.md): 제너레이터 (Generator)
- [`docs/016.md`](docs/016.md): 객체 지향 기초 (클래스/객체)
- [`docs/017.md`](docs/017.md): 생성자와 인스턴스 속성 (`__init__`)
- [`docs/018.md`](docs/018.md): 상속과 메서드 오버라이딩
- [`docs/019.md`](docs/019.md): 다형성, 덕 타이핑, 추상 클래스
- [`docs/020.md`](docs/020.md): 캡슐화와 `property`
- [`docs/021.md`](docs/021.md): `@classmethod`와 `@staticmethod`
- [`docs/022.md`](docs/022.md): 특수 메서드와 `dataclass`

---

## 확장/고도화 제안

1. Script -> Library 분리
2. 각 스크립트 로직을 함수형 모듈로 분리하고 CLI는 thin wrapper로 축소
3. Job Queue 도입
4. FastAPI는 요청/상태관리만 담당하고, 실제 실행은 `Celery + Redis` 또는 `RQ` 워커로 분리
5. Storage 표준화
6. 입력/출력 파일을 로컬 폴더 대신 S3/MinIO로 통일하고 job metadata를 DB(PostgreSQL)에 저장
7. AI 처리 고도화
8. `ana.py`를 멀티모달 파이프라인(캡션 + ASR + 번역 + 요약)으로 확장
9. OCR 품질 개선
10. 주민번호 외 여권번호/계좌번호 등 패턴 룰셋 + confidence threshold + review queue 추가
11. 운영 품질
12. `structlog`, OpenTelemetry, Prometheus, Sentry를 붙여 추적/관측성 강화
13. 보안
14. 작업 실행 allowlist 유지, 경로 검증 강화, 업로드 파일 바이러스 스캔, API 인증(JWT/Keycloak) 적용

## 권장 다음 단계

1. `lab_image/id_masker.py`, `lab_image/subtitle_remover.py`를 함수형 모듈로 리팩터링해서 API 직접 호출형으로 전환
2. GPU/CPU 워커 분리 배포 전략 수립(캡션 모델 전용 워커)
3. CI에 lint/test + smoke test(docker compose 기반) 추가

---

## 🎬 관련 유튜브 강의

[▶ 유튜브에서 "파이썬 기초 프로그래밍 강의" 검색하기](https://www.youtube.com/results?search_query=파이썬+기초+프로그래밍+강의)
