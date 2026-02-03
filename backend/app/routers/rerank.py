from fastapi import APIRouter

from app.schemas.knowledge_graph import KGGenerateRequest, RerankResponse
from app.services import knowledge_graph_service

router = APIRouter(prefix="/rerank", tags=["rerank"])


@router.post("/cosine", response_model=RerankResponse)
def rerank_cosine(req: KGGenerateRequest):
    """Rerank documents by cosine similarity; returns top 3."""
    top_3 = knowledge_graph_service.rerank_top_3(req.documents)
    return RerankResponse(top_3=top_3)
