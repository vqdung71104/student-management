from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine
from app.db import database
from app.routes import student_routes
from app.routes import department_routes
from dotenv import load_dotenv

load_dotenv()

database.Base.metadata.create_all(bind=engine)

app = FastAPI(title="University API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_routes.router)
app.include_router(department_routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Management API"}
