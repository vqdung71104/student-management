from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FamilyStatusEnum(str, Enum):
    BINH_THUONG = "bình thường"
    KHO_KHAN = "khó khăn"
    CAN_NGHEO = "cận nghèo"
    NGHEO = "nghèo"


class ApplicationStatusEnum(str, Enum):
    CHO_DUYET = "Chờ duyệt"
    DA_DUYET = "Đã duyệt"
    BI_TU_CHOI = "Bị từ chối"


class ScholarshipApplicationCreate(BaseModel):
    scholarship_id: int = Field(..., description="ID học bổng")
    student_id: str = Field(..., description="ID sinh viên")
    bank_account_number: Optional[str] = Field(None, description="Số tài khoản ngân hàng")
    bank_name: Optional[str] = Field(None, description="Tên ngân hàng")
    phone_number: Optional[str] = Field(None, description="Số điện thoại")
    family_status: Optional[FamilyStatusEnum] = Field(None, description="Tình trạng gia đình")
    address_country: Optional[str] = Field(None, description="Quốc gia")
    address_city: Optional[str] = Field(None, description="Thành phố")
    address_ward: Optional[str] = Field(None, description="Phường/Xã")
    address_detail: Optional[str] = Field(None, description="Địa chỉ chi tiết")
    family_description: Optional[str] = Field(None, description="Mô tả hoàn cảnh gia đình")
    achievement_special: Optional[str] = Field(None, description="Thành tích đặc biệt")
    achievement_activity: Optional[str] = Field(None, description="Hoạt động nổi bật")
    reason_apply: Optional[str] = Field(None, description="Lý do xin học bổng")
    attachment_url: Optional[str] = Field(None, description="File đính kèm")


class ScholarshipApplicationUpdate(BaseModel):
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    phone_number: Optional[str] = None
    family_status: Optional[FamilyStatusEnum] = None
    address_country: Optional[str] = None
    address_city: Optional[str] = None
    address_ward: Optional[str] = None
    address_detail: Optional[str] = None
    family_description: Optional[str] = None
    achievement_special: Optional[str] = None
    achievement_activity: Optional[str] = None
    reason_apply: Optional[str] = None
    attachment_url: Optional[str] = None


class ScholarshipApplicationReview(BaseModel):
    status: ApplicationStatusEnum = Field(..., description="Trạng thái duyệt")
    note_admin: Optional[str] = Field(None, description="Ghi chú từ admin")


class ScholarshipApplicationResponse(BaseModel):
    id: int
    scholarship_id: int
    student_id: str
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    phone_number: Optional[str] = None
    family_status: Optional[str] = None
    address_country: Optional[str] = None
    address_city: Optional[str] = None
    address_ward: Optional[str] = None
    address_detail: Optional[str] = None
    family_description: Optional[str] = None
    achievement_special: Optional[str] = None
    achievement_activity: Optional[str] = None
    reason_apply: Optional[str] = None
    attachment_url: Optional[str] = None
    
    # Auto fields
    auto_cpa: Optional[float] = None
    auto_gpa: Optional[float] = None
    auto_drl_latest: Optional[int] = None
    auto_drl_average: Optional[float] = None
    auto_gpa_last_2_sem: Optional[float] = None
    auto_drl_last_2_sem: Optional[str] = None
    auto_total_credits: Optional[int] = None
    
    # Review info
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    note_admin: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScholarshipApplicationListResponse(BaseModel):
    id: int
    scholarship_id: int
    student_id: str
    family_status: Optional[str] = None
    auto_cpa: Optional[float] = None
    auto_gpa: Optional[float] = None
    auto_drl_latest: Optional[int] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True