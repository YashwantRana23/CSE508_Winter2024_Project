from pydantic import BaseModel


class KGGenerateRequest(BaseModel):
    """Request body: list of documents (text + name) from BM25 top results."""
    documents: list[dict]  # [{"text": "...", "name": "..."}, ...]


class KGNode(BaseModel):
    id: str
    label: str
    rank: int
    avg_similarity: float


class KGEdge(BaseModel):
    source: str
    target: str
    weight: float


class KGResponse(BaseModel):
    nodes: list[KGNode]
    edges: list[KGEdge]
    top_3: list[dict]  # [{"rank": 1, "text": "...", "name": "..."}, ...]


class RerankResponse(BaseModel):
    """Top 3 reranked results after cosine similarity."""
    top_3: list[dict]
