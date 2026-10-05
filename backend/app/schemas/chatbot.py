from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.classification import QuestionClassification
from app.schemas.retrieval import Domain, RetrievalInfo, RetrievalMethod, Source


class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    domain: Domain | None = None
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=40)
    method: RetrievalMethod = "hybrid"
    answer_mode: Literal["auto", "excerpts"] = "auto"


class ChatResponse(BaseModel):
    response: str
    domain: str
    mode: Literal["generated", "excerpts", "no_evidence"]
    reason: str | None = None
    sources: list[Source] = Field(default_factory=list)
    retrieval: RetrievalInfo
    request_id: str
    classification: QuestionClassification
