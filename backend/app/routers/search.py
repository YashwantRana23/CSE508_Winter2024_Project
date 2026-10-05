from fastapi import APIRouter, HTTPException

from app.schemas.search import BM25Request, BM25Response, BM25ResultItem
from app.services import bm25_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/bm25", response_model=BM25Response)
def bm25_search(req: BM25Request):
    """BM25 search: returns top K (default 10) results."""
    top_k = min(req.top_k, 50)
    try:
        results = bm25_service.get_bm25_results(req.query, top_k=top_k)
    except (ValueError, OSError):
        raise HTTPException(503, "The search corpus could not be loaded. Check DATA_PATH and the CSV text column.")
    return BM25Response(
        query=req.query,
        results=[BM25ResultItem(**r) for r in results],
    )


from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services import retrieval_service


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve(req: RetrievalRequest):
    try:
        return retrieval_service.retrieve(req.query, req.domain, req.top_k, req.method)
    except (ValueError, OSError):
        raise HTTPException(503, "The selected source could not be loaded. Check its PDF configuration and extractable text.")
