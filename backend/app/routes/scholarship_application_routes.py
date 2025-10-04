from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.scholarship_application_model import ScholarshipApplication, ApplicationStatus
from app.models.student_model import Student
from app.models.semester_gpa_model import SemesterGPA
from app.models.student_drl_model import StudentDRL
from app.schemas.scholarship_application_schema import (
    ScholarshipApplicationCreate,
    ScholarshipApplicationUpdate,
    ScholarshipApplicationReview,
    ScholarshipApplicationResponse,
    ScholarshipApplicationListResponse
)


router = APIRouter(prefix="/api/scholarship-applications", tags=["Scholarship Applications"])


def calculate_auto_fields(db: Session, student_id: str):
    """
    Tính toán tự động các trường auto_ từ CSDL sinh viên
    """
    # Lấy thông tin sinh viên
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        return {}
    
    # auto_cpa và auto_total_credits từ bảng student
    auto_cpa = student.cpa
    auto_total_credits = student.cpa  # Theo yêu cầu, lấy trường cpa
    
    # auto_gpa từ semester_gpa mới nhất
    latest_gpa = db.query(SemesterGPA).filter(
        SemesterGPA.student_id == student_id
    ).order_by(desc(SemesterGPA.semester)).first()
    auto_gpa = latest_gpa.gpa if latest_gpa else None
    
    # auto_drl_latest từ student_drl mới nhất
    latest_drl = db.query(StudentDRL).filter(
        StudentDRL.student_id == student_id
    ).order_by(desc(StudentDRL.semester)).first()
    auto_drl_latest = latest_drl.total_score if latest_drl else None
    
    # auto_drl_average - trung bình tất cả điểm rèn luyện
    avg_drl = db.query(func.avg(StudentDRL.total_score)).filter(
        StudentDRL.student_id == student_id
    ).scalar()
    auto_drl_average = float(avg_drl) if avg_drl else None
    
    # auto_gpa_last_2_sem - trung bình GPA của 2 kỳ mới nhất
    last_2_gpa = db.query(SemesterGPA).filter(
        SemesterGPA.student_id == student_id
    ).order_by(desc(SemesterGPA.semester)).limit(2).all()
    
    if len(last_2_gpa) >= 2:
        auto_gpa_last_2_sem = (last_2_gpa[0].gpa + last_2_gpa[1].gpa) / 2
    elif len(last_2_gpa) == 1:
        auto_gpa_last_2_sem = last_2_gpa[0].gpa
    else:
        auto_gpa_last_2_sem = None
    
    # auto_drl_last_2_sem - trung bình DRL của 2 kỳ mới nhất
    last_2_drl = db.query(StudentDRL).filter(
        StudentDRL.student_id == student_id
    ).order_by(desc(StudentDRL.semester)).limit(2).all()
    
    if len(last_2_drl) >= 2:
        auto_drl_last_2_sem = f"{last_2_drl[0].total_score}, {last_2_drl[1].total_score}"
    elif len(last_2_drl) == 1:
        auto_drl_last_2_sem = str(last_2_drl[0].total_score)
    else:
        auto_drl_last_2_sem = None
    
    return {
        "auto_cpa": auto_cpa,
        "auto_gpa": auto_gpa,
        "auto_drl_latest": auto_drl_latest,
        "auto_drl_average": auto_drl_average,
        "auto_gpa_last_2_sem": auto_gpa_last_2_sem,
        "auto_drl_last_2_sem": auto_drl_last_2_sem,
        "auto_total_credits": auto_total_credits
    }


@router.get("/", response_model=List[ScholarshipApplicationListResponse])
async def get_applications(
    scholarship_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Admin lấy danh sách đơn đăng ký học bổng
    """
    try:
        query = db.query(ScholarshipApplication)
        
        if scholarship_id:
            query = query.filter(ScholarshipApplication.scholarship_id == scholarship_id)
        
        if status_filter:
            query = query.filter(ScholarshipApplication.status == status_filter)
        
        applications = query.order_by(desc(ScholarshipApplication.created_at)).all()
        return applications
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi server: {str(e)}"
        )


@router.get("/{application_id}", response_model=ScholarshipApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết đơn đăng ký
    """
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn đăng ký"
        )
    
    return application


