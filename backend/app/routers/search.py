from fastapi import APIRouter

from app.schemas.search import BM25Request, BM25Response, BM25ResultItem
from app.services import bm25_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/bm25", response_model=BM25Response)
def bm25_search(req: BM25Request):
    """BM25 search: returns top K (default 10) results."""
    top_k = min(req.top_k, 50)
    results = bm25_service.get_bm25_results(req.query, top_k=top_k)
    return BM25Response(
        query=req.query,
        results=[BM25ResultItem(**r) for r in results],
    )
