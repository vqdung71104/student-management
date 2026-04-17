from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import text
from app.db.database import engine
from app.db import database
from app.db.database import SessionLocal
from app.routes import student_routes
from app.routes import department_routes
from app.routes import class_routes
from app.routes import class_register_routes
from app.routes import course_routes
from app.routes import course_subject_routes
from app.routes import learned_subject_routes
from app.routes import semester_gpa_routes
from app.routes import subject_routes
from app.routes import subject_register_routes
from app.routes import auth_routes
from app.routes import feedback_routes
from app.routes import admin_password_routes
from app.routes import student_password_routes
from app.routes import student_forms_routes
from app.routes import chatbot_routes
from app.routes import agent_tool_routes
from app.utils.jwt_utils import get_current_user
from dotenv import load_dotenv
from app.agents.orchestration_metrics import get_orchestration_metrics
from app.agents.orchestration_alerts import evaluate_orchestration_alerts
from app.llm.llm_client import LLMClient

try:
    from app.cache.redis_cache import get_redis_cache
except Exception:
    get_redis_cache = None

load_dotenv()

database.Base.metadata.create_all(bind=engine)

app = FastAPI(title="University API")


def _is_agent_enabled() -> bool:
    return os.getenv("AGENT_ENABLED", "false").strip().lower() == "true"


def _validate_agent_env_or_raise() -> None:
    if not _is_agent_enabled():
        return

    missing = []
    llm_space_url = os.getenv("LLM_SPACE_URL", "").strip()
    internal_key = os.getenv("AGENT_INTERNAL_TOOL_KEY", "").strip()

    if not llm_space_url:
        missing.append("LLM_SPACE_URL")
    if not internal_key:
        missing.append("AGENT_INTERNAL_TOOL_KEY")

    if missing:
        raise RuntimeError(f"Missing required agent env vars: {', '.join(missing)}")

    if internal_key == "dev-agent-key" or len(internal_key) < 24:
        raise RuntimeError("AGENT_INTERNAL_TOOL_KEY must be strong in production (>=24 chars and not default)")


@app.on_event("startup")
def _startup_validation() -> None:
    _validate_agent_env_or_raise()


def _check_db_ready() -> dict:
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        session.close()


def _check_redis_ready() -> dict:
    if get_redis_cache is None:
        return {"status": "error", "error": "redis cache module unavailable"}
    try:
        cache = get_redis_cache()
        cache.client.ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


async def _check_llm_ready() -> dict:
    if not _is_agent_enabled():
        return {"status": "skipped", "reason": "agent disabled"}
    try:
        llm = LLMClient()
        state = llm.circuit_state()
        await llm.close()
        return {"status": "ok", "circuit": state}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

# Load CORS origins from env. Default includes localhost for dev and https://learnbuild.dev for production.
raw_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,https://learnbuild.dev",
)
cors_origins = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Account management + system data
app.include_router(student_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
# Course/Department GET endpoints are public; write endpoints enforce auth at route level.
app.include_router(department_routes.router, prefix="/api")
app.include_router(class_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(course_routes.router, prefix="/api")
app.include_router(course_subject_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(subject_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])

# Student-private data: student only
app.include_router(class_register_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(learned_subject_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(semester_gpa_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(subject_register_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])

# Public auth endpoints
app.include_router(auth_routes.router, prefix="/api")

# Admin-only operations
app.include_router(feedback_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(admin_password_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])

# Student-only operations
app.include_router(student_password_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(student_forms_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(chatbot_routes.router, prefix="/api", dependencies=[Depends(get_current_user)])
app.include_router(agent_tool_routes.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Management API"}


@app.get("/health/live")
def health_live():
    return {
        "status": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready")
async def health_ready():
    db_status = _check_db_ready()
    redis_status = _check_redis_ready()
    llm_status = await _check_llm_ready()

    checks = {
        "db": db_status,
        "redis": redis_status,
        "llm": llm_status,
    }
    ready = all(v.get("status") in {"ok", "skipped"} for v in checks.values())
    return {
        "status": "ready" if ready else "degraded",
        "agent_enabled": _is_agent_enabled(),
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/internal/metrics/orchestration")
def orchestration_metrics_snapshot(
    x_internal_metrics_key: str | None = Header(default=None, alias="X-Internal-Metrics-Key"),
):
    expected = os.getenv("METRICS_INTERNAL_KEY", os.getenv("AGENT_INTERNAL_TOOL_KEY", "")).strip()
    if expected and x_internal_metrics_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    return get_orchestration_metrics().snapshot()


@app.get("/internal/alerts/orchestration")
def orchestration_alerts_snapshot(
    x_internal_metrics_key: str | None = Header(default=None, alias="X-Internal-Metrics-Key"),
):
    expected = os.getenv("METRICS_INTERNAL_KEY", os.getenv("AGENT_INTERNAL_TOOL_KEY", "")).strip()
    if expected and x_internal_metrics_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    snapshot = get_orchestration_metrics().snapshot()
    return evaluate_orchestration_alerts(snapshot)
