from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
import os
import uuid
import shutil

from app.db.database import get_db
from app.models.scholarship_application_model import ScholarshipApplication, ApplicationStatus
from app.models.scholarship_attachment_model import ScholarshipApplicationAttachment
from app.models.student_model import Student
from app.models.semester_gpa_model import SemesterGPA
from app.models.student_drl_model import StudentDRL
from app.utils.jwt_utils import get_current_user, get_current_student, get_current_admin
from app.schemas.scholarship_application_schema import (
    ScholarshipApplicationCreate,
    ScholarshipApplicationUpdate,
    ScholarshipApplicationReview,
    ScholarshipApplicationResponse,
    ScholarshipApplicationListResponse,
    AttachmentInfo
)


router = APIRouter(prefix="/api/scholarship-applications", tags=["Scholarship Applications"])


def calculate_auto_fields(db: Session, student_id: str):
    """
    Tính toán tự động các trường auto_ từ CSDL sinh viên
    """
    # Lấy thông tin sinh viên
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        return {
            "auto_cpa": 0,
            "auto_gpa": 0,
            "auto_drl_latest": 0,
            "auto_drl_average": 0,
            "auto_gpa_last_2_sem": 0,
            "auto_drl_last_2_sem": "0",
            "auto_total_credits": 0
        }
    
    # auto_cpa và auto_total_credits từ bảng student
    auto_cpa = student.cpa or 0
    auto_total_credits = student.total_learned_credits or 0
    
    # auto_gpa từ semester_gpa mới nhất
    # SemesterGPA.student_id tham chiếu đến students.id (integer)
    latest_gpa = db.query(SemesterGPA).filter(
        SemesterGPA.student_id == student.id
    ).order_by(desc(SemesterGPA.semester)).first()
    auto_gpa = latest_gpa.gpa if latest_gpa else 0
    
    # auto_drl_latest từ student_drl mới nhất  
    # StudentDRL.student_id tham chiếu đến students.student_id (string)
    latest_drl = db.query(StudentDRL).filter(
        StudentDRL.student_id == student_id
    ).order_by(desc(StudentDRL.semester)).first()
    auto_drl_latest = latest_drl.drl_score if latest_drl else 0
    
    # auto_drl_average - trung bình tất cả điểm rèn luyện
    avg_drl = db.query(func.avg(StudentDRL.drl_score)).filter(
        StudentDRL.student_id == student_id
    ).scalar()
    auto_drl_average = float(avg_drl) if avg_drl else 0
    
    # auto_gpa_last_2_sem - trung bình GPA của 2 kỳ mới nhất
    last_2_gpa = db.query(SemesterGPA).filter(
        SemesterGPA.student_id == student.id
    ).order_by(desc(SemesterGPA.semester)).limit(2).all()
    
    if len(last_2_gpa) >= 2:
        auto_gpa_last_2_sem = (last_2_gpa[0].gpa + last_2_gpa[1].gpa) / 2
    elif len(last_2_gpa) == 1:
        auto_gpa_last_2_sem = last_2_gpa[0].gpa
    else:
        auto_gpa_last_2_sem = 0
    
    # auto_drl_last_2_sem - trung bình DRL của 2 kỳ mới nhất (trả về string)
    last_2_drl = db.query(StudentDRL).filter(
        StudentDRL.student_id == student_id
    ).order_by(desc(StudentDRL.semester)).limit(2).all()
    
    if len(last_2_drl) >= 2:
        auto_drl_last_2_sem = f"{last_2_drl[0].drl_score}, {last_2_drl[1].drl_score}"
    elif len(last_2_drl) == 1:
        auto_drl_last_2_sem = str(last_2_drl[0].drl_score)
    else:
        auto_drl_last_2_sem = "0"
    
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


@router.get("/my-applications", response_model=List[ScholarshipApplicationResponse])
async def get_my_applications(
    db: Session = Depends(get_db)
):
    """
    Sinh viên lấy danh sách đơn đăng ký của mình
    """
    try:
        # TODO: Lấy student_id từ token authentication khi có
        # Tạm thời dùng student thực tế để test
        student_id = "20225818"

        applications = db.query(ScholarshipApplication).filter(
            ScholarshipApplication.student_id == student_id
        ).order_by(desc(ScholarshipApplication.created_at)).all()
        
        return applications
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi lấy danh sách đơn đăng ký: {str(e)}"
        )


@router.get("/auto-data")
async def get_auto_data(
    db: Session = Depends(get_db)
):
    """
    Lấy dữ liệu tự động để hiển thị trong form đăng ký
    """
    try:
        # TODO: Lấy student_id từ token authentication khi có
        # Tạm thời dùng student thực tế để test
        student_id = "20225818"
        
        auto_fields = calculate_auto_fields(db, student_id)
        return auto_fields
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi lấy dữ liệu tự động: {str(e)}"
        )


