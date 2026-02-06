# pycap

## 개요
이 저장소는 여러 개의 파이썬 스크립트로 구성되어 있으며, **문서(PDF) 후처리**, **화면 녹화 및 영상 후처리**, **OCR 기반 개인정보 마스킹**, **자막 제거 실험** 등 다양한 자동화 작업을 실험적으로 다룹니다. 각 스크립트는 독립적으로 실행되며, 용도별로 기능이 분리되어 있습니다.【F:main.py†L1-L86】【F:pdf.py†L1-L92】【F:cap.py†L1-L111】【F:start.py†L1-L124】【F:ana.py†L1-L78】【F:mask.py†L1-L59】【F:remove.py†L1-L43】

## 기술 스택
- **언어**: Python
- **문서/PDF 처리**
  - PyMuPDF(fitz), ReportLab, PyPDF2: PDF 렌더링/크기 조정/크롭마크 생성.【F:main.py†L1-L65】【F:pdf.py†L1-L90】
- **영상/이미지 처리**
  - OpenCV, Pillow: 화면 프레임 처리 및 영상 저장.【F:cap.py†L1-L79】【F:start.py†L1-L77】
  - ffmpeg(파이썬 바인딩 포함): 오디오/비디오 병합, 동영상 후처리.【F:ana.py†L1-L78】【F:remove.py†L1-L43】
- **캡처/입력 제어**
  - mss: 화면 캡처.【F:cap.py†L1-L56】【F:start.py†L1-L52】
  - pynput: 글로벌 핫키 처리.【F:cap.py†L1-L108】【F:start.py†L1-L124】
  - pyautogui: 마우스 커서 위치 표시(녹화 프레임 표시용).【F:cap.py†L1-L69】
- **AI/음성**
  - Transformers(BLIP), PyTorch: 이미지 캡셔닝으로 장면 설명 생성.【F:ana.py†L1-L44】
  - gTTS: 설명 텍스트의 음성 합성.【F:ana.py†L1-L72】【F:start.py†L1-L77】
- **OCR**
  - Tesseract OCR(pytesseract): 주민번호 패턴 탐지 후 마스킹.【F:mask.py†L1-L59】
- **AWS 연동**
  - boto3: Lambda 환경에서 S3 기반 PDF 후처리 예시.【F:main.py†L67-L86】

> 참고: `requirements.txt`에는 PDF 처리 라이브러리만 명시되어 있으며, 나머지 의존성은 별도 설치가 필요합니다.【F:requirements.txt†L1-L3】

## 주요 목적 및 스크립트 설명

### 1) PDF 크기 보정 및 크롭마크 삽입
- **`pdf.py`**: 입력 PDF를 지정된 재단 사이즈(460×318mm)에 맞춰 중앙 배치하고 크롭마크를 추가한 뒤 `_work.pdf`로 저장합니다.【F:pdf.py†L1-L92】
- **`main.py`**: `pdf.py`와 유사한 처리를 수행하되, AWS Lambda + S3 트리거 기반 워크플로 예시가 포함되어 있습니다.【F:main.py†L1-L86】

### 2) 화면 녹화 및 간단한 후처리
- **`cap.py`**: 화면을 일정 해상도로 중앙 크롭하여 녹화하고, 녹화 중 마우스 위치를 녹색 원으로 표시합니다. 단축키로 녹화 시작/중지/종료를 제어합니다.【F:cap.py†L1-L111】
- **`start.py`**: `cap.py`와 유사한 화면 녹화 기능을 제공하며, 녹화 후 기본 설명을 TTS로 합성해 영상에 오디오를 병합합니다.【F:start.py†L1-L124】

### 3) 녹화 영상의 AI 캡션/음성 생성
- **`ana.py`**: 영상에서 일정 시간 간격으로 프레임을 추출해 BLIP 모델로 장면 설명을 생성하고, 자막을 입힌 뒤 전체 설명을 gTTS로 음성 합성하여 합칩니다.【F:ana.py†L1-L78】
- **`main2.py`**: `cap.py` 실행 → 녹화 완료 대기 → 가장 최근 mp4를 찾아 `ana.py`로 분석하는 파이프라인 스크립트입니다.【F:main2.py†L1-L27】

### 4) OCR 기반 개인정보 마스킹
- **`mask.py`**: 이미지에서 주민등록번호 패턴을 탐지해 뒷자리 영역을 마스킹(검정 박스) 처리합니다. 폴더 단위 배치 처리도 지원합니다.【F:mask.py†L1-L59】

### 5) 자막 제거 실험
- **`remove.py`**: 영상 프레임을 추출한 뒤, 하단 자막 영역을 인페인팅으로 제거하고 다시 영상으로 합치는 실험 스크립트입니다.【F:remove.py†L1-L43】

## 사용 방법 (예시)
> 각 스크립트는 독립적으로 실행됩니다. 필요한 라이브러리를 먼저 설치하세요.

```bash
# PDF 크롭마크 처리
python pdf.py

# 화면 녹화 (핫키 사용)
python cap.py

# 녹화 + 자동 분석 파이프라인
python main2.py
```
