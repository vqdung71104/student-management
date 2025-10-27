from pydantic import BaseModel, validator, EmailStr
from typing import Optional
from datetime import datetime
import re


class StudentBase(BaseModel):
    """Base fields that can be manually set"""
    student_name: str
    email: EmailStr
    course_id: int
    department_id: Optional[str] = None

    @validator("student_name")
    def strip_spaces(cls, v):
        return " ".join(v.split())


class StudentCreate(StudentBase):
    """Schema for creating students - includes password"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        """Kiểm tra mật khẩu"""
        if len(v) < 6:
            raise ValueError('Mật khẩu phải có ít nhất 6 ký tự')
        return v


class StudentUpdate(BaseModel):
    """Schema for updating students - only manually editable fields"""
    student_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department_id: Optional[str] = None
    course_id: Optional[int] = None

    @validator("student_name")
    def strip_spaces(cls, v):
        if v is not None:
            return " ".join(v.split())
        return v


class StudentResponse(BaseModel):
    """Schema for response - includes all fields including auto-calculated ones"""
    id: int
    student_name: str
    email: EmailStr
    course_id: int
    department_id: Optional[str] = None
    
    # Auto-calculated fields - shown in response but not editable
    cpa: float = 0.0
    failed_subjects_number: int = 0
    study_subjects_number: int = 0
    total_failed_credits: int = 0
    total_learned_credits: int = 0
    year_level: str = "Trình độ năm 1"
    warning_level: str = "Cảnh cáo mức 0"
    level_3_warning_number: int = 0

    class Config:
        from_attributes = True


# Student Password Management Schemas
class StudentChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Kiểm tra mật khẩu mạnh"""
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ cái viết hoa')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ cái viết thường')
        
        if not re.search(r'\d', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ số')
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 ký tự đặc biệt')
        
        return v


class StudentRequestPasswordResetRequest(BaseModel):
    email: EmailStr


class StudentVerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Kiểm tra mật khẩu mạnh"""
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ cái viết hoa')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ cái viết thường')
        
        if not re.search(r'\d', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ số')
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 ký tự đặc biệt')
        
        return v


class StudentPasswordResetResponse(BaseModel):
    message: str
    expires_in: int  # seconds
