from typing import Optional
from pydantic import BaseModel
from app.schemas.class_schema import ClassResponse
from app.schemas.student_schemas import StudentResponse
from app.schemas.enums import RegisterStatus, RegisterType

class ClassRegisterBase(BaseModel):
    class_info: str
    require: str
    register_status: RegisterStatus
    register_type: RegisterType

class ClassRegisterCreate(ClassRegisterBase):
    student_id: str
    class_id: str

class ClassRegisterUpdate(BaseModel):
    class_info: Optional[str] = None
    require: Optional[str] = None
    register_status: Optional[RegisterStatus] = None
    register_type: Optional[RegisterType] = None

class ClassRegisterResponse(ClassRegisterBase):
    student: StudentResponse
    class_: ClassResponse

    class Config:
        from_attributes = True