@router.post("/", response_model=ScholarshipApplicationResponse)
async def create_application(
    application_data: ScholarshipApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Sinh viên tạo đơn đăng ký học bổng mới
    """
    try:
        # Kiểm tra xem sinh viên đã đăng ký học bổng này chưa
        existing = db.query(ScholarshipApplication).filter(
            ScholarshipApplication.scholarship_id == application_data.scholarship_id,
            ScholarshipApplication.student_id == current_student["student_id"]
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đã đăng ký học bổng này rồi"
            )
        
        # Tính toán các trường auto_
        auto_fields = calculate_auto_fields(db, current_student["student_id"])
        
        # Tạo đơn đăng ký mới
        application_dict = application_data.dict()
        application_dict["student_id"] = current_student["student_id"]
        application_dict.update(auto_fields)
        
        application = ScholarshipApplication(**application_dict)
        
        db.add(application)
        db.commit()
        db.refresh(application)
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi tạo đơn đăng ký: {str(e)}"
        )


@router.put("/{application_id}", response_model=ScholarshipApplicationResponse)
async def update_application(
    application_id: int,
    application_data: ScholarshipApplicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Sinh viên cập nhật đơn đăng ký học bổng
    """
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id,
        ScholarshipApplication.student_id == current_student["student_id"]
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn đăng ký"
        )
    
    # Chỉ cho phép cập nhật nếu chưa được duyệt
    if application.status != ApplicationStatus.CHO_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể cập nhật đơn đã được duyệt"
        )
    
    try:
        # Cập nhật thông tin
        for field, value in application_data.dict(exclude_unset=True).items():
            setattr(application, field, value)
        
        # Cập nhật lại các trường auto_
        auto_fields = calculate_auto_fields(db, current_student["student_id"])
        for field, value in auto_fields.items():
            setattr(application, field, value)
        
        application.updated_at = datetime.now()
        db.commit()
        db.refresh(application)
        
        return application
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi cập nhật đơn đăng ký: {str(e)}"
        )


@router.put("/{application_id}/review", response_model=ScholarshipApplicationResponse)
async def review_application(
    application_id: int,
    review_data: ScholarshipApplicationReview,
    db: Session = Depends(get_db)
):
    """
    Admin duyệt đơn đăng ký học bổng
    """
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn đăng ký"
        )
    
    try:
        application.status = review_data.status
        application.note_admin = review_data.note_admin
        application.reviewed_by = current_admin.get("username", "admin")
        application.reviewed_at = datetime.now()
        application.updated_at = datetime.now()
        
        db.commit()
        db.refresh(application)
        
        return application
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi duyệt đơn đăng ký: {str(e)}"
        )


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Sinh viên xóa đơn đăng ký học bổng
    """
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id,
        ScholarshipApplication.student_id == current_student["student_id"]
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn đăng ký"
        )
    
    # Chỉ cho phép xóa nếu chưa được duyệt
    if application.status != ApplicationStatus.CHO_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa đơn đã được duyệt"
        )
    
    try:
        db.delete(application)
        db.commit()
        
        return {"success": True, "message": "Xóa đơn đăng ký thành công"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xóa đơn đăng ký: {str(e)}"
        )


@router.post("/{application_id}/upload-attachment")
async def upload_attachment(
    application_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload file đính kèm cho đơn đăng ký
    """
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id,
        ScholarshipApplication.student_id == current_student["student_id"]
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn đăng ký"
        )
    
    try:
        # Lưu file (implementation tùy vào storage system)
        # Ví dụ đơn giản: lưu tên file vào database
        application.attachment_url = file.filename
        application.updated_at = datetime.now()
        db.commit()
        
        return {
            "success": True,
            "message": "Upload file thành công",
            "attachment_url": application.attachment_url
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi upload file: {str(e)}"
        )