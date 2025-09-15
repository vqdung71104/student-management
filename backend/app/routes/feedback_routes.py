from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.database import get_db
from app.models.feedback_model import Feedback, FAQ, FeedbackStatus
from app.schemas.feedback_schema import (
    FeedbackCreate, FeedbackResponse, FeedbackUpdate, FeedbackBulkUpdate,
    FAQCreate, FAQResponse, FAQUpdate
)

router = APIRouter()

# Feedback endpoints
@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(feedback_data: FeedbackCreate, db: Session = Depends(get_db)):
    try:
        feedback = Feedback(**feedback_data.dict())
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating feedback: {str(e)}")

@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_all_feedback(
    status: Optional[FeedbackStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Feedback)
    if status:
        query = query.filter(Feedback.status == status)
    
    feedbacks = query.order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
    return feedbacks

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback

@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(feedback_id: int, feedback_update: FeedbackUpdate, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    for field, value in feedback_update.dict(exclude_unset=True).items():
        setattr(feedback, field, value)
    
    try:
        db.commit()
        db.refresh(feedback)
        return feedback
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}")

@router.put("/feedback/bulk-update", response_model=dict)
async def bulk_update_feedback(bulk_update: FeedbackBulkUpdate, db: Session = Depends(get_db)):
    try:
        updated_count = db.query(Feedback).filter(
            Feedback.id.in_(bulk_update.feedback_ids)
        ).update(
            {"status": bulk_update.status},
            synchronize_session=False
        )
        
        db.commit()
        return {"message": f"Updated {updated_count} feedback(s)", "updated_count": updated_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error bulk updating feedback: {str(e)}")

@router.delete("/feedback/{feedback_id}")
async def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    try:
        db.delete(feedback)
        db.commit()
        return {"message": "Feedback deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting feedback: {str(e)}")

# FAQ endpoints
@router.post("/faq", response_model=FAQResponse)
async def create_faq(faq_data: FAQCreate, db: Session = Depends(get_db)):
    try:
        faq = FAQ(**faq_data.dict())
        db.add(faq)
        db.commit()
        db.refresh(faq)
        return faq
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating FAQ: {str(e)}")

@router.get("/faq", response_model=List[FAQResponse])
async def get_all_faq(
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    query = db.query(FAQ)
    if active_only:
        query = query.filter(FAQ.is_active == True)
    
    faqs = query.order_by(FAQ.order_index.asc(), FAQ.created_at.desc()).all()
    return faqs

@router.get("/faq/{faq_id}", response_model=FAQResponse)
async def get_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return faq

@router.put("/faq/{faq_id}", response_model=FAQResponse)
async def update_faq(faq_id: int, faq_update: FAQUpdate, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    for field, value in faq_update.dict(exclude_unset=True).items():
        setattr(faq, field, value)
    
    try:
        db.commit()
        db.refresh(faq)
        return faq
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating FAQ: {str(e)}")

@router.delete("/faq/{faq_id}")
async def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    try:
        db.delete(faq)
        db.commit()
        return {"message": "FAQ deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting FAQ: {str(e)}")