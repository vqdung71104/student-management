# 🐳 Hướng Dẫn Docker - Tiếng Việt

## 📝 Tổng Quan

Tôi đã tạo một hệ thống Docker hoàn chỉnh cho dự án Student Management System của bạn với các tính năng:

### ✨ Tính Năng Chính

1. **Multi-stage builds** - Tối ưu kích thước image
2. **Health checks** - Tự động kiểm tra sức khỏe services
3. **Hot reload** - Tự động reload khi code thay đổi (development)
4. **Production-ready** - Tối ưu cho môi trường production
5. **Easy management** - Scripts quản lý dễ dàng
6. **Security** - Bảo mật với non-root user, environment variables
7. **Monitoring** - Log rotation, health monitoring

## 📦 Các File Đã Tạo

### 1. Docker Files

#### Backend (`backend/`)
- ✅ `Dockerfile` - Multi-stage build cho Python/FastAPI
- ✅ `.dockerignore` - Loại trừ file không cần thiết
- ✅ `scripts/init.sql` - Khởi tạo database

#### Frontend (`frontend/`)
- ✅ `Dockerfile` - Multi-stage build cho React/Vite
- ✅ `.dockerignore` - Loại trừ file không cần thiết
- ✅ `nginx.conf` - Cấu hình Nginx cho production

### 2. Docker Compose Files

- ✅ `docker-compose.yml` - Development environment
- ✅ `docker-compose.prod.yml` - Production environment
- ✅ `docker-compose.override.example.yml` - Mẫu customization

### 3. Environment Files

- ✅ `.env.docker` - Biến môi trường development
- ✅ `.env.production` - Template cho production

### 4. Management Scripts

- ✅ `docker-manager.ps1` - Script quản lý cho Windows
- ✅ `docker-manager.sh` - Script quản lý cho Linux/Mac
- ✅ `Makefile` - Alternative management interface
- ✅ `healthcheck.ps1` - Kiểm tra health cho Windows
- ✅ `healthcheck.sh` - Kiểm tra health cho Linux/Mac

### 5. Documentation

- ✅ `README.md` - Tài liệu chính của project
- ✅ `DOCKER_GUIDE.md` - Hướng dẫn Docker chi tiết
- ✅ `QUICK_START.md` - Hướng dẫn nhanh
- ✅ `DOCKER_FILES_SUMMARY.md` - Tổng kết các file Docker
- ✅ `DEPLOYMENT_CHECKLIST.md` - Checklist trước khi deploy
- ✅ `HUONG_DAN_DOCKER.md` - File này (tiếng Việt)

### 6. CI/CD

- ✅ `.github/workflows/docker-build.yml` - GitHub Actions workflow

## 🚀 Cách Sử Dụng

### Bước 1: Cài Đặt Docker

