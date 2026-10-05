from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import search, knowledge_graph, rerank, chatbot, feedback, sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=get_settings().APP_NAME,
    description="Legal Lens: BM25 search, knowledge graph, rerank, domain-specific chatbot, feedback",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(knowledge_graph.router)
app.include_router(rerank.router)
app.include_router(chatbot.router)
app.include_router(feedback.router)
app.include_router(sources.router)


@app.get("/health")
def health():
    settings = get_settings()
    from app.services import source_service
    return {
        "status": "ok",
        "corpus_mode": "configured" if settings.DATA_PATH else "demo",
        "research_sources_available": sum(document.path.is_file() for document in source_service.registry()),
        "provider_configured": bool(settings.OPENAI_API_KEY),
        "provider_health": "not_checked",
        "retrieval_readiness": "lazy; BM25 builds on first request, hybrid requires a cached local model",
    }
