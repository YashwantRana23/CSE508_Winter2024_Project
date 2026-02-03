from pydantic import BaseModel


class BM25Request(BaseModel):
    query: str
    top_k: int = 10


class BM25ResultItem(BaseModel):
    text: str
    name: str
    score: float
    rank: int


class BM25Response(BaseModel):
    query: str
    results: list[BM25ResultItem]
