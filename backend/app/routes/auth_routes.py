from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Student, Admin
from app.utils.jwt_utils import create_access_token, get_current_student, get_current_user
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

from app.core.config import settings
from app.services.email_service import email_service
from app.services.password_reset_service import password_reset_service
from app.utils.password_utils import hash_password, verify_password, needs_rehash

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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        return v


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=30 * 24 * 60 * 60,
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    API đăng nhập cho admin và sinh viên
    """
    # Admin đăng nhập với database (check by email)
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if admin and verify_password(request.password, admin.password_hash):
        if needs_rehash(admin.password_hash):
            admin.password_hash = hash_password(request.password)
            admin.password_updated_at = datetime.now()
            db.commit()

        # Create JWT token for admin
        token = create_access_token(data={
            "user_id": admin.id,
            "user_type": "admin",
            "email": admin.email
        })

        _set_auth_cookie(response, token)

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
        if needs_rehash(admin_by_username.password_hash):
            admin_by_username.password_hash = hash_password(request.password)
            admin_by_username.password_updated_at = datetime.now()
            db.commit()

        # Create JWT token for admin
        token = create_access_token(data={
            "user_id": admin_by_username.id,
            "user_type": "admin",
            "email": admin_by_username.email
        })

        _set_auth_cookie(response, token)

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
        if needs_rehash(student.password):
            student.password = hash_password(request.password)
            student.password_updated_at = datetime.now()
            db.commit()

        # Create JWT token for student
        token = create_access_token(data={
            "user_id": student.id,
            "user_type": "student",
            "email": student.email
        })

        _set_auth_cookie(response, token)

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
def register(request: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """
    API đăng ký tài khoản cho sinh viên
    """
    # Check email đã tồn tại chưa
    existing_student = db.query(Student).filter(Student.email == request.email).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")
    
    # Hash password
    hashed_password = hash_password(request.password)
    
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
    
    _set_auth_cookie(response, token)

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
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    Đổi mật khẩu cho sinh viên
    """
    if not verify_password(current_password, current_student.password):
        raise HTTPException(status_code=401, detail="Mật khẩu hiện tại không chính xác")
    if verify_password(new_password, current_student.password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")

    # Update với mật khẩu mới
    current_student.password = hash_password(new_password)
    current_student.password_updated_at = datetime.now()
    db.commit()
    
    return {"message": "Đổi mật khẩu thành công"}


@router.get("/me")
def me(current_user = Depends(get_current_user)):
    """Quick check endpoint for current authenticated identity."""
    if isinstance(current_user, Admin):
        return {
            "authenticated": True,
            "user_type": "admin",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username,
            },
        }

    return {
        "authenticated": True,
        "user_type": "student",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "student_name": current_user.student_name,
        },
    }


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Always return neutral response to avoid account enumeration.
    neutral = ForgotPasswordResponse(
        message="Nếu email tồn tại, hệ thống đã gửi link đặt lại mật khẩu."
    )

    user_type, user_id = password_reset_service.find_user_by_email(db, payload.email)
    if not user_type or not user_id:
        print(f"[FORGOT_PASSWORD] email not found: {payload.email}")
        return neutral

    if not password_reset_service.check_rate_limit(db, payload.email):
        print(f"[FORGOT_PASSWORD] rate limit exceeded for: {payload.email}")
        return neutral

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    token = password_reset_service.create_reset_token(
        db=db,
        user_type=user_type,
        user_id=user_id,
        email=payload.email,
        request_ip=client_ip,
        user_agent=user_agent,
    )
    print(f"[FORGOT_PASSWORD] token created for {payload.email} ({user_type}:{user_id})")

    reset_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password?token={token}"
    sent = email_service.send_reset_password_email(payload.email, reset_url)
    if not sent:
        print(f"[FORGOT_PASSWORD] send mail failed for: {payload.email}")
    else:
        print(f"[FORGOT_PASSWORD] send mail success for: {payload.email}")
    return neutral


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_row = password_reset_service.verify_reset_token(db, payload.token)
    if not token_row:
        raise HTTPException(status_code=400, detail="Token không hợp lệ hoặc đã hết hạn")

    if token_row.user_type == "student":
        user = db.query(Student).filter(Student.id == token_row.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User không tồn tại")
        user.password = hash_password(payload.new_password)
        user.password_updated_at = datetime.now()
    elif token_row.user_type == "admin":
        user = db.query(Admin).filter(Admin.id == token_row.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User không tồn tại")
        user.password_hash = hash_password(payload.new_password)
        user.password_updated_at = datetime.now()
    else:
        raise HTTPException(status_code=400, detail="Token không hợp lệ")

    db.commit()
    password_reset_service.mark_token_used(db, token_row)
    return {"message": "Đặt lại mật khẩu thành công"}


@router.get("/reset-password/validate")
def validate_reset_password_token(token: str, db: Session = Depends(get_db)):
    token_row = password_reset_service.verify_reset_token(db, token)
    return {"valid": bool(token_row)}
