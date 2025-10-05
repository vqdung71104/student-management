from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class ScholarshipApplicationAttachment(Base):
    __tablename__ = "scholarship_application_attachments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scholarship_application_id = Column(Integer, ForeignKey('scholarship_applications.id'), nullable=False)
    filename = Column(String(255), nullable=False)  # Original filename
    file_path = Column(String(500), nullable=False)  # Path to stored file
    file_type = Column(String(50), nullable=False)  # pdf, jpg, png, jpeg
    file_size = Column(Integer, nullable=False)  # File size in bytes
    upload_order = Column(Integer, nullable=False, default=1)  # Order of files (1, 2, 3)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship
    application = relationship("ScholarshipApplication", back_populates="attachments")