1. Tải và cài đặt [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Khởi động Docker Desktop
3. Kiểm tra cài đặt:
   ```powershell
   docker --version
   docker-compose --version
   ```

### Bước 2: Chạy Development Environment

#### Windows (PowerShell):

```powershell
# Khởi động tất cả services
.\docker-manager.ps1 dev:start

# Xem logs
.\docker-manager.ps1 dev:logs

# Kiểm tra health
.\healthcheck.ps1

# Dừng services
.\docker-manager.ps1 dev:stop
```

#### Linux/Mac:

```bash
# Cấp quyền thực thi cho scripts
chmod +x docker-manager.sh healthcheck.sh

# Khởi động tất cả services
make dev-start
# hoặc
./docker-manager.sh dev:start

# Xem logs
make dev-logs

# Kiểm tra health
./healthcheck.sh

# Dừng services
make dev-stop
```

### Bước 3: Truy Cập Ứng Dụng

Sau khi chạy `dev:start`, đợi khoảng 30-60 giây để services khởi động, sau đó truy cập:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **phpMyAdmin**: http://localhost:8080
  - Username: `root`
  - Password: `123456`

## 🔧 Các Lệnh Thường Dùng

### Development

| Mục đích | Windows | Linux/Mac |
|----------|---------|-----------|
| Khởi động | `.\docker-manager.ps1 dev:start` | `make dev-start` |
| Dừng | `.\docker-manager.ps1 dev:stop` | `make dev-stop` |
| Restart | `.\docker-manager.ps1 dev:restart` | `make dev-restart` |
| Xem logs | `.\docker-manager.ps1 dev:logs` | `make dev-logs` |
| Xem logs service cụ thể | `.\docker-manager.ps1 dev:logs backend` | `make dev-logs` |
| Rebuild images | `.\docker-manager.ps1 dev:build` | `make dev-build` |

### Database

| Mục đích | Windows | Linux/Mac |
|----------|---------|-----------|
| Backup | `.\docker-manager.ps1 db:backup` | `make db-backup` |
| Restore | `.\docker-manager.ps1 db:restore backup.sql` | `make db-restore FILE=backup.sql` |
| MySQL Shell | `.\docker-manager.ps1 db:shell` | `make db-shell` |

### Health Check

| Mục đích | Windows | Linux/Mac |
|----------|---------|-----------|
| Kiểm tra health | `.\healthcheck.ps1` | `./healthcheck.sh` |
| Đợi services sẵn sàng | `.\healthcheck.ps1 -Wait` | `./healthcheck.sh --wait` |

## 🏭 Production Deployment

### Bước 1: Chuẩn Bị

1. **Cập nhật file `.env.production`:**

```powershell
# Mở file .env.production và thay đổi:
MYSQL_PASSWORD=mat_khau_manh_cua_ban
SECRET_KEY=secret_key_moi_sinh_ra
GOOGLE_API_KEY=api_key_cua_ban
VITE_API_URL=https://domain-cua-ban.com
```

2. **Tạo SECRET_KEY mới:**

```powershell
# Windows PowerShell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

# Linux/Mac
openssl rand -hex 32
```

### Bước 2: Build và Deploy

```powershell
# Windows
.\docker-manager.ps1 prod:build
.\docker-manager.ps1 prod:start

# Linux/Mac
make prod-build
make prod-start
```

### Bước 3: Kiểm Tra

```powershell
# Kiểm tra health
.\healthcheck.ps1

# Xem logs
docker-compose -f docker-compose.prod.yml logs -f
```

## ❗ Xử Lý Lỗi Thường Gặp

### 1. Port đã được sử dụng

**Lỗi**: `bind: address already in use`

**Giải pháp**:
```powershell
# Tìm process đang dùng port
netstat -ano | findstr :8000

# Kill process hoặc đổi port trong .env.docker
BACKEND_PORT=8001
```

### 2. Database không kết nối được

**Lỗi**: `Can't connect to MySQL server`

**Giải pháp**:
```powershell
# Kiểm tra MySQL container
docker-compose ps

# Xem logs MySQL
docker-compose logs mysql

# Restart MySQL
docker-compose restart mysql

# Đợi 30-60 giây để MySQL khởi động
```

### 3. Frontend không build được

**Lỗi**: `npm run build failed`

**Giải pháp**:
```powershell
# Rebuild không dùng cache
docker-compose build --no-cache frontend

# Xem logs chi tiết
docker-compose logs frontend
```

### 4. Hết dung lượng ổ đĩa

**Lỗi**: `no space left on device`

**Giải pháp**:
```powershell
# Xóa images không dùng
docker image prune -a

# Xóa volumes không dùng
docker volume prune

# Xóa tất cả (CẢNH BÁO: Mất dữ liệu!)
docker system prune -a --volumes
```

## 🔒 Bảo Mật

### ⚠️ QUAN TRỌNG - Trước Khi Deploy Production:

1. ✅ Đổi `MYSQL_PASSWORD` trong `.env.production`
2. ✅ Tạo `SECRET_KEY` mới
3. ✅ Cập nhật `GOOGLE_API_KEY`
4. ✅ Đảm bảo `.env.production` KHÔNG commit lên Git
5. ✅ Cấu hình SSL/HTTPS
6. ✅ Thiết lập firewall
7. ✅ Backup database thường xuyên

## 📊 Monitoring

### Xem Resource Usage

```powershell
# Xem CPU, RAM usage
docker stats

# Xem disk usage
docker system df
```

### Xem Logs

```powershell
# Tất cả services
docker-compose logs -f

# Service cụ thể
docker-compose logs -f backend

# 100 dòng cuối
docker-compose logs --tail=100

# Với timestamp
docker-compose logs -t
```

## 💾 Backup & Restore

### Backup Database

```powershell
# Tự động tạo file backup với timestamp
.\docker-manager.ps1 db:backup

# File sẽ được lưu: backup_YYYYMMDD_HHMMSS.sql
```

### Restore Database

```powershell
# Restore từ file backup
.\docker-manager.ps1 db:restore backup_20260209_120000.sql
```

### Backup Toàn Bộ

```powershell
# Backup volumes
docker run --rm -v student-management_mysql-data:/data -v ${PWD}:/backup ubuntu tar czf /backup/mysql-data-backup.tar.gz /data
```

## 🧹 Cleanup

### Dọn Dẹp Nhẹ

```powershell
# Dừng containers
docker-compose down

# Xóa images không dùng
docker image prune
```

### Dọn Dẹp Hoàn Toàn (CẢNH BÁO: Mất dữ liệu!)

```powershell
# Windows
.\docker-manager.ps1 cleanup

# Linux/Mac
make cleanup
```

## 📚 Tài Liệu Tham Khảo

- **[README.md](README.md)** - Tổng quan dự án
- **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Hướng dẫn Docker chi tiết (English)
- **[QUICK_START.md](QUICK_START.md)** - Hướng dẫn nhanh
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Checklist deploy
- **[DOCKER_FILES_SUMMARY.md](DOCKER_FILES_SUMMARY.md)** - Tổng kết files

## 🆘 Hỗ Trợ

Nếu gặp vấn đề:

1. Kiểm tra logs: `docker-compose logs -f`
2. Kiểm tra health: `.\healthcheck.ps1`
3. Xem [DOCKER_GUIDE.md](DOCKER_GUIDE.md) phần Troubleshooting
4. Restart services: `docker-compose restart`
5. Rebuild: `docker-compose build --no-cache && docker-compose up -d`

## 🎯 Next Steps

1. ✅ Chạy development environment
2. ✅ Test tất cả tính năng
3. ✅ Chuẩn bị production environment
4. ✅ Setup backup tự động
5. ✅ Cấu hình monitoring
6. ✅ Deploy production

---

**Chúc bạn deploy thành công! 🚀**

Nếu cần hỗ trợ thêm, hãy tham khảo các file tài liệu khác hoặc tạo issue trong repository.
