from typing import Optional
from pydantic import BaseModel
from app.schemas.enums import RegisterStatus, RegisterType

class ClassRegisterBase(BaseModel):
    class_info: str
    register_type: RegisterType
    register_status: RegisterStatus

class ClassRegisterCreate(ClassRegisterBase):
    student_id: int
    class_id: int

class ClassRegisterUpdate(BaseModel):
    class_info: Optional[str] = None
    register_type: Optional[RegisterType] = None
    register_status: Optional[RegisterStatus] = None

class ClassRegisterResponse(ClassRegisterBase):
    id: int
    student_id: int
    class_id: int

    class Config:
        from_attributes = True
