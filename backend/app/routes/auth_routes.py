from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Student
from pydantic import BaseModel
import hashlib

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_type: str
    user_info: dict
    message: str

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    API đăng nhập cho admin và sinh viên
    """
    # Admin đăng nhập
    if request.email == "admin" and request.password == "admin123":
        return LoginResponse(
            user_type="admin",
            user_info={"username": "admin", "role": "administrator"},
            message="Đăng nhập admin thành công"
        )
    
    # Sinh viên đăng nhập bằng email
    hashed_password = hashlib.md5(request.password.encode()).hexdigest()
    student = db.query(Student).filter(
        Student.email == request.email,
        Student.login_password == hashed_password
    ).first()
    
    if student:
        return LoginResponse(
            user_type="student",
            user_info={
                "student_id": student.student_id,
                "student_name": student.student_name,
                "email": student.email,
                "course_id": student.course_id,
                "classes": student.classes
            },
            message="Đăng nhập sinh viên thành công"
        )
    
    raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")

@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    email: str,
    db: Session = Depends(get_db)
):
    """
    Đổi mật khẩu cho sinh viên
    """
    hashed_current = hashlib.md5(current_password.encode()).hexdigest()
    student = db.query(Student).filter(
        Student.email == email,
        Student.login_password == hashed_current
    ).first()
    
    if not student:
        raise HTTPException(status_code=401, detail="Mật khẩu hiện tại không chính xác")
    
    # Update với mật khẩu mới
    student.login_password = hashlib.md5(new_password.encode()).hexdigest()
    db.commit()
    
    return {"message": "Đổi mật khẩu thành công"}
