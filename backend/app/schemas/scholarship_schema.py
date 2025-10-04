from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ScholarshipCreate(BaseModel):
    title: str = Field(..., description="Tiêu đề học bổng")
    type: str = Field(..., description="Loại học bổng")
    slots: int = Field(..., description="Số lượng học bổng")
    value_per_slot: int = Field(..., description="Giá trị mỗi suất")
    sponsor: Optional[str] = Field(None, description="Đối tác cấp học bổng")
    register_start_at: datetime = Field(..., description="Thời gian bắt đầu đăng ký")
    register_end_at: datetime = Field(..., description="Thời gian kết thúc đăng ký")
    target_departments: Optional[str] = Field(None, description="Danh sách đơn vị")
    target_courses: Optional[str] = Field(None, description="Khóa học")
    target_programs: Optional[str] = Field(None, description="Chương trình")
    contact_person: Optional[str] = Field(None, description="Người liên hệ")
    contact_info: Optional[str] = Field(None, description="Thông tin liên hệ")
    document_url: Optional[str] = Field(None, description="URL tài liệu")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")
    note: Optional[str] = Field(None, description="Ghi chú")


class ScholarshipUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    slots: Optional[int] = None
    value_per_slot: Optional[int] = None
    sponsor: Optional[str] = None
    register_start_at: Optional[datetime] = None
    register_end_at: Optional[datetime] = None
    target_departments: Optional[str] = None
    target_courses: Optional[str] = None
    target_programs: Optional[str] = None
    contact_person: Optional[str] = None
    contact_info: Optional[str] = None
    document_url: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None


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