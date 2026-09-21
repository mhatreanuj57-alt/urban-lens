# Build from the repository root so the model weights are reachable:
#   docker build -f backend/Dockerfile -t urbanlens-backend .
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

# Detection runs on the exported ONNX graph from ml/models (requirements pulls
# in onnxruntime), which keeps torch out of the image so detection fits the
# 512 MB free tier. `yolo export` regenerates it:
#   yolo export model=ml/models/urbanlens_yolov8_v1.pt format=onnx opset=18 simplify=False

COPY backend/ ./
COPY ml/models/ /models/
ENV ML_MODEL_PATH=/models

EXPOSE 8000

# Exec form: docker leaves ${PORT} alone, so the shell resolves it at runtime.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD ["sh", "-c", "curl -fsS \"http://127.0.0.1:${PORT:-8000}/health\" || exit 1"]

# Render injects PORT; local runs fall back to 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
