# ============================================
# Stage 1: Base — system deps only
# ============================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ============================================
# Stage 2: Python dependencies
# NOTE: torch is installed CPU-only to reduce image size from ~8 GB to ~3 GB
# ============================================
FROM base AS dependencies

COPY requirements.txt .

# 1) Upgrade pip
RUN pip install --upgrade pip

# 2) Install PyTorch CPU-only FIRST (avoids pulling CUDA wheels ~2.5 GB extra)
RUN pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu

# 3) Install remaining packages (torch already satisfied, so it won't reinstall)
RUN pip install -r requirements.txt

# ============================================
# Stage 3: Development (hot-reload)
# ============================================
FROM dependencies AS development

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Stage 4: Production
# ============================================
FROM dependencies AS production

COPY main.py .
COPY app ./app
COPY models ./models
COPY scripts ./scripts

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
