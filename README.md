# 🎓 Student Management System

A comprehensive student management system built with FastAPI (Python) backend and React (TypeScript) frontend, featuring AI-powered chatbot assistance.

## 🚀 Features

- **Student Management**: Complete CRUD operations for student records
- **Course Management**: Manage courses, subjects, and class schedules
- **Grade Tracking**: Semester GPA calculation and tracking
- **AI Chatbot**: Natural language query support with PhoBERT and Google Gemini
- **Authentication**: Secure JWT-based authentication
- **Feedback System**: Student feedback and forms management
- **Excel Export**: Export data to Excel format

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **AI/ML**: PhoBERT, Google Gemini, Underthesea

### Frontend
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Ant Design
- **Routing**: React Router v7
- **Charts**: Chart.js
- **Styling**: Tailwind CSS

## 📦 Docker Deployment

This project is fully containerized with Docker for easy deployment.

### Quick Start with Docker

#### Development Mode

**Windows:**
```powershell
# Start all services
.\docker-manager.ps1 dev:start

# View logs
.\docker-manager.ps1 dev:logs

# Stop services
.\docker-manager.ps1 dev:stop
```

**Linux/Mac:**
```bash
# Start all services
make dev-start

# View logs
make dev-logs

# Stop services
make dev-stop
```

#### Production Mode

**Windows:**
```powershell
# 1. Update .env.production with your credentials
# 2. Build and start
.\docker-manager.ps1 prod:build
.\docker-manager.ps1 prod:start
```

**Linux/Mac:**
```bash
# 1. Update .env.production with your credentials
# 2. Build and start
make prod-build
make prod-start
```

### Access Services

| Service | Development | Production |
|---------|-------------|------------|
| Frontend | http://localhost:5173 | http://localhost:80 |
| Backend API | http://localhost:8000 | Internal only |
| API Docs | http://localhost:8000/docs | - |
| phpMyAdmin | http://localhost:8080 | - |

### Docker Documentation

- **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Complete deployment guide with troubleshooting
- **[QUICK_START.md](QUICK_START.md)** - Quick reference for common commands
- **[DOCKER_FILES_SUMMARY.md](DOCKER_FILES_SUMMARY.md)** - Overview of all Docker files

## 🔧 Manual Installation (Without Docker)

### Prerequisites

- Python 3.11+
- Node.js 20+
- MySQL 8.0+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure .env file
cp .env.example .env
# Edit .env with your database credentials

# Run migrations (tables will be created automatically)
# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📊 Database Schema

The system includes the following main entities:

- Students
- Departments
- Classes
- Courses
- Subjects
- Learned Subjects
- Semester GPA
- Feedback
- Student Forms

Tables are automatically created by SQLAlchemy on first run.

## 🤖 AI Chatbot

The system includes an intelligent chatbot that can:

- Answer questions in Vietnamese using natural language
- Query student information, grades, and schedules
- Support both PhoBERT and Google Gemini models
- Hybrid strategy for optimal responses

Configure in `.env`:
```
USE_PHOBERT=true
USE_GEMINI=true
CHATBOT_STRATEGY=hybrid
GOOGLE_API_KEY=your_api_key
```

## 🔐 Security

- JWT-based authentication
- Password hashing with Argon2
- CORS configuration
- Environment variable management
- SQL injection protection via ORM

## 📝 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🚢 Deployment

### Docker (Recommended)

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for detailed deployment instructions.

### Manual Deployment

1. **Backend**: Use Gunicorn or Uvicorn with multiple workers
2. **Frontend**: Build and serve with Nginx
3. **Database**: Use managed MySQL service or self-hosted
4. **SSL**: Configure reverse proxy (Nginx/Traefik) with Let's Encrypt

## 📋 Environment Variables

### Backend (.env)

```env
# Database
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=student_management

# Redis (local run)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI
GOOGLE_API_KEY=your_api_key
USE_PHOBERT=true
USE_GEMINI=true
CHATBOT_STRATEGY=hybrid
```

When running with Docker Compose, backend must use service hostnames in the container network:

```env
MYSQL_HOST=mysql
REDIS_HOST=redis
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React team for the UI library
- Ant Design for beautiful components
- Google for Gemini AI
- VinAI for PhoBERT model

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for troubleshooting

---

**Happy Coding! 🚀**