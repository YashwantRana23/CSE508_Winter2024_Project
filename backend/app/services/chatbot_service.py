"""
Domain-specific chatbot: FAISS + LangChain ConversationalRetrievalChain per domain.
Domains: murder, child, maternity, ipc (Indian Penal Code), general.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.config import get_settings, PROJECT_ROOT

settings = get_settings()

# Cache: domain -> conversation chain (or None if not available)
_chains: Dict[str, Any] = {}


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
        p = Path(path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        if p.exists():
            return p

    # Default relative paths under project (LegalLaw/Chatbot)
    defaults = {
        "murder": "LegalLaw/Chatbot/MurderLaw.pdf",
        "child": "LegalLaw/Chatbot/childLaw.pdf",
        "maternity": "LegalLaw/Chatbot/MaternatiyLaw.pdf",
        "ipc": "LegalLaw/Chatbot/Indian Penal Code Book.pdf",
        "general": "LegalLaw/Chatbot/Indian Penal Code Book.pdf",
    }
    candidate = PROJECT_ROOT / defaults.get(domain_lower, defaults["general"])
    if candidate.exists():
        return candidate
    # Fallback: use Indian Penal Code for any domain when specific PDF is missing
    fallback = PROJECT_ROOT / "LegalLaw/Chatbot/Indian Penal Code Book.pdf"
    if fallback.exists():
        return fallback
    return None


def _get_pdf_text(pdf_path: Path) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(str(pdf_path))
    return " ".join(page.extract_text() or "" for page in reader.pages)


def _get_chain_for_domain(domain: str):
    """Build or return cached LangChain conversation chain for domain."""
    if domain in _chains:
        return _chains[domain]

    pdf_path = _resolve_pdf_path(domain)
    if not pdf_path:
        _chains[domain] = None
        return None

    try:
        from langchain.text_splitter import CharacterTextSplitter
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain.chains import ConversationalRetrievalChain
        from langchain.memory import ConversationBufferMemory
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        _chains[domain] = None
        return None

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        _chains[domain] = "no_api_key"
        return "no_api_key"

    text = _get_pdf_text(pdf_path)
    splitter = CharacterTextSplitter(
        separator="\n", chunk_size=900, chunk_overlap=100, length_function=len
    )
    chunks = splitter.split_text(text)
    embeddings = HuggingFaceEmbeddings()
    vector_store = FAISS.from_texts(chunks, embeddings)
    llm = ChatOpenAI(openai_api_key=api_key, model_name="gpt-3.5-turbo", temperature=0)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm, retriever=vector_store.as_retriever(), memory=memory
    )
    _chains[domain] = chain
    return chain


def chat(domain: str, message: str, history: Optional[List[dict]] = None) -> str:
    """
    Get chatbot response for the given domain and message.
    history: optional list of {"role": "user"|"assistant", "content": "..."} for context.
    """
    chain = _get_chain_for_domain(domain)
    if chain is None:
        return (
            "No document is configured for this legal domain. "
            "Please set the corresponding PDF path in environment variables."
        )
    if chain == "no_api_key":
        return (
            "Chatbot requires OPENAI_API_KEY to be set in the server environment. "
            "Please configure it to use the domain-specific legal assistant."
        )

    try:
        response = chain({"question": message})
        answer = response.get("answer", "")
        if not answer and "chat_history" in response:
            msgs = response["chat_history"]
            if msgs:
                answer = msgs[-1].content if hasattr(msgs[-1], "content") else str(msgs[-1])
        return answer or "I couldn't generate a response. Please try rephrasing."
    except Exception as e:
        return f"An error occurred while generating the response: {str(e)}"
