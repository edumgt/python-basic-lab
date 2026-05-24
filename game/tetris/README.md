# Python Tetris Room Match

`Python + pygame-ce + pygame_gui`로 만든 2인 실시간 대전 테트리스입니다.

핵심 목표:
- 방 생성/입장
- 2명 모두 READY 후에만 게임 시작
- 게임 하단 실시간 채팅
- 경기 종료 후 다시 READY로 다음 판 진행

---

## 1. 주요 기능

### 로비/방 시스템
- 방 생성 (`Create Room`)
- 방 코드로 입장 (`Join Room`)
- 방 최대 인원 2명
- 각 플레이어 READY 상태 표시
- **두 플레이어 모두 READY일 때만** 자동 게임 시작

### 채팅
- 게임 화면 하단 채팅 박스 제공
- 같은 방 플레이어끼리 채팅 전송/수신

### 대전 플레이
- 라인 삭제 기반 점수/레벨
- 공격(garbage line) 전송
  - 2줄 삭제 -> 1줄 공격
  - 3줄 삭제 -> 2줄 공격
  - 4줄 삭제 -> 4줄 공격
- 한쪽이 먼저 죽으면 승패 판정, 다음 판 READY 대기

### 단일 실행파일(원파일) 지원
- Windows: `tetris.exe`
- Linux: `tetris`
- 동일 실행파일에서 모드 선택 가능
  - 클라이언트: 기본 실행
  - 서버: `--server` 옵션

### 로컬 임베디드 서버 자동 시작
- 클라이언트에서 `127.0.0.1`(또는 `localhost`) 연결 시 서버가 없으면 내부적으로 서버를 자동 기동
- 한 PC 테스트 편의성 개선

---

## 2. 프로젝트 구조

- `tet.py`: 클라이언트(UI + 로비 + 게임 로직)
- `server.py`: TCP 방 서버(방/채팅/ready/game_start 관리)
- `main.py`: 단일 실행파일 진입점 (`--server` 지원)
- `ui_theme.json`: pygame_gui 테마
- `requirements.txt`: 런타임 의존성
- `requirements-build.txt`: 빌드용 의존성(PyInstaller 포함)
- `tetris.spec`: PyInstaller one-file 설정
- `build_exe.py`: 로컬 빌드 스크립트
- `.github/workflows/build-windows-exe.yml`: Windows/Linux 바이너리 빌드 CI

---

## 3. Python으로 실행(개발 모드)

## 설치

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 실행

### 방법 A) 서버 따로 실행

1. 서버 실행
```bash
python3 server.py --host 0.0.0.0 --port 9009
```

2. 각 플레이어 클라이언트 실행
```bash
python3 tet.py
```

### 방법 B) 한 PC 간단 테스트

- `python3 tet.py` 실행 후 호스트를 `127.0.0.1`, 포트를 `9009`로 두고 `Create Room` 클릭
- 서버가 없으면 임베디드 서버가 자동 실행됨

---

## 4. 단일 실행파일로 실행

## Windows

- 클라이언트:
```bash
tetris.exe
```

- 서버:
```bash
tetris.exe --server --host 0.0.0.0 --port 9009
```

## Linux

- 클라이언트:
```bash
./tetris
```

- 서버:
```bash
./tetris --server --host 0.0.0.0 --port 9009
```

---

## 5. 게임 시작 플로우

1. 플레이어 1이 방 생성
2. 플레이어 2가 방 코드로 입장
3. 하단 채팅으로 대화
4. 양쪽 모두 `Start (Ready)` 클릭
5. 서버가 두 사람 READY를 확인하면 자동 시작

---

## 6. 조작키

- 좌/우 이동: `←/→` 또는 `A/D`
- 소프트 드랍: `↓` 또는 `S`
- 회전: `↑` 또는 `W`
- 하드 드랍: `Space` 또는 `Shift`
- 종료: `ESC`

---

## 7. 빌드

## 로컬 빌드

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-build.txt
python3 build_exe.py
```

산출물:
- Windows: `dist/tetris.exe`
- Linux/macOS: `dist/tetris`

## GitHub Actions 자동 빌드

워크플로 파일: `.github/workflows/build-windows-exe.yml`

실행 결과 아티팩트:
- `tetris-windows-exe` -> `tetris.exe`
- `tetris-linux` -> `tetris`

---

## 8. 참고

- 가상환경/빌드 산출물은 `.gitignore`에 반영되어 있습니다 (`venv`, `.venv`, `dist`, `build` 등).
