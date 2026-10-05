"""Administrator-configured, allowlisted source PDFs. Never accepts user file paths."""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path

from app.config import get_settings, PROJECT_ROOT

NOTICE = "Sources are research material. Historical IPC content is not a statement of current law; verify applicable law, amendments, and dates. PDF page numbers are physical file pages."


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    title: str
    domains: tuple[str, ...]
    path: Path
    corpus_status: str


def registry() -> list[SourceDocument]:
    settings = get_settings()
    specs = [
        ("ipc-book", "Indian Penal Code Book", ("ipc", "general"), settings.CHATBOT_IPC_PDF, "Indian Penal Code Book.pdf"),
        ("murder-law", "Murder Law", ("murder",), settings.CHATBOT_MURDER_PDF, "MurderLaw.pdf"),
        ("child-law", "Child Law", ("child",), settings.CHATBOT_CHILD_PDF, "childLaw.pdf"),
        ("maternity-law", "Maternity Law", ("maternity",), settings.CHATBOT_MATERNITY_PDF, "MaternatiyLaw.pdf"),
    ]
    result = []
    for document_id, title, domains, configured, filename in specs:
        default_path = PROJECT_ROOT / "LegalLaw" / "Chatbot" / filename
        path = Path(configured) if configured else default_path
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path = path.resolve()
        historical = document_id == "ipc-book" and path == default_path.resolve()
        result.append(SourceDocument(document_id, title, domains, path, "historical" if historical else "unverified"))
    return result


def for_domain(domain: str) -> SourceDocument:
    for document in registry():
        if domain in document.domains:
            return document
    raise ValueError("Unknown research domain.")


def by_id(document_id: str) -> SourceDocument:
    for document in registry():
        if document.document_id == document_id:
            return document
    raise ValueError("Unknown source document.")


@lru_cache(maxsize=16)
def _metadata(path: str, modified_ns: int, size: int) -> tuple[int, str]:
    import pymupdf
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    with pymupdf.open(path) as pdf:
        page_count = len(pdf)
    return page_count, digest.hexdigest()


def metadata(document: SourceDocument) -> tuple[int, str]:
    stat = document.path.stat()
    return _metadata(str(document.path), stat.st_mtime_ns, stat.st_size)


def manifest() -> dict:
    documents = []
    for document in registry():
        available = document.path.is_file()
        page_count = None
        sha256 = None
        reason = "" if available else "No PDF is configured for this domain."
        if available:
            try:
                page_count, sha256 = metadata(document)
            except Exception:
                available = False
                reason = "The configured PDF could not be read."
        documents.append({
            "document_id": document.document_id,
            "title": document.title,
            "domains": list(document.domains),
            "available": available,
            "corpus_status": document.corpus_status,
            "page_count": page_count,
            "sha256": sha256,
            "url": f"/sources/{document.document_id}/pdf?version={sha256}" if available else None,
            "reason": reason,
        })
    return {"documents": documents, "notice": NOTICE}
