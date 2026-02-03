from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/submit", response_model=FeedbackResponse)
def submit_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
):
    """Store user feedback (optionally linked to user via auth later)."""
    fb = Feedback(
        message=data.message,
        subject=data.subject,
        email=data.email,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackResponse(
        id=fb.id,
        message=fb.message,
        created_at=fb.created_at.isoformat() if fb.created_at else "",
    )
