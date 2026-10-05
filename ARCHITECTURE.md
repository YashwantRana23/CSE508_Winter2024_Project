# Legal Lens architecture

The supported local application consists of a Next.js dashboard and a FastAPI backend. Home, login, and register URLs redirect to the dashboard. Account routes are not mounted in the API; legacy authentication code remains for reference.

## Workflows

- **Search:** CSV (`DATA_PATH`) or a labeled three-document demo → tokenization → BM25 positive-scoring hits. Configured invalid corpora return actionable errors.
- **Similarity:** retrieved documents → first 50 words → TF-IDF → cosine similarity → distinct indexed graph nodes and a top-three ranking by average similarity. This is document similarity, not legal entity extraction or query-aware reranking.
- **Chat:** domain-specific PDF → recursive text chunks → Hugging Face embeddings → FAISS → LangChain retrieval chain → configured OpenAI model. Chains have no shared conversation memory. Browser history is separate per domain and sent with each request. Missing domain files do not fall back to another domain. Provider failures use clearly labeled local document excerpts; exhausted-credit and rejected-key states are remembered until backend restart.
- **Feedback:** validated request → SQLAlchemy → SQLite. No account is required.

## Configuration and state

`backend/.env` is loaded before settings are read. OS process environment variables take precedence. The frontend reads `NEXT_PUBLIC_API_URL`, defaulting to localhost:8000. API keys remain server-side. SQLite, `.env`, logs, and dependency/build folders are ignored by Git.

BM25 corpus/index and chatbot retrieval chains are cached in the backend process. PDF embedding arrays also persist in a content-keyed local cache without pickle deserialization. Restart after changing data, PDF paths, or backend configuration. Chat messages live in browser memory only. The frontend dynamically imports vis-network and cancels graph creation after component cleanup.

## API

- `GET /health`: backend health and demo/configured corpus mode.
- `POST /search/bm25`: validated query and top_k (1–50).
- `POST /knowledge-graph/generate`, `POST /rerank/cosine`: up to 50 typed documents.
- `GET /chatbot/status`: per-domain configuration availability.
- `POST /chatbot/{domain}`: message plus optional validated history (up to 40 messages).
- `POST /feedback/submit`: validated feedback persisted in SQLite.

See README.md for setup, launcher, verification, and known limits.
