from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.student_projects_model import StudentProjects
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.schemas.student_projects_schema import StudentProjectsCreate, StudentProjectsUpdate, StudentProjectsResponse
from app.enums import ProjectType, ProjectStatus
from typing import List, Optional

router = APIRouter(prefix="/student-projects", tags=["Student Projects"])


@router.get("/", response_model=List[StudentProjectsResponse])
def get_all_student_projects(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    project_type: Optional[ProjectType] = Query(None, description="Filter by project type"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """Lấy danh sách đồ án/dự án"""
    query = db.query(StudentProjects)
    
    if student_id:
        query = query.filter(StudentProjects.student_id == student_id)
    if subject_id:
        query = query.filter(StudentProjects.subject_id == subject_id)
    if project_type:
        query = query.filter(StudentProjects.type == project_type)
    if status:
        query = query.filter(StudentProjects.status == status)
    
    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=StudentProjectsResponse)
def get_student_project(project_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin đồ án/dự án theo ID"""
    project = db.query(StudentProjects).filter(StudentProjects.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy đồ án/dự án")
    return project


@router.post("/", response_model=StudentProjectsResponse)
def create_student_project(project_data: StudentProjectsCreate, db: Session = Depends(get_db)):
    """Tạo mới đồ án/dự án"""
    # Kiểm tra student_id có tồn tại không
    student = db.query(Student).filter(Student.student_id == project_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    
    # Kiểm tra subject_id có tồn tại không
    subject = db.query(Subject).filter(Subject.subject_id == project_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
    
    new_project = StudentProjects(**project_data.dict())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.put("/{project_id}", response_model=StudentProjectsResponse)
def update_student_project(project_id: int, project_data: StudentProjectsUpdate, db: Session = Depends(get_db)):
    """Cập nhật đồ án/dự án"""
    project = db.query(StudentProjects).filter(StudentProjects.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy đồ án/dự án")
    
    update_data = project_data.dict(exclude_unset=True)
    
    # Kiểm tra subject_id nếu có cập nhật
    if 'subject_id' in update_data:
        subject = db.query(Subject).filter(Subject.subject_id == update_data['subject_id']).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_student_project(project_id: int, db: Session = Depends(get_db)):
    """Xóa đồ án/dự án"""
    project = db.query(StudentProjects).filter(StudentProjects.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy đồ án/dự án")
    
    db.delete(project)
    db.commit()
    return {"message": f"Đã xóa đồ án/dự án ID {project_id}"}


@router.get("/student/{student_id}/summary")
def get_student_projects_summary(student_id: str, db: Session = Depends(get_db)):
    """Lấy tóm tắt đồ án/dự án của sinh viên"""
    # Kiểm tra sinh viên tồn tại
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    
    projects = db.query(StudentProjects).filter(StudentProjects.student_id == student_id).all()
    
    if not projects:
        return {
            "student_id": student_id,
            "total_projects": 0,
            "completed_projects": 0,
            "average_score": 0,
            "projects_by_type": {},
            "projects_by_status": {}
        }
    
    # Thống kê theo loại
    projects_by_type = {}
    for project in projects:
        if project.type.value not in projects_by_type:
            projects_by_type[project.type.value] = 0
        projects_by_type[project.type.value] += 1
    
    # Thống kê theo trạng thái
    projects_by_status = {}
    for project in projects:
        if project.status.value not in projects_by_status:
            projects_by_status[project.status.value] = 0
        projects_by_status[project.status.value] += 1
    
    # Tính điểm trung bình (chỉ tính những project đã có điểm)
    scored_projects = [p for p in projects if p.scores is not None]
    average_score = sum([p.scores for p in scored_projects]) / len(scored_projects) if scored_projects else 0
    
    return {
        "student_id": student_id,
        "total_projects": len(projects),
        "completed_projects": len([p for p in projects if p.status == ProjectStatus.COMPLETED]),
        "average_score": round(average_score, 2),
        "projects_by_type": projects_by_type,
        "projects_by_status": projects_by_status,
        "projects": projects
    }


@router.patch("/{project_id}/grade")
def grade_project(project_id: int, scores: int, db: Session = Depends(get_db)):
    """Chấm điểm cho đồ án/dự án"""
    if scores < 0 or scores > 100:
        raise HTTPException(status_code=400, detail="Điểm phải từ 0-100")
        
    project = db.query(StudentProjects).filter(StudentProjects.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy đồ án/dự án")
    
    project.scores = scores
    project.status = ProjectStatus.GRADED
    
    db.commit()
    db.refresh(project)
    return {"message": f"Đã chấm điểm {scores} cho đồ án/dự án ID {project_id}", "project": project}