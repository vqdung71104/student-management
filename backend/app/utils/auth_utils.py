from fastapi import Depends, HTTPException, status, Header
from typing import Optional

def get_current_student_id(x_student_id: Optional[str] = Header(None, alias="X-Student-ID")):
    """
    Lấy student_id từ header request
    Trong production, nên sử dụng JWT token thay vì header đơn giản
    """
    if not x_student_id:
        # Fallback cho testing
        return "SV001"
    return x_student_id

def get_current_admin():
    """Dummy function - authentication disabled"""
    pass

def get_current_user():
    """Dummy function - authentication disabled"""
    pass