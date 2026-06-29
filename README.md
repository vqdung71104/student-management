# Student Management System

A web application for suggesting class and subject registration for HUST students.

## Features

- Authentication with JWT-based access control
- Student, department, class, course, and subject management
- Course registration and class registration
- Learned subject tracking and semester GPA tracking
- Feedback and student form handling
- Chatbot support for academic questions, combining rule-based logic, intent classification, NL2SQL, and optional agent tools
- Excel export and reporting utilities

## Tech Stack

### Backend

- FastAPI
- SQLAlchemy
- MySQL
- Redis
- JWT authentication
- Passlib / bcrypt
- Python-based chatbot services and rule engine

### Frontend

- React 19
- TypeScript
- Vite
- Ant Design
- React Router
- Chart.js
- Tailwind CSS

## Project Structure

- `backend/`: FastAPI application, routes, services, chatbot logic, cache/queue helpers, and tests
- `frontend/`: React client for student and admin workflows
- `docker-compose.yml`: Local container setup
- `.env.example`: Environment variable template

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- MySQL 8+
- Redis

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the app at `http://localhost:5173`.

## Environment Variables

Use `.env.example` as the starting point. The most important values are:

- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DB`
- `REDIS_HOST`
- `REDIS_PORT`
- `SECRET_KEY`
- `VITE_API_URL`

If you enable the chatbot agent mode, also configure the LLM-related variables in `.env.example`, especially:

- `AGENT_ENABLED`
- `LLM_SPACE_URL`
- `LLM_API_TOKEN`
- `AGENT_INTERNAL_TOOL_KEY`
- `METRICS_INTERNAL_KEY`

## Tests and Checks

```bash
cd backend
pytest

cd ../frontend
npm run lint
npm run build
```

## Docker

The repository includes Docker support through `docker-compose.yml` and related files.

```bash
docker compose up --build
```
