from typing import Optional
from pydantic import BaseModel

class DepartmentBase(BaseModel):
    id: str
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    class Config:
        from_attributes = True
