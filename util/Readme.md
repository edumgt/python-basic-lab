# Python 스크립트 기술 스택 정리

이 저장소는 **영상/오디오 가공**, **TTS(Text-to-Speech) 생성**, **YouTube 업로드/자동화**, **간단한 데이터 처리/유틸리티** 스크립트들이 섞여 있는 형태입니다.
아래는 Python 파일들에서 실제로 사용되는 기술 스택을 기준으로 정리한 내용입니다.

---

## 1) 실행 환경 및 언어

- 언어: **Python 3.x**
- 실행 형태: 대부분 단일 스크립트 실행 (`python <script>.py`)
- 공통 시스템 의존성:
  - **FFmpeg 바이너리** (subprocess/ffmpeg-python/moviepy/pydub 기반 작업에서 사실상 필수)
  - OS 셸 명령 실행 환경 (여러 스크립트가 `subprocess` 사용)

---

## 2) 핵심 기술 스택 (도메인별)

## A. 영상/오디오 처리

- `subprocess` + FFmpeg CLI
  - 다수 파일에서 FFmpeg 명령을 외부 프로세스로 호출해 변환/병합/자르기 수행
- `moviepy`
  - `concat.py`, `mix.py` 등에서 영상 클립 조합/믹싱에 사용
- `pydub`
  - MP3/WAV/M4A 변환, 오디오 길이/클립 편집 등에 활용
- `ffmpeg` (ffmpeg-python)
  - `cut.py`에서 Python API 형태로 ffmpeg 작업 제어
- `scipy`, `numpy`
  - `piano.py`에서 파형/수치 연산 기반 음성(또는 음원) 처리

### 해당 계열 스크립트 예

`MergeMp4Mp3.py`, `MergeMp4Mp3Loop.py`, `MergeMp4Mp3Loop2.py`, `MergeTextLoop.py`, `WomanMM.py`, `ChampMp4.py`, `sum.py`, `sketch.py`, `mm.py`, `mmm.py`, `mmsp.py`, `mm00.py`, `concat.py`, `mix.py`, `cut.py`, `m4atomp3.py`, `wavetomp3.py`, `piano.py`

---

## B. 음성 합성(TTS) / 텍스트 처리

- `google.cloud` 계열 (Google Cloud TTS)
  - 텍스트를 음성 파일로 생성하는 파이프라인
- `googletrans`
  - 번역을 거쳐 다국어 음성 생성 워크플로우 구성
- `pydub`
  - 생성된 오디오의 후처리(포맷 변환/합치기)

### 해당 계열 스크립트 예

`VoiceToMp3.py`, `VoiceToMp3Kr.py`, `SleepToMp3Kr.py`, `txtmp3.py`, `gen.py`, `gen2.py`

---

## C. YouTube API 자동화

- `googleapiclient`
  - YouTube Data API 호출 (업로드/조회/메타데이터 처리)
- `google_auth_oauthlib`, `pickle`
  - OAuth 인증 및 토큰 캐싱
- `dotenv`
  - 환경 변수 기반 설정 로드
- `argparse`
  - CLI 인자 기반 자동화 실행

### 해당 계열 스크립트 예

`YouTBUp.py`, `yshorts.py`, `yyy.py`

---

## D. 기타 자동화/유틸

- `webbrowser`
  - 브라우저 자동 오픈 보조
- `re`, `datetime`, `random`, `pathlib`, `json`, `time`, `os`
  - 파일명 생성, 문자열 처리, 배치성 실행 로직 등 공통 유틸
- `torch`
  - `Test.py`에서 딥러닝 프레임워크 테스트성 사용

### 해당 계열 스크립트 예

`ypop.py`, `Scr.py`, `Test.py`

---

## 3) Python 파일 기준 사용 라이브러리 맵

- **YouTube/OAuth**: `YouTBUp.py`, `yshorts.py`, `yyy.py`
- **Google TTS/번역**: `VoiceToMp3.py`, `VoiceToMp3Kr.py`, `SleepToMp3Kr.py`, `txtmp3.py`, `gen.py`, `gen2.py`
- **MoviePy 기반 편집**: `concat.py`, `mix.py`
- **Pydub 기반 변환**: `m4atomp3.py`, `wavetomp3.py`, `piano.py` (+ TTS 스크립트 일부)
- **FFmpeg/subprocess 기반 배치 편집**: `Merge*`, `WomanMM.py`, `ChampMp4.py`, `mm*.py`, `sum.py`, `sketch.py`
- **기타**: `Test.py(torch)`, `ypop.py(webbrowser)`, `Scr.py(regex/date/random)`

---

## 4) 의존성 설치 예시

프로젝트 전체를 일괄적으로 쓰기 위한 최소 예시(환경에 맞게 선택 설치 권장):

```bash
pip install moviepy pydub ffmpeg-python numpy scipy torch \
            google-cloud-texttospeech googletrans==4.0.0-rc1 \
            google-api-python-client google-auth-oauthlib python-dotenv
```

추가로 시스템에 FFmpeg 설치가 필요합니다.

---

## 5) 운영 시 참고 사항

- 스크립트들이 공통 모듈로 정리되어 있지 않아, 기능별로 개별 실행/관리하는 구조입니다.
- Google API 사용 스크립트는 인증 키/토큰 파일(`client_secret.json`, pickle 캐시 등) 준비가 필요합니다.
- 멀티미디어 스크립트는 입력 파일 포맷/코덱에 민감하므로 FFmpeg 버전 차이에 따라 동작이 달라질 수 있습니다.
