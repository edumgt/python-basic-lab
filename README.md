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

## 저장소 구조

```text
.
├─ ana.py
├─ cap.py
├─ main.py
├─ main2.py
├─ mask.py
├─ pdf.py
├─ remove.py
├─ start.py
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
├─ docker-compose.yml
├─ requirements.txt
└─ requirements.full.txt
```

## 각 Python 파일 분석

| 파일 | 실행 내용 | 입력/출력 | 핵심 기술 스택 | 실행 명령 |
|---|---|---|---|---|
| `pdf.py` | PDF 각 페이지를 460x318mm 기준으로 중앙 배치 후 크롭마크 삽입 | 입력: 사용자 입력 PDF 경로, 출력: `*_work.pdf` | `PyMuPDF`, `reportlab`, `PyPDF2` | `python pdf.py` |
| `main.py` | `resize_with_cropmarks()` + `lambda_handler()`로 S3 이벤트 기반 처리 예시 | 입력: S3 event, 출력: S3 업로드(`*_work.pdf`) | `boto3`, PDF 스택 | Lambda 환경에서 핸들러로 사용 |
| `cap.py` | 글로벌 핫키 기반 화면 녹화, 중앙 크롭, 마우스 커서 표시 | 입력: 데스크톱 화면, 출력: `z_YYYYmmdd_HHMMSS.mp4` | `mss`, `pynput`, `opencv`, `Pillow`, `pyautogui` | `python cap.py` |
| `start.py` | 화면 녹화 후 고정 설명 TTS 생성, 영상+오디오 병합 | 입력: 화면, 출력: `record_*.mp4`, `final_record_*.mp4` | `gTTS`, `ffmpeg`, 영상 스택 | `python start.py` |
| `ana.py` | 영상 프레임 간격 샘플링 -> BLIP 캡션 -> 자막 오버레이 -> TTS 합성 | 입력: mp4, 출력: `captioned_<원본>_<timestamp>.mp4` | `torch`, `transformers(BLIP)`, `gTTS`, `ffmpeg-python` | `python ana.py <video_path>` |
| `main2.py` | `cap.py` 종료 후 최신 `z_*.mp4`/`record_*.mp4`를 `ana.py`로 전달 | 입력: 녹화 결과 파일, 출력: 분석된 mp4 | `subprocess`, 파이프라인 오케스트레이션 | `python main2.py` |
| `mask.py` | OCR 결과에서 주민번호 패턴 탐지 후 뒷자리 영역 마스킹 | 입력: `org/` 이미지, 출력: `upd/` 이미지 | `pytesseract`, `opencv`, `regex` | `python mask.py` |
| `remove.py` | 프레임 추출 -> 하단 영역 인페인팅 -> 동영상 재조립 | 입력: `1.mp4`, 출력: `output_cleaned.mp4` | `opencv`, `ffmpeg` | `python remove.py` |

## 기술 스택 상세

1. PDF: `PyMuPDF`, `reportlab`, `PyPDF2`
2. Video/Image: `opencv-python`, `numpy`, `Pillow`, `mss`
3. Desktop Control: `pynput`, `pyautogui`
4. AI Caption: `torch`, `transformers` (BLIP)
5. TTS/Media Merge: `gTTS`, `ffmpeg`, `ffmpeg-python`
6. OCR/PII: `pytesseract`
7. Cloud Example: `boto3` (Lambda + S3 pattern)
8. Solution Layer: `FastAPI`, `Uvicorn`, `Nginx`, `Docker Compose`

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
python pdf.py

# 2) 화면 녹화
python cap.py

# 3) 특정 영상 AI 분석
python ana.py z_20260301_120000.mp4 --frame-interval 2

# 4) 녹화 후 자동 분석 파이프라인
python main2.py
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

`pdf.py`처럼 stdin 입력이 필요한 작업은 `stdin` 필드를 함께 전달합니다.

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

1. `mask.py`, `remove.py`를 함수형 모듈로 리팩터링해서 API 직접 호출형으로 전환
2. GPU/CPU 워커 분리 배포 전략 수립(캡션 모델 전용 워커)
3. CI에 lint/test + smoke test(docker compose 기반) 추가
