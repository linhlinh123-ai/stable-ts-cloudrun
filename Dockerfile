FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
WORKDIR /app
COPY app.py /app/app.py
ENV WHISPER_MODEL=small LANG_DEFAULT=vi TORCH_NUM_THREADS=1 PYTHONPATH=/app
EXPOSE 8080
# Dùng shell form để expand $PORT
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
