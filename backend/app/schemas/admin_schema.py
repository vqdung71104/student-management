from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional


class AdminBase(BaseModel):
    username: str
    email: EmailStr
    
    
class AdminCreate(AdminBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        """Kiểm tra độ dài mật khẩu tối thiểu"""
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        
        return v


class AdminUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class AdminResponse(AdminBase):
    id: int
    password_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    is_active: str
    
    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Kiểm tra độ dài mật khẩu tối thiểu"""
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        
        return v


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Kiểm tra độ dài mật khẩu tối thiểu"""
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        
        return v


class PasswordResetResponse(BaseModel):
    message: str
    expires_in: int  # seconds