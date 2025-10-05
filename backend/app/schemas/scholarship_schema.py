from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ScholarshipCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề học bổng")
    type: str = Field(..., min_length=1, max_length=100, description="Loại học bổng")
    slots: int = Field(..., gt=0, description="Số lượng học bổng")
    value_per_slot: int = Field(..., gt=0, description="Giá trị mỗi suất")
    sponsor: Optional[str] = Field(None, max_length=255, description="Đối tác cấp học bổng")
    register_start_at: datetime = Field(..., description="Thời gian bắt đầu đăng ký")
    register_end_at: datetime = Field(..., description="Thời gian kết thúc đăng ký")
    target_departments: Optional[str] = Field(None, description="Danh sách đơn vị")
    target_courses: Optional[str] = Field(None, description="Khóa học")
    target_programs: Optional[str] = Field(None, description="Chương trình")
    contact_person: Optional[str] = Field(None, max_length=255, description="Người liên hệ")
    contact_info: Optional[str] = Field(None, max_length=255, description="Thông tin liên hệ")
    document_url: Optional[str] = Field(None, max_length=255, description="URL tài liệu")
    description: Optional[str] = Field(None, description="Mô tả chi tiết (có thể chứa văn bản dài với ký tự đặc biệt)")
    note: Optional[str] = Field(None, description="Ghi chú")

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            # Normalize line endings và xử lý ký tự đặc biệt
            v = v.replace('\r\n', '\n').replace('\r', '\n')
            # Loại bỏ các ký tự điều khiển không cần thiết (trừ \n, \t)
            import re
            v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
            return v.strip()
        return v

    @validator('register_end_at')
    def validate_register_dates(cls, v, values):
        if 'register_start_at' in values and v <= values['register_start_at']:
            raise ValueError('Thời gian kết thúc phải sau thời gian bắt đầu')
        return v

    class Config:
        # Cho phép mã hóa UTF-8
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScholarshipUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    slots: Optional[int] = Field(None, gt=0)
    value_per_slot: Optional[int] = Field(None, gt=0)
    sponsor: Optional[str] = Field(None, max_length=255)
    register_start_at: Optional[datetime] = None
    register_end_at: Optional[datetime] = None
    target_departments: Optional[str] = None
    target_courses: Optional[str] = None
    target_programs: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_info: Optional[str] = Field(None, max_length=255)
    document_url: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None  # Không giới hạn độ dài cho mô tả
    note: Optional[str] = None

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            # Normalize line endings và xử lý ký tự đặc biệt
            v = v.replace('\r\n', '\n').replace('\r', '\n')
            # Loại bỏ các ký tự điều khiển không cần thiết (trừ \n, \t)
            import re
            v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
            return v.strip()
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScholarshipResponse(BaseModel):
    id: int
    title: str
    type: str
    slots: int
    value_per_slot: int
    sponsor: Optional[str] = None
    register_start_at: datetime
    register_end_at: datetime
    target_departments: Optional[str] = None
    target_courses: Optional[str] = None
    target_programs: Optional[str] = None
    contact_person: Optional[str] = None
    contact_info: Optional[str] = None
    document_url: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScholarshipListResponse(BaseModel):
    id: int
    title: str
    type: str
    slots: int
    value_per_slot: int
    sponsor: Optional[str] = None
    register_start_at: datetime
    register_end_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True