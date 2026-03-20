import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.password_reset_token_model import PasswordResetToken
from app.models.student_model import Student
from app.models.admin_model import Admin


class PasswordResetService:
    def __init__(self, expire_minutes: int = 15, max_per_hour: int = 5):
        self.expire_minutes = expire_minutes
        self.max_per_hour = max_per_hour

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _cleanup_expired(self, db: Session) -> None:
        db.query(PasswordResetToken).filter(PasswordResetToken.expires_at < datetime.utcnow()).delete()
        db.commit()

    def find_user_by_email(self, db: Session, email: str) -> Tuple[Optional[str], Optional[int]]:
        student = db.query(Student).filter(Student.email == email).first()
        if student:
            return "student", student.id

        admin = db.query(Admin).filter(Admin.email == email).first()
        if admin:
            return "admin", admin.id

        return None, None

    def check_rate_limit(self, db: Session, email: str) -> bool:
        since = datetime.utcnow() - timedelta(hours=1)
        count = db.query(PasswordResetToken).filter(
            PasswordResetToken.email == email,
            PasswordResetToken.created_at >= since,
        ).count()
        return count < self.max_per_hour

    def create_reset_token(
        self,
        db: Session,
        user_type: str,
        user_id: int,
        email: str,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        self._cleanup_expired(db)

        # Invalidate previous active tokens for same user.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_type == user_type,
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used.is_(False),
        ).update({"used": True, "used_at": datetime.utcnow()}, synchronize_session=False)
        db.commit()

        raw_token = secrets.token_urlsafe(48)
        token_hash = self._hash_token(raw_token)

        record = PasswordResetToken(
            user_type=user_type,
            user_id=user_id,
            email=email,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(minutes=self.expire_minutes),
            used=False,
            request_ip=request_ip,
            user_agent=user_agent,
        )
        db.add(record)
        db.commit()

        return raw_token

    def verify_reset_token(self, db: Session, raw_token: str) -> Optional[PasswordResetToken]:
        token_hash = self._hash_token(raw_token)
        token_row = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.utcnow(),
        ).first()
        return token_row

    def mark_token_used(self, db: Session, token_row: PasswordResetToken) -> None:
        token_row.used = True
        token_row.used_at = datetime.utcnow()
        db.commit()


password_reset_service = PasswordResetService()
