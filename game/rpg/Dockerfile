# Python 2D RPG – 게임 컨테이너
# 가상 디스플레이(Xvfb)를 통해 헤드리스 환경에서도 실행 가능합니다.
FROM python:3.11-slim

# 시스템 의존성: SDL2 헤드리스 실행을 위한 Xvfb와 pygame 빌드 도구
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# pip 설정 복사 (폐쇄망 Nexus 프록시 사용 시 pip.conf를 활성화)
# COPY pip.conf /etc/pip.conf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Xvfb 가상 디스플레이를 통해 게임 실행
ENV DISPLAY=:99
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & sleep 1 && python gg.py"]
