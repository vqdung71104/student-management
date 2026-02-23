# 🐳 Docker Deployment Guide

Hướng dẫn triển khai dự án Student Management System sử dụng Docker.

## 📋 Mục lục

- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cấu trúc Docker](#cấu-trúc-docker)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [Quản lý Docker](#quản-lý-docker)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## 🔧 Yêu cầu hệ thống

- **Docker**: >= 20.10.0
- **Docker Compose**: >= 2.0.0
- **RAM**: >= 4GB (khuyến nghị 8GB)
- **Disk Space**: >= 10GB

### Kiểm tra phiên bản

```bash
docker --version
docker-compose --version
```

## 📁 Cấu trúc Docker

```
student-management/
├── backend/
│   ├── Dockerfile              # Multi-stage build cho backend
│   ├── .dockerignore          # Loại trừ file không cần thiết
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── Dockerfile             # Multi-stage build cho frontend
│   ├── .dockerignore         # Loại trừ file không cần thiết
│   ├── nginx.conf            # Nginx configuration
│   └── package.json          # Node dependencies
├── docker-compose.yml         # Development configuration
├── docker-compose.prod.yml    # Production configuration
├── .env.docker               # Development environment variables
├── .env.production           # Production environment variables
├── docker-manager.sh         # Bash management script
└── docker-manager.ps1        # PowerShell management script
```

## 🚀 Cài đặt và chạy

### Development Mode

#### Sử dụng Docker Compose trực tiếp

```bash
# 1. Copy environment file
cp .env.docker .env

# 2. Start all services
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop services
docker-compose down
```

#### Sử dụng Docker Manager Script

**Windows (PowerShell):**
```powershell
# Start development environment
.\docker-manager.ps1 dev:start

# View logs
.\docker-manager.ps1 dev:logs

# View specific service logs
.\docker-manager.ps1 dev:logs backend

# Stop environment
.\docker-manager.ps1 dev:stop
```

**Linux/Mac (Bash):**
```bash
# Make script executable
chmod +x docker-manager.sh

# Start development environment
./docker-manager.sh dev:start

# View logs
./docker-manager.sh dev:logs

# Stop environment
./docker-manager.sh dev:stop
```

### Production Mode

#### Chuẩn bị

1. **Cập nhật file `.env.production`:**
```bash
# QUAN TRỌNG: Thay đổi các giá trị sau
MYSQL_PASSWORD=your_strong_password
SECRET_KEY=generate_new_secret_key
GOOGLE_API_KEY=your_api_key
```

2. **Generate SECRET_KEY mới:**
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

#### Deploy Production

**Windows:**
```powershell
# Build production images
.\docker-manager.ps1 prod:build

# Start production environment
.\docker-manager.ps1 prod:start

# Check health
.\docker-manager.ps1 health
```

**Linux/Mac:**
```bash
# Build production images
./docker-manager.sh prod:build

# Start production environment
./docker-manager.sh prod:start

# Check health
./docker-manager.sh health
```

## 🎯 Các Service

### Development Mode

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Frontend | 5173 | http://localhost:5173 | React Development Server |
| Backend | 8000 | http://localhost:8000 | FastAPI Server |
| MySQL | 3306 | localhost:3306 | MySQL Database |
| phpMyAdmin | 8080 | http://localhost:8080 | Database Management (optional) |

### Production Mode

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Frontend | 80 | http://localhost | Nginx Static Server |
| Backend | Internal | - | FastAPI Server (internal only) |
| MySQL | Internal | - | MySQL Database (internal only) |

## 🛠️ Quản lý Docker

### Docker Manager Commands

#### Development Commands

```bash
# Start development environment
dev:start

# Stop development environment
dev:stop

# Restart services
dev:restart

# View all logs
dev:logs

# View specific service logs
dev:logs [service_name]  # backend, frontend, mysql

# Rebuild images
dev:build
```

#### Production Commands

```bash
# Start production environment
prod:start

# Stop production environment
prod:stop

# Build production images
prod:build
```

#### Database Commands

```bash
# Create database backup
db:backup

# Restore database from backup
db:restore [backup_file]

# Open MySQL shell
db:shell
```

#### Utility Commands

```bash
# Check service health
health

# Clean up all containers and volumes
cleanup

# Show help
help
```

### Manual Docker Commands

#### Container Management

```bash
# List running containers
docker-compose ps

# View container logs
docker-compose logs -f [service_name]

# Execute command in container
docker-compose exec [service_name] [command]

# Restart specific service
docker-compose restart [service_name]

# Stop specific service
docker-compose stop [service_name]
```

#### Database Operations

```bash
# Access MySQL shell
docker-compose exec mysql mysql -u root -p

# Create backup
docker-compose exec mysql mysqldump -u root -p student_management > backup.sql

# Restore backup
docker-compose exec -T mysql mysql -u root -p student_management < backup.sql

# View database logs
docker-compose logs mysql
```

#### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect student-management_mysql-data

# Remove volumes (WARNING: Data loss!)
docker-compose down -v
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:**
```
Error starting userland proxy: listen tcp 0.0.0.0:8000: bind: address already in use
```

**Solution:**
```bash
# Find process using the port
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Kill the process or change port in .env.docker
BACKEND_PORT=8001
```

#### 2. Database Connection Failed

**Error:**
```
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solution:**
```bash
# Check if MySQL is healthy
docker-compose ps

# View MySQL logs
docker-compose logs mysql

# Restart MySQL
docker-compose restart mysql

# Wait for MySQL to be ready (30-60 seconds)
```

#### 3. Frontend Build Failed

**Error:**
```
ERROR: failed to solve: process "/bin/sh -c npm run build" did not complete successfully
```

**Solution:**
```bash
# Clear Docker cache
docker-compose build --no-cache frontend

# Check Node version in Dockerfile
# Ensure package.json is valid
```

#### 4. Permission Denied (Linux)

**Error:**
```
Permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again
# Or use sudo
sudo docker-compose up -d
```

#### 5. Out of Disk Space

**Error:**
```
no space left on device
```

**Solution:**
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything (WARNING!)
docker system prune -a --volumes
```

### Health Checks

```bash
# Check all services
docker-compose ps

# Check backend health
curl http://localhost:8000/

# Check frontend health
curl http://localhost:5173/

# Check MySQL health
docker-compose exec mysql mysqladmin ping -h localhost -u root -p
```

### Logs Analysis

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific service
docker-compose logs -f backend

# View logs with timestamps
docker-compose logs -t
```

## 📊 Monitoring

### Container Stats

```bash
# View resource usage
docker stats

# View specific container
docker stats student-management-backend
```

### Log Files

Logs are stored in JSON format with rotation:
- Max size: 10MB (dev) / 50MB (prod)
- Max files: 3 (dev) / 5 (prod)

## 🔒 Security Best Practices

### Production Deployment

1. **Change all default passwords:**
   - MySQL root password
   - JWT secret key
   - API keys

2. **Use environment variables:**
   - Never commit `.env.production` to git
   - Use secrets management in production

3. **Network security:**
   - Only expose necessary ports
   - Use reverse proxy (Nginx/Traefik)
   - Enable HTTPS/SSL

4. **Regular updates:**
   ```bash
   # Update base images
   docker-compose pull
   
   # Rebuild with latest dependencies
   docker-compose build --no-cache
   ```

5. **Backup strategy:**
   ```bash
   # Automated daily backups
   0 2 * * * /path/to/docker-manager.sh db:backup
   ```

## 🚢 Deployment to Cloud

### Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag images
docker tag student-management-backend:latest username/student-backend:latest
docker tag student-management-frontend:latest username/student-frontend:latest

# Push images
docker push username/student-backend:latest
docker push username/student-frontend:latest
```

### AWS ECS / Azure Container Instances / GCP Cloud Run

Refer to platform-specific documentation for deploying Docker Compose applications.

## 📝 Environment Variables Reference

### Backend (.env.docker)

| Variable | Description | Default |
|----------|-------------|---------|
| MYSQL_USER | Database user | root |
| MYSQL_PASSWORD | Database password | 123456 |
| MYSQL_DB | Database name | student_management |
| SECRET_KEY | JWT secret key | (generated) |
| GOOGLE_API_KEY | Google AI API key | - |
| USE_PHOBERT | Enable PhoBERT | true |
| USE_GEMINI | Enable Gemini | true |

### Frontend (.env.docker)

| Variable | Description | Default |
|----------|-------------|---------|
| VITE_API_URL | Backend API URL | http://localhost:8000 |
| NODE_ENV | Node environment | development |

## 🤝 Contributing

Khi thêm dependencies mới:

1. **Backend:** Thêm vào `requirements.txt` và rebuild
2. **Frontend:** Thêm vào `package.json` và rebuild

```bash
# Rebuild after adding dependencies
docker-compose build --no-cache
```

## 📞 Support

Nếu gặp vấn đề:

1. Check logs: `docker-compose logs -f`
2. Check health: `./docker-manager.sh health`
3. Restart services: `docker-compose restart`
4. Clean rebuild: `docker-compose down && docker-compose build --no-cache && docker-compose up -d`

---

**Happy Dockerizing! 🐳**
