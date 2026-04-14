# ============================================
# Stage 1: Base — system deps only
# ============================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300

# Chỉ giữ lại những gì Runtime thực sự cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ============================================
# Stage 2: Builder — Biên dịch (Có gcc/g++)
# ============================================
FROM base AS builder

# Cài đặt công cụ build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# FIX CHÍNH: Cài đặt Torch CPU và requirements trong cùng 1 lệnh 
# để tránh pip tự ý tải bản CUDA nặng 5GB+ từ PyPI
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.5.1 \
    -r requirements.txt

# ============================================
# Stage 3: Production (Tối ưu dung lượng)
# ============================================
FROM base AS production

# Chỉ lấy "thành phẩm" thư viện, loại bỏ hoàn toàn GCC/G++ và Cache build
COPY --from=builder /install /usr/local

# Copy source code (Đảm bảo đã có .dockerignore để không copy venv/ node_modules)
COPY main.py .
COPY app ./app
COPY data ./data
COPY ml_models ./ml_models
COPY scripts ./scripts

# Tạo User để bảo mật, tránh chạy quyền root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Dọn dẹp thêm các file bytecode thừa nếu có
RUN find . -name "__pycache__" -type d -exec rm -rf {} +

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]