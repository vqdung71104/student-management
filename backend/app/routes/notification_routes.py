from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from ..db.database import get_db
from ..models.notification_model import Notification
from ..schemas.notification_schema import NotificationCreate, NotificationUpdate, NotificationResponse

router = APIRouter(tags=["Notifications"])

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    db: Session = Depends(get_db)
):
    """Get all notifications, ordered by updated_at desc"""
    notifications = db.query(Notification).order_by(desc(Notification.updated_at)).offset(skip).limit(limit).all()
    return notifications

@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    """Get a specific notification by ID"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/notifications", response_model=NotificationResponse)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    """Create a new notification"""
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.put("/notifications/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: int, 
    notification_update: NotificationUpdate, 
    db: Session = Depends(get_db)
):
    """Update a notification"""
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    update_data = notification_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_notification, field, value)
    
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """Delete a notification"""
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(db_notification)
    db.commit()
    return {"message": "Notification deleted successfully"}

@router.get("/notifications/count/total")
def get_notifications_count(db: Session = Depends(get_db)):
    """Get total count of notifications"""
    count = db.query(Notification).count()
    return {"count": count}