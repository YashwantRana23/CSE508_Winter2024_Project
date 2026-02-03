# Legal Lens – Architecture (Refactored)

## Overview

The refactored Legal Lens is a **decoupled full-stack application**: a single FastAPI backend and a single Next.js frontend. All previous functionality (auth, BM25 search, knowledge graph, rerank, domain chatbots, feedback) is preserved and exposed via REST APIs.

## Components

### Backend (FastAPI)

- **Auth**: JWT-based. Register and login return an `access_token`; frontend sends `Authorization: Bearer <token>` on API calls. User and password hashing (bcrypt) match the original Flask behavior.
- **BM25**: Service loads a corpus from CSV (`DATA_PATH`) or uses a small in-memory demo corpus. Preprocessing uses gensim-style tokenization (or a simple regex fallback). `rank_bm25.BM25Okapi` returns top 10 results per query.
- **Knowledge graph**: Accepts the list of documents (e.g. BM25 top 10). Builds TF-IDF vectors, computes pairwise cosine similarity, builds a directed graph (NetworkX), and returns nodes, edges, and **top 3** reranked by average similarity (same logic as the original 3D Knowledge Graph script).
- **Rerank**: Same cosine-similarity logic; returns only the top 3 reranked results.
- **Chatbot**: One endpoint per domain: `POST /chatbot/{domain}` (murder, child, maternity, ipc). Each domain can be backed by a PDF (env-configurable). Uses LangChain + FAISS + OpenAI; if `OPENAI_API_KEY` or the PDF is missing, returns an explanatory message.
- **Feedback**: Stored in SQLite via SQLAlchemy (Feedback model). No auth required to submit.

### Frontend (Next.js)

- **Auth**: Login and register pages; token and user stored in `localStorage`; dashboard redirects to login when not authenticated.
- **Dashboard**: Single page with (1) BM25 search bar and results list, (2) “Process → Knowledge Graph” button that calls the KG API and shows the graph + top 3, (3) domain-specific chatbot (tabs + chat UI), (4) feedback form.
- **Knowledge graph**: vis-network (client-only, dynamic import) for interactive nodes and edges; same data contract as the backend (nodes, edges, top_3).
- **Chatbot**: Domain selector and a chat-style UI; messages sent to `POST /chatbot/{domain}` with optional history.

## Data Flow

1. User registers or logs in → JWT and user info stored in frontend.
2. User enters a query → `POST /search/bm25` → top 10 results shown.
3. User clicks “Process” → frontend sends those 10 documents to `POST /knowledge-graph/generate` → backend returns nodes, edges, and top 3 → frontend shows the graph and the top 3.
4. User selects a chatbot domain and sends a message → `POST /chatbot/{domain}` → backend uses the domain’s chain (or fallback) → response shown in the chat UI.
5. User submits feedback → `POST /feedback/submit` → stored in the backend DB.

## Design Choices

- **No Streamlit**: All UI is in the Next.js app; backend is headless and scalable.
- **Config via env**: Paths and secrets (e.g. `DATA_PATH`, `OPENAI_API_KEY`, `CHATBOT_*_PDF`) are read from the environment so there are no hardcoded paths.
- **Modular services**: BM25, knowledge graph, chatbot, and feedback are separate services and routers, making it easy to test and extend.
- **Single backend process**: One uvicorn process serves all APIs; no need to start multiple Streamlit or Flask apps.

## Running

- **Backend**: From project root, `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python run.py`. Listens on port 8000.
- **Frontend**: From project root, `cd frontend && npm install && npm run dev`. Listens on port 3000 and uses `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) for API calls.
