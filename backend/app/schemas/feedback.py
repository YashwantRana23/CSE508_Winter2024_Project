from typing import Optional

from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    subject: Optional[str] = None
    message: str
    email: Optional[str] = None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    created_at: str
