# 2P Network Shooting Game – Lab

**2인용 네트워크 슈팅 게임** | Python asyncio 기반 서버 + HTML5 Canvas 클라이언트

> **Lab:** 이 프로젝트는 Python `asyncio`와 `WebSocket`을 활용한 실시간 네트워크 게임 개발의
> 기초 원리를 학습하는 교육용(lab-style) 예제입니다.  
> GitHub Codespaces에서 바로 실행하고 URL을 공유하면 2인 플레이가 가능합니다.

---

## 아키텍처 (Architecture)

```
Browser (P1) ←──WebSocket──┐
                            ├── server.py  (aiohttp, port 8080)
Browser (P2) ←──WebSocket──┘     │
                                  └── asyncio game loop (30 fps)
                                       서버 권위 물리 엔진
                                       (Server-authoritative physics)
```

| 개념 | 설명 |
|------|------|
| 서버 권위 (Server Authority) | 모든 물리/충돌 연산은 서버에서 수행. 클라이언트는 입력 전송 + 렌더링만 담당 |
| 상태 브로드캐스트 | 매 틱(30fps)마다 전체 게임 상태를 모든 클라이언트에 전송 |
| 최적화 직렬화 | 정수 좌표, 콤팩트 배열(객체 키 대신 배열 인덱스)로 JSON 페이로드 최소화 |
| 로비 / 레디체크 | 2명 접속 후 양측이 모두 START를 눌러야 게임 시작 |

---

## 2인용 네트워크 게임 실행 방법

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 시작
python server.py

# 브라우저 두 탭에서 열기
open http://localhost:8080
```

### GitHub Codespaces (권장)

1. 이 저장소를 Codespaces로 열기
2. 터미널에서 실행:
   ```bash
   pip install -r requirements.txt
   python server.py
   ```
3. VS Code 하단 **PORTS** 탭에서 포트 `8080` 확인
4. 포트 가시성을 **Public** 으로 변경
5. 전달된 URL을 Player 2에게 공유 → 둘 다 URL을 브라우저에서 열기
6. 두 플레이어 모두 **READY / START** 버튼 클릭 → 게임 시작!

---

## 게임 조작법

| 키 | 동작 |
|----|------|
| `←` / `→` | 좌우 이동 |
| `Space` (홀드) | 연속 발사 |
| `X` | 폭탄 (화면 전체 적 제거) |

---

## 게임 규칙

- 목숨 3개로 시작, 적 충돌/총알에 맞으면 감소
- 적 처치 시 점수 +10, 콤보 보너스
- 파워업 획득 시 멀티샷(최대 5발) / 실드 / 레이저 / 래피드 파이어 활성화
- 매 5웨이브마다 보스 등장
- 두 플레이어 모두 목숨이 0이 되면 게임 오버
- 게임 오버 후 **RESTART** 버튼으로 재시작

---

## 파일 구조

```
.
├── server.py              # 🖥  Python asyncio 게임 서버 (HTTP + WebSocket)
├── static/
│   └── index.html         # 🌐  HTML5 Canvas 웹 클라이언트 (단일 파일)
├── game.py                # 🎮  단일 플레이어 pygame 버전 (기존)
├── requirements.txt       # 📦  Python 의존성 (aiohttp)
├── .devcontainer/
│   └── devcontainer.json  # ☁️  GitHub Codespaces 설정
└── README.md
```

---

## 단일 플레이어 (pygame 버전)

기존 단일 플레이어 게임은 `game.py`로 유지됩니다.

```bash
pip install pygame
python game.py
```

### 단일 플레이어 조작법
- `←` / `→` : 좌우 이동
- `Space` : 발사
- `Shift` : 대시
- `X` : 폭탄
- `P` : 일시정지
- `R` : 게임 오버 시 재시작
