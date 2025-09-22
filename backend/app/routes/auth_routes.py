from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Student, Admin
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


def hash_password_sha256(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_student_password(password: str, hashed_password: str) -> bool:
    """Verify student password against hash (support both MD5 and SHA256)"""
    # Try SHA256 first (new format)
    if hashlib.sha256(password.encode()).hexdigest() == hashed_password:
        return True
    # Fallback to MD5 (old format)
    return hashlib.md5(password.encode()).hexdigest() == hashed_password


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    API đăng nhập cho admin và sinh viên
    """
    # Admin đăng nhập với database
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if admin:
        # Kiểm tra mật khẩu SHA256
        if admin.password_hash == hash_password_sha256(request.password):
            return LoginResponse(
                user_type="admin",
                user_info={
                    "id": admin.id,
                    "username": admin.username,
                    "email": admin.email,
                    "role": "administrator"
                },
                message="Đăng nhập admin thành công"
            )
    
    # Fallback cho admin cũ (tạm thời)
    if request.email == "admin" and request.password == "admin123":
        return LoginResponse(
            user_type="admin",
            user_info={"username": "admin", "role": "administrator"},
            message="Đăng nhập admin thành công (fallback)"
        )
    
    # Sinh viên đăng nhập bằng email (hỗ trợ cả MD5 và SHA256)
    student = db.query(Student).filter(Student.email == request.email).first()
    
    if student and verify_student_password(request.password, student.login_password):
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
