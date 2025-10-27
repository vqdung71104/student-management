from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Student, Admin
from app.utils.jwt_utils import create_access_token
from pydantic import BaseModel, EmailStr, validator
import hashlib

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    student_name: str
    email: EmailStr
    password: str
    course_id: int
    department_id: str = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Mật khẩu phải có ít nhất 6 ký tự')
        return v
    
    @validator('student_name')
    def strip_spaces(cls, v):
        return " ".join(v.split())

class LoginResponse(BaseModel):
    user_type: str
    user_info: dict
    message: str
    access_token: str
    token_type: str


def hash_password_sha256(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash (support both MD5 and SHA256)"""
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
    # Admin đăng nhập với database (check by email)
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if admin and verify_password(request.password, admin.password_hash):
        # Create JWT token for admin
        token = create_access_token(data={
            "user_id": admin.id,
            "user_type": "admin",
            "email": admin.email
        })
        
        return LoginResponse(
            user_type="admin",
            user_info={
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "role": "administrator"
            },
            message="Đăng nhập admin thành công",
            access_token=token,
            token_type="bearer"
        )
    
    # Admin đăng nhập với database (check by username for backward compatibility)
    admin_by_username = db.query(Admin).filter(Admin.username == request.email).first()
    if admin_by_username and verify_password(request.password, admin_by_username.password_hash):
        # Create JWT token for admin
        token = create_access_token(data={
            "user_id": admin_by_username.id,
            "user_type": "admin",
            "email": admin_by_username.email
        })
        
        return LoginResponse(
            user_type="admin",
            user_info={
                "id": admin_by_username.id,
                "username": admin_by_username.username,
                "email": admin_by_username.email,
                "role": "administrator"
            },
            message="Đăng nhập admin thành công",
            access_token=token,
            token_type="bearer"
        )
    
    # Sinh viên đăng nhập bằng email (hỗ trợ cả MD5 và SHA256)
    student = db.query(Student).filter(Student.email == request.email).first()
    
    if student and verify_password(request.password, student.password):
        # Create JWT token for student
        token = create_access_token(data={
            "user_id": student.id,
            "user_type": "student",
            "email": student.email
        })
        
        return LoginResponse(
            user_type="student",
            user_info={
                "id": student.id,
                "student_name": student.student_name,
                "email": student.email,
                "course_id": student.course_id
            },
            message="Đăng nhập sinh viên thành công",
            access_token=token,
            token_type="bearer"
        )
    
    raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    API đăng ký tài khoản cho sinh viên
    """
    # Check email đã tồn tại chưa
    existing_student = db.query(Student).filter(Student.email == request.email).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")
    
    # Hash password
    hashed_password = hashlib.md5(request.password.encode()).hexdigest()
    
    # Tạo sinh viên mới
    new_student = Student(
        student_name=request.student_name,
        email=request.email,
        password=hashed_password,
        course_id=request.course_id,
        department_id=request.department_id,
        cpa=0.0,
        failed_subjects_number=0,
        study_subjects_number=0,
        total_failed_credits=0,
        total_learned_credits=0,
        year_level="Trình độ năm 1",
        warning_level="Cảnh cáo mức 0",
        level_3_warning_number=0
    )
    
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    # Create JWT token
    token = create_access_token(data={
        "user_id": new_student.id,
        "user_type": "student",
        "email": new_student.email
    })
    
    return LoginResponse(
        user_type="student",
        user_info={
            "id": new_student.id,
            "student_name": new_student.student_name,
            "email": new_student.email,
            "course_id": new_student.course_id
        },
        message="Đăng ký thành công",
        access_token=token,
        token_type="bearer"
    )

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
