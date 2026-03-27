# ============================================
# Stage 1: Base — system deps only
# ============================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300

# Base này chỉ giữ lại những gì Runtime thực sự cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ============================================
# Stage 2: Builder — Dùng để biên dịch (Có gcc/g++)
# ============================================
FROM base AS builder

# Cài đặt gcc/g++ ở đây để phục vụ việc build thư viện
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

# Cài đặt mọi thứ vào thư mục /install để copy sang stage sau cho sạch
RUN pip install --no-cache-dir --prefix=/install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================
# Stage 3: Development (hot-reload)
# ============================================
FROM builder AS development
# Copy thư viện từ folder /install vào path mặc định của python
COPY --from=builder /install /usr/local

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Stage 4: Production
# ============================================
FROM base AS production

# Lấy "thành phẩm" thư viện đã build xong, không lấy gcc/g++
COPY --from=builder /install /usr/local

COPY main.py .
COPY app ./app
COPY data ./data
COPY ml_models ./ml_models
COPY scripts ./scripts

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]