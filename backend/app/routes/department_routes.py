from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.department_model import Department
from app.schemas.department_schema import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse
)

router = APIRouter(prefix="/departments", tags=["Departments"])

# CREATE Department
@router.post("/", response_model=DepartmentResponse)
def create_department(dept: DepartmentCreate, db: Session = Depends(get_db)):
    # Check trùng ID
    existing = db.query(Department).filter(Department.id == dept.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department ID already exists")

    new_department = Department(
        id=dept.id,
        name=dept.name
    )
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    return new_department

# GET all Departments
@router.get("/", response_model=list[DepartmentResponse])
def get_all_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return departments

# UPDATE Department
@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: str, dept_update: DepartmentUpdate, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    if dept_update.name is not None:
        department.name = dept_update.name

    db.commit()
    db.refresh(department)
    return department

# DELETE Department
@router.delete("/{department_id}")
def delete_department(department_id: str, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(department)
    db.commit()
    return {"message": "Department deleted successfully"}
