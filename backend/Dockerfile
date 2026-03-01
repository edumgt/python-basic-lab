FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.backend.txt
COPY requirements.txt /app/requirements.repo.txt
RUN pip install --no-cache-dir -r /app/requirements.backend.txt -r /app/requirements.repo.txt

COPY backend/app /app/app

ENV WORKSPACE_ROOT=/workspace
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
