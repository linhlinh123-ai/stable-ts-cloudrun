FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# FFmpeg cho stable-ts
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Cài torch CPU wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Cài các thư viện còn lại
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY app.py /app/app.py

# Biến môi trường mặc định
ENV WHISPER_MODEL=small \
    LANG_DEFAULT=vi \
    TORCH_NUM_THREADS=1 \
    PYTHONPATH=/app

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
