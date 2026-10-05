from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=100000)
    name: str = Field(min_length=1, max_length=500)

class KGGenerateRequest(BaseModel):
    documents: list[Document] = Field(max_length=50)


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
