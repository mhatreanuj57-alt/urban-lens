# Build from the repository root so the model weights are reachable:
#   docker build -f backend/Dockerfile --build-arg ML_INSTALL=1 -t urbanlens-backend .
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# libgl1/libglib2.0-0 are what opencv-python-headless dlopen at import time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ML_INSTALL=1 adds ultralytics + CPU-only torch so detection runs in the cloud.
# Left at 0 for the free tier: the pipeline degrades to "detection skipped".
ARG ML_INSTALL=0
RUN if [ "$ML_INSTALL" = "1" ]; then \
      pip install --no-cache-dir "ultralytics==8.3.40" \
        torch torchvision --index-url https://download.pytorch.org/whl/cpu; \
    fi

COPY backend/ ./
COPY ml/models/ /models/
ENV ML_MODEL_PATH=/models

EXPOSE 8000

# Exec form: docker leaves ${PORT} alone, so the shell resolves it at runtime.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD ["sh", "-c", "curl -fsS \"http://127.0.0.1:${PORT:-8000}/health\" || exit 1"]

# Render injects PORT; local runs fall back to 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
