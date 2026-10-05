from fastapi import APIRouter
from app.schemas.classification import ClassifyQuestionRequest, QuestionClassification
from app.services.classification_service import classify

router = APIRouter(prefix="/questions", tags=["question classification"])


@router.post("/classify", response_model=QuestionClassification)
def classify_question(request: ClassifyQuestionRequest):
    """Local advisory question labels; no API key or user-text persistence."""
    return classify(request.question)
