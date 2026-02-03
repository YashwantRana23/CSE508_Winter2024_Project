from fastapi import APIRouter

from app.schemas.knowledge_graph import (
    KGGenerateRequest,
    KGResponse,
    KGNode,
    KGEdge,
    RerankResponse,
)
from app.services import knowledge_graph_service

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.post("/generate", response_model=KGResponse)
def generate_knowledge_graph(req: KGGenerateRequest):
    """Generate knowledge graph from list of documents (e.g. BM25 top 10). Returns nodes, edges, and top 3."""
    data = knowledge_graph_service.build_knowledge_graph(req.documents)
    return KGResponse(
        nodes=[KGNode(**n) for n in data["nodes"]],
        edges=[KGEdge(**e) for e in data["edges"]],
        top_3=data["top_3"],
    )
