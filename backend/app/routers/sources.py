from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.services import source_service

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
def list_sources():
    return source_service.manifest()


@router.get("/{document_id}/pdf")
def source_pdf(document_id: str, version: str | None = Query(default=None, pattern=r"^[0-9a-f]{64}$")):
    try:
        document = source_service.by_id(document_id)
    except ValueError:
        raise HTTPException(404, "Source document not found.")
    if not document.path.is_file():
        raise HTTPException(404, "Source PDF is unavailable.")
    if version is not None:
        try:
            _, current_hash = source_service.metadata(document)
        except Exception:
            raise HTTPException(503, "The source PDF could not be read.")
        if version != current_hash:
            raise HTTPException(409, "This source has changed. Run the search again to cite the current file.")
    return FileResponse(
        document.path, media_type="application/pdf",
        filename=f"{document.document_id}.pdf", content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )
