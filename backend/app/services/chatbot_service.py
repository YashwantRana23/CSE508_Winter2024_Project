"""
Domain-specific chatbot: FAISS + LangChain ConversationalRetrievalChain per domain.
Domains: murder, child, maternity, ipc (Indian Penal Code), general.
"""
import hashlib
import os
import tempfile
from threading import RLock
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.config import get_settings, PROJECT_ROOT, BASE_DIR

settings = get_settings()

# Cached retrieval chains contain no conversation memory.
_chains: Dict[str, Any] = {}
_chain_lock = RLock()
_provider_issue = ""


def _resolve_pdf_path(domain: str) -> Optional[Path]:
    """Resolve PDF path for domain from env or default paths."""
    domain_lower = domain.lower()
    path = None
    if domain_lower == "murder":
        path = settings.CHATBOT_MURDER_PDF
    elif domain_lower == "child":
        path = settings.CHATBOT_CHILD_PDF
    elif domain_lower == "maternity":
        path = settings.CHATBOT_MATERNITY_PDF
    elif domain_lower in ("ipc", "general"):
        path = settings.CHATBOT_IPC_PDF

    if path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate if candidate.is_file() else None

    defaults = {
        "murder": "LegalLaw/Chatbot/MurderLaw.pdf",
        "child": "LegalLaw/Chatbot/childLaw.pdf",
        "maternity": "LegalLaw/Chatbot/MaternatiyLaw.pdf",
        "ipc": "LegalLaw/Chatbot/Indian Penal Code Book.pdf",
        "general": "LegalLaw/Chatbot/Indian Penal Code Book.pdf",
    }
    relative = defaults.get(domain_lower)
    if not relative:
        return None
    candidate = PROJECT_ROOT / relative
    return candidate if candidate.is_file() else None


def domain_status(domain: str) -> dict:
    if not _resolve_pdf_path(domain):
        return {"available": False, "reason": "No PDF is configured for this domain."}
    if not settings.OPENAI_API_KEY:
        return {"available": False, "reason": "AI chat is unavailable until OPENAI_API_KEY is configured on the server."}
    return {"available": True, "reason": ""}


def _get_pdf_text(pdf_path: Path) -> str:
    import pymupdf
    with pymupdf.open(pdf_path) as document:
        return "\n\n".join(page.get_text() for page in document)


def _get_chain_for_domain(domain: str):
    with _chain_lock:
        return _build_chain_for_domain(domain)


def _build_chain_for_domain(domain: str):
    """Cache document retrieval resources, never conversation memory."""
    status = domain_status(domain)
    if not status["available"]:
        raise RuntimeError(status["reason"])
    if domain in _chains:
        return _chains[domain]

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.chains import ConversationalRetrievalChain
    from langchain_openai import ChatOpenAI

    import numpy as np
    pdf_path = _resolve_pdf_path(domain)
    # Cache safe arrays only (no pickle). PDF/model/chunking changes invalidate it.
    fingerprint = hashlib.sha256(pdf_path.read_bytes())
    fingerprint.update((settings.EMBEDDING_MODEL + ":pymupdf-recursive-900-100:v2").encode())
    cache_dir = BASE_DIR / "instance" / "embeddings"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / (fingerprint.hexdigest() + ".npz")
    import torch
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL, show_progress=True)
    chunks = vectors = None
    if cache_file.is_file():
        try:
            with np.load(cache_file, allow_pickle=False) as cached:
                chunks = cached["texts"].tolist()
                vectors = cached["vectors"]
                if vectors.ndim != 2 or len(chunks) != len(vectors):
                    chunks = vectors = None
        except (OSError, ValueError, KeyError):
            chunks = vectors = None
    if chunks is None:
        text = _get_pdf_text(pdf_path)
        if not text.strip():
            raise RuntimeError("The configured PDF contains no extractable text.")
        splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = splitter.split_text(text)
        vectors = np.asarray(embeddings.embed_documents(chunks), dtype=np.float32)
        with tempfile.NamedTemporaryFile(dir=cache_dir, suffix=".npz", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            np.savez_compressed(temporary, texts=np.asarray(chunks), vectors=vectors)
        try:
            os.replace(temporary_path, cache_file)
        finally:
            temporary_path.unlink(missing_ok=True)
    vector_store = FAISS.from_embeddings(zip(chunks, vectors.tolist()), embeddings)
    llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL, temperature=0)
    chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=vector_store.as_retriever())
    _chains[domain] = chain
    return chain


def _document_excerpts(chain, domain: str, message: str, history: Optional[List[dict]]) -> str:
    previous_questions = [item["content"] for item in (history or []) if item["role"] == "user"][-2:]
    query = " ".join(previous_questions + [message])
    documents = chain.retriever.invoke(query)
    source = _resolve_pdf_path(domain).name
    passages = []
    for i, document in enumerate(documents[:3], start=1):
        passages.append(f"Passage {i}:\n{document.page_content.strip()}")
    if not passages:
        return "Document-excerpt mode: No relevant passages were found. Try more specific keywords."
    return (
        "Document-excerpt mode — " + _provider_issue + "\n"
        "These are retrieved passages from the PDF, not an AI-generated answer.\n"
        f"Source: {source}\n\n" + "\n\n".join(passages)
    )


def chat(domain: str, message: str, history: Optional[List[dict]] = None) -> str:
    global _provider_issue
    from langchain_core.messages import HumanMessage, AIMessage
    from openai import APIError, AuthenticationError, RateLimitError

    chain = _get_chain_for_domain(domain)
    if _provider_issue:
        return _document_excerpts(chain, domain, message, history)
    messages = [
        (HumanMessage if item["role"] == "user" else AIMessage)(content=item["content"])
        for item in (history or [])
    ]
    try:
        response = chain.invoke({"question": message, "chat_history": messages})
        return response.get("answer") or "I couldn't generate a response. Please try rephrasing."
    except RateLimitError as error:
        if error.code in ("insufficient_quota", "credit_balance_exhausted"):
            _provider_issue = "OpenAI API credits are exhausted."
        else:
            # Transient rate limits use a fallback for this request only.
            _provider_issue = "The AI provider is temporarily rate-limited."
            try:
                return _document_excerpts(chain, domain, message, history)
            finally:
                _provider_issue = ""
    except AuthenticationError:
        _provider_issue = "The AI provider rejected the configured key."
    except APIError:
        _provider_issue = "The AI provider is temporarily unavailable."
        try:
            return _document_excerpts(chain, domain, message, history)
        finally:
            _provider_issue = ""
    return _document_excerpts(chain, domain, message, history)
