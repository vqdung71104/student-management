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
    existing = db.query(Department).filter(Department.id == dept.department_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department ID already exists")

    new_department = Department(
        id=dept.department_id,
        name=dept.department_name
    )
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    return DepartmentResponse(
        department_id=new_department.id,
        department_name=new_department.name
    )

# GET all Departments
@router.get("/", response_model=list[DepartmentResponse])
def get_all_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return [
        DepartmentResponse(department_id=d.id, department_name=d.name)
        for d in departments
    ]

# UPDATE Department
@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: str, dept_update: DepartmentUpdate, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    if dept_update.department_name is not None:
        department.name = dept_update.department_name

    db.commit()
    db.refresh(department)
    return DepartmentResponse(department_id=department.id, department_name=department.name)

# DELETE Department
@router.delete("/{department_id}")
def delete_department(department_id: str, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(department)
    db.commit()
    return {"message": "Department deleted successfully"}
