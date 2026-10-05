from pydantic import BaseModel, ConfigDict, Field


class BM25Request(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=50)


class BM25ResultItem(BaseModel):
    text: str
    name: str
    score: float
    rank: int


class BM25Response(BaseModel):
    query: str
    results: list[BM25ResultItem]
