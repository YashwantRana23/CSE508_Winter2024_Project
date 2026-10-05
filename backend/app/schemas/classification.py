from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ClassifyQuestionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=4000)


class QuestionClassification(BaseModel):
    status: Literal["ready", "unavailable"]
    model_version: str | None
    scope: Literal["historical", "current", "comparison", "uncertain"]
    intent: Literal["section_lookup", "explanation", "comparison", "unrelated", "uncertain"]
    note: str
