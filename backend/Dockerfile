# Sử dụng image Python 3.11
FROM python:3.11

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép requirements.txt trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ source code
COPY . .

# Expose cổng FastAPI
EXPOSE 8000

# Lệnh khởi chạy ứng dụng (với auto-reload cho development)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]