@router.get("/auto-fields")
async def get_auto_fields(
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin tự động điền cho form đăng ký (student)
    """
    try:
        # TODO: Lấy student_id từ token authentication khi có
        # Tạm thời dùng student thực tế để test
        student_id = "20225818"
        
        auto_fields = calculate_auto_fields(db, student_id)
        
        return auto_fields
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi lấy thông tin tự động: {str(e)}"
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


@router.post("/create-with-files")
async def create_application_with_files(
    scholarship_id: int = Form(...),
    student_id: str = Form(...),  # Thêm student_id vào form
    bank_account_number: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None), 
    phone_number: Optional[str] = Form(None),
    family_status: Optional[str] = Form(None),
    address_country: Optional[str] = Form(None),
    address_city: Optional[str] = Form(None),
    address_ward: Optional[str] = Form(None),
    address_detail: Optional[str] = Form(None),
    family_description: Optional[str] = Form(None),
    achievement_special: Optional[str] = Form(None),
    achievement_activity: Optional[str] = Form(None),
    reason_apply: Optional[str] = Form(None),
    # Auto fields từ frontend
    auto_cpa: Optional[float] = Form(None),
    auto_gpa: Optional[float] = Form(None),
    auto_drl_latest: Optional[int] = Form(None),
    auto_drl_average: Optional[float] = Form(None),
    auto_gpa_last_2_sem: Optional[float] = Form(None),
    auto_drl_last_2_sem: Optional[str] = Form(None),
    auto_total_credits: Optional[int] = Form(None),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    """
    Tạo đơn đăng ký học bổng với files đính kèm
    """
    try:
        # student_id đã được truyền từ form data
        print(f"DEBUG: Received student_id: {student_id}")
        
        # Kiểm tra student có tồn tại không
        from app.models.student_model import Student
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=400,
                detail=f"Không tìm thấy sinh viên với ID: {student_id}"
            )
        
        # Kiểm tra xem sinh viên đã đăng ký học bổng này chưa
        existing = db.query(ScholarshipApplication).filter(
            ScholarshipApplication.scholarship_id == scholarship_id,
            ScholarshipApplication.student_id == student_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đã đăng ký học bổng này rồi"
            )
        
        # Validate files if provided
        if files and len(files) > MAX_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"Tối đa {MAX_FILES} files"
            )
        
        # Sử dụng auto fields từ form (đã được tính từ frontend)
        auto_fields = {
            "auto_cpa": auto_cpa,
            "auto_gpa": auto_gpa,
            "auto_drl_latest": auto_drl_latest,
            "auto_drl_average": auto_drl_average,
            "auto_gpa_last_2_sem": auto_gpa_last_2_sem,
            "auto_drl_last_2_sem": auto_drl_last_2_sem,
            "auto_total_credits": auto_total_credits
        }
        print(f"DEBUG: Auto fields from form: {auto_fields}")
        
        # Parse family_status enum if provided
        family_status_enum = None
        if family_status:
            from app.models.scholarship_application_model import FamilyStatus
            # Map frontend values to enum values
            family_status_mapping = {
                'bình thường': FamilyStatus.BINH_THUONG,
                'khó khăn': FamilyStatus.KHO_KHAN, 
                'cận nghèo': FamilyStatus.CAN_NGHEO,
                'nghèo': FamilyStatus.NGHEO,
                'Bình thường': FamilyStatus.BINH_THUONG,
                'Khó khăn': FamilyStatus.KHO_KHAN,
                'Cận nghèo': FamilyStatus.CAN_NGHEO,
                'Nghèo': FamilyStatus.NGHEO
            }
            
            family_status_enum = family_status_mapping.get(family_status)
            if not family_status_enum:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tình trạng gia đình không hợp lệ: {family_status}. Các giá trị hỗ trợ: {list(family_status_mapping.keys())}"
                )
        
        # Tạo đơn đăng ký
        print(f"DEBUG: Creating application with family_status_enum: {family_status_enum}")
        try:
            new_application = ScholarshipApplication(
                scholarship_id=scholarship_id,
                student_id=student_id,
                bank_account_number=bank_account_number,
                bank_name=bank_name,
                phone_number=phone_number,
                family_status=family_status_enum,
                address_country=address_country,
                address_city=address_city,
                address_ward=address_ward,
                address_detail=address_detail,
                family_description=family_description,
                achievement_special=achievement_special,
                achievement_activity=achievement_activity,
                reason_apply=reason_apply,
                **auto_fields
            )
            
            db.add(new_application)
            db.flush()  # Get the ID
            print(f"DEBUG: Application created successfully with ID: {new_application.id}")
        except Exception as e:
            print(f"ERROR creating application: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Lỗi tạo đơn đăng ký: {str(e)}"
            )
        
        # Handle file uploads if any
        uploaded_files = []
        if files and files[0].filename:  # Check if actually have files
            for idx, file in enumerate(files, 1):
                if file.filename:  # Skip empty file uploads
                    # Validate file
                    extension = validate_file(file)
                    
                    # Check file size
                    content = await file.read()
                    if len(content) > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File {file.filename} quá lớn (tối đa 10MB)"
                        )
                    
                    # Generate unique filename
                    unique_filename = f"{uuid.uuid4()}.{extension}"
                    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
                    
                    # Save file to disk
                    with open(file_path, "wb") as f:
                        f.write(content)
                    
                    # Save to database
                    attachment = ScholarshipApplicationAttachment(
                        scholarship_application_id=new_application.id,
                        filename=file.filename,
                        file_path=file_path,
                        file_type=extension,
                        file_size=len(content),
                        upload_order=idx
                    )
                    db.add(attachment)
                    
                    uploaded_files.append({
                        "filename": file.filename,
                        "file_type": extension,
                        "file_size": len(content),
                        "upload_order": idx
                    })
        
        db.commit()
        
        return {
            "success": True,
            "message": "Tạo đơn đăng ký thành công",
            "application_id": new_application.id,
            "uploaded_files": uploaded_files
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi tạo đơn đăng ký: {str(e)}"
        )


@router.post("/", response_model=ScholarshipApplicationResponse)
async def create_application(
    application_data: ScholarshipApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Sinh viên tạo đơn đăng ký học bổng mới
    """
    try:
        # Lấy student_id từ request body
        student_id = application_data.student_id
        
        # Kiểm tra xem sinh viên đã đăng ký học bổng này chưa
        existing = db.query(ScholarshipApplication).filter(
            ScholarshipApplication.scholarship_id == application_data.scholarship_id,
            ScholarshipApplication.student_id == student_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đã đăng ký học bổng này rồi"
            )
        
        # Tính toán các trường auto_
        auto_fields = calculate_auto_fields(db, student_id)
        
        # Tạo đơn đăng ký mới
        application_dict = application_data.dict()
        application_dict["student_id"] = student_id
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
    # Lấy student_id từ token hoặc session - tạm thời cần truyền vào
    # Hiện tại chỉ cho phép sinh viên cập nhật đơn của chính mình
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id
        # TODO: Thêm filter student_id khi có authentication
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
        
        # Cập nhật lại các trường auto_ với student_id của application
        auto_fields = calculate_auto_fields(db, application.student_id)
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
        application.reviewed_by = "admin"
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
    # Lấy student_id từ token hoặc session - tạm thời cho phép xóa bất kỳ
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id
        # TODO: Thêm filter student_id khi có authentication  
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


# Configuration for file uploads
UPLOAD_DIRECTORY = "uploads/scholarship_attachments"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES = 3

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


def validate_file(file: UploadFile) -> str:
    """Validate file type and return file extension"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ")
    
    extension = file.filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Chỉ hỗ trợ các file: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    return extension


@router.post("/{application_id}/upload-attachments")
async def upload_multiple_attachments(
    application_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files đính kèm cho đơn đăng ký (tối đa 3 files)
    """
    # Lấy student_id từ token hoặc session - tạm thời cho phép upload cho bất kỳ
    application = db.query(ScholarshipApplication).filter(
        ScholarshipApplication.id == application_id
        # TODO: Thêm filter student_id khi có authentication
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn đăng ký"
        )
    
    # Validate number of files
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Tối đa {MAX_FILES} files"
        )
    
    # Remove existing attachments
    db.query(ScholarshipApplicationAttachment).filter(
        ScholarshipApplicationAttachment.scholarship_application_id == application_id
    ).delete()
    
    try:
        uploaded_files = []
        
        for idx, file in enumerate(files, 1):
            # Validate file
            extension = validate_file(file)
            
            # Check file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} quá lớn (tối đa 10MB)"
                )
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}.{extension}"
            file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
            
            # Save file to disk
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Save to database
            attachment = ScholarshipApplicationAttachment(
                scholarship_application_id=application_id,
                filename=file.filename,
                file_path=file_path,
                file_type=extension,
                file_size=len(content),
                upload_order=idx
            )
            db.add(attachment)
            
            uploaded_files.append({
                "filename": file.filename,
                "file_type": extension,
                "file_size": len(content),
                "upload_order": idx
            })
        
        application.updated_at = datetime.now()
        db.commit()
        
        return {
            "success": True,
            "message": f"Upload {len(files)} file(s) thành công",
            "uploaded_files": uploaded_files
        }
        
    except Exception as e:
        db.rollback()
        # Clean up any uploaded files on error
        for file_info in uploaded_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi upload file: {str(e)}"
        )


