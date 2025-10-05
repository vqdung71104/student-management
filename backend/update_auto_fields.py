#!/usr/bin/env python3
"""
Script để cập nhật lại tất cả auto fields cho các scholarship applications hiện tại
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.database import SessionLocal
from app.models.scholarship_application_model import ScholarshipApplication
from app.routes.scholarship_application_routes import calculate_auto_fields

def update_all_auto_fields():
    """Cập nhật lại tất cả auto fields cho các applications hiện tại"""
    db = SessionLocal()
    
    try:
        # Lấy tất cả applications
        applications = db.query(ScholarshipApplication).all()
        
        print(f"Tìm thấy {len(applications)} applications để cập nhật")
        
        for app in applications:
            print(f"Updating application ID {app.id} for student {app.student_id}...")
            
            # Tính toán lại auto fields
            auto_fields = calculate_auto_fields(db, app.student_id)
            
            # Cập nhật các trường auto
            for field, value in auto_fields.items():
                setattr(app, field, value)
                print(f"  {field}: {value}")
            
            print()
        
        # Commit tất cả changes
        db.commit()
        print("Đã cập nhật thành công tất cả applications!")
        
        # Hiển thị kết quả
        print("\nKết quả sau khi cập nhật:")
        for app in applications:
            print(f"Application ID {app.id}:")
            print(f"  auto_cpa: {app.auto_cpa}")
            print(f"  auto_gpa: {app.auto_gpa}")
            print(f"  auto_drl_latest: {app.auto_drl_latest}")
            print(f"  auto_drl_average: {app.auto_drl_average}")
            print(f"  auto_gpa_last_2_sem: {app.auto_gpa_last_2_sem}")
            print(f"  auto_drl_last_2_sem: {app.auto_drl_last_2_sem}")
            print(f"  auto_total_credits: {app.auto_total_credits}")
            print()
            
    except Exception as e:
        db.rollback()
        print(f"Lỗi: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_all_auto_fields()