from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Domain = Literal["murder", "child", "maternity", "ipc", "general"]
RetrievalMethod = Literal["hybrid", "bm25"]
CorpusStatus = Literal["historical", "unverified"]


class Source(BaseModel):
    id: str
    document_id: str
    title: str
    page: int = Field(ge=1)
    excerpt: str
    url: str
    corpus_status: CorpusStatus
    score: float
    rank: int


class RetrievalInfo(BaseModel):
    method: RetrievalMethod
    elapsed_ms: float
    warning: str | None = None


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=4000)
    domain: Domain = "ipc"
    top_k: int = Field(default=6, ge=1, le=20)
    method: RetrievalMethod = "hybrid"


class RetrievalResponse(BaseModel):
    query: str
    results: list[Source]
    retrieval: RetrievalInfo
    corpus_status: CorpusStatus
