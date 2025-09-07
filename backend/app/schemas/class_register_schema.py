from typing import Optional
from pydantic import BaseModel, validator

class ClassRegisterBase(BaseModel):
    class_info: str
    register_type: str
    register_status: str

    # --- Validator ---
    @validator("class_info")
    def validate_class_info(cls, v):
        allowed = ["Đang mở", "Hoàn thành đăng ký", "Lớp đầy"]
        if v not in allowed:
            raise ValueError(f"class_info phải thuộc {allowed}")
        return v

    @validator("register_type")
    def validate_register_type(cls, v):
        allowed = ["Đăng ký online", "Đăng ký bổ sung"]
        if v not in allowed:
            raise ValueError(f"register_type phải thuộc {allowed}")
        return v

    @validator("register_status")
    def validate_register_status(cls, v):
        allowed = ["Đăng ký thành công", "Đăng ký thất bại"]
        if v not in allowed:
            raise ValueError(f"register_status phải thuộc {allowed}")
        return v


class ClassRegisterCreate(ClassRegisterBase):
    requirement: Optional[str] = None
    student_id: int
    class_id: int


class ClassRegisterUpdate(BaseModel):
    requirement: Optional[str] = None
    class_info: Optional[str] = None
    register_type: Optional[str] = None
    register_status: Optional[str] = None

    # --- Validator ---
    @validator("class_info")
    def validate_class_info(cls, v):
        if v is None: return v
        allowed = ["Đang mở", "Hoàn thành đăng ký", "Lớp đầy"]
        if v not in allowed:
            raise ValueError(f"class_info phải thuộc {allowed}")
        return v

    @validator("register_type")
    def validate_register_type(cls, v):
        if v is None: return v
        allowed = ["Đăng ký online", "Đăng ký bổ sung"]
        if v not in allowed:
            raise ValueError(f"register_type phải thuộc {allowed}")
        return v

    @validator("register_status")
    def validate_register_status(cls, v):
        if v is None: return v
        allowed = ["Đăng ký thành công", "Đăng ký thất bại"]
        if v not in allowed:
            raise ValueError(f"register_status phải thuộc {allowed}")
        return v


class ClassRegisterResponse(ClassRegisterBase):
    id: int
    student_id: int
    class_id: int
    requirement: Optional[str] = None
    class_info: str
    register_type: str
    register_status: str

    class Config:
        from_attributes = True
