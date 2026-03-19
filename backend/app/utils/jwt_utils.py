from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.student_model import Student
from app.models.admin_model import Admin

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(30 * 24 * 60)))

security = HTTPBearer(auto_error=False)


def _extract_token(
    credentials: Optional[HTTPAuthorizationCredentials],
    request: Request,
) -> Optional[str]:
    """Extract token from common header formats used by different clients."""
    if credentials is not None and credentials.credentials:
        return credentials.credentials

    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header:
        parts = auth_header.strip().split()
        if len(parts) == 1:
            # Some clients send raw token without "Bearer" prefix.
            return parts[0]
        if len(parts) == 2 and parts[0].lower() in {"bearer", "jwt", "token"}:
            return parts[1]

    fallback_token = request.headers.get("x-access-token") or request.headers.get("X-Access-Token")
    if fallback_token:
        return fallback_token.strip()

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        parts = cookie_token.strip().split()
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2 and parts[0].lower() in {"bearer", "jwt", "token"}:
            return parts[1]

    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Union[Student, Admin]:
    """Get current user from JWT token"""
    token = _extract_token(credentials, request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = verify_token(token)
    
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")
    
    if not user_type or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    if user_type == "student":
        user = db.query(Student).filter(Student.id == user_id).first()
    elif user_type == "admin":
        user = db.query(Admin).filter(Admin.id == user_id).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user type"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def get_current_student(current_user: Union[Student, Admin] = Depends(get_current_user)) -> Student:
    """Compatibility wrapper: any authenticated user is accepted."""
    return current_user


def get_current_admin(current_user: Union[Student, Admin] = Depends(get_current_user)) -> Admin:
    """Compatibility wrapper: any authenticated user is accepted."""
    return current_user