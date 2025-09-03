from typing import Optional
from pydantic import BaseModel

class DepartmentBase(BaseModel):
    department_id: str
    department_name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    class Config:
        from_attributes = True
