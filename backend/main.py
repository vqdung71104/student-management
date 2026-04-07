from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from app.db.database import engine
from app.db import database
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
from app.utils.jwt_utils import get_current_user
from dotenv import load_dotenv

load_dotenv()

database.Base.metadata.create_all(bind=engine)

app = FastAPI(title="University API")

raw_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Management API"}
