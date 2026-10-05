# Legal Lens

A local legal-document retrieval prototype with BM25 search, TF-IDF document similarity, PDF-based AI chat, a FastAPI backend, and a Next.js interface. Open the dashboard directly: no account, registration, or login is required.

## Run locally

Requirements: Python 3.12, Node.js 20.9 or newer, and npm. The checked-in Python lock records the verified Windows/Python 3.12 environment.

From the repository root, in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env  # first setup only; preserve an existing .env
cd ../frontend
npm ci
cd ..
.\start-local.ps1
```

The launcher starts background processes with logs in the project root. It leaves occupied ports alone; if another application owns ports 3000 or 8000, stop that application or use manual startup with different ports and matching API/CORS settings.

- Dashboard: http://localhost:3000/dashboard
- API documentation: http://localhost:8000/docs
- API health: http://localhost:8000/health

For manual startup, use separate terminals:

```powershell
cd backend
.\.venv\Scripts\python.exe run.py
```

```powershell
cd frontend
npm run dev -- --hostname 127.0.0.1
```

Manual backend startup reloads Python changes. The background launcher requires restarting the relevant process after backend configuration/code changes. The frontend development server reloads page changes.

## Configuration

Backend configuration loads `backend/.env` before all settings. Process environment variables take precedence. The optional frontend configuration is `frontend/.env.local`, based on `frontend/.env.example`.

| Setting | Purpose |
| --- | --- |
| `DATA_PATH` | Optional CSV corpus path, relative to the repository root or absolute. Requires a `text` column; `name` is optional. |
| `OPENAI_API_KEY` | Required for AI chat; keep it in backend/.env. Never put it in a frontend/public variable. |
| `EMBEDDING_MODEL` | Hugging Face embedding model; defaults to `sentence-transformers/all-MiniLM-L6-v2` for local CPU use. |
| `OPENAI_MODEL` | Chat model; defaults to `gpt-3.5-turbo`. Must be available to the configured API project. |
| `CHATBOT_IPC_PDF` | Overrides the bundled IPC PDF. |
| `CHATBOT_MURDER_PDF`, `CHATBOT_CHILD_PDF`, `CHATBOT_MATERNITY_PDF` | PDFs for the other domains. Configure them before using those tabs. |
| `DATABASE_URL` | Optional database URL; defaults to `backend/instance/legal_lens.db`. |
| `NEXT_PUBLIC_API_URL` | Frontend API URL; defaults to `http://localhost:8000`. |

Real `.env` files, databases, logs, and local dependency folders are Git-ignored. Example environment files are safe to commit.

## Search and graph

To use the bundled book as a real search corpus, run `backend/.venv/Scripts/python.exe backend/prepare_corpus.py` from the repository root. Set `DATA_PATH=backend/instance/ipc_corpus.csv` in `backend/.env`, then restart the backend. Each result identifies its original PDF page. This local checkout has been configured this way.

Without `DATA_PATH`, search uses three demonstration documents. The dashboard labels this clearly. Try `maternity benefit`, `murder`, or `child labour`. An invalid configured corpus produces a configuration error rather than silently switching to demo data.

`POST /search/bm25` accepts `{"query":"maternity benefit","top_k":10}`. `top_k` must be between 1 and 50. Results include text, name, score, and rank. Empty results have an explicit message in the dashboard.

The **Process → Knowledge Graph** action submits retrieved documents to `/knowledge-graph/generate`. The service uses at most the first 50 words to calculate pairwise TF-IDF cosine similarities. It returns distinct document nodes (even when names repeat), weighted edges, and up to three documents ranked by average similarity, including self-similarity. `/rerank/cosine` exposes the same ranking separately.

This graph shows document similarity; it does not extract legal entities or relations. The second ranking measures similarity within the retrieved set, not relevance to the original query. Search results are not fed into the chatbot.

## AI chatbot

The server extracts text from the selected PDF using PyMuPDF, splits it into chunks of up to 900 characters with 100-character overlap, embeds the chunks with `sentence-transformers/all-MiniLM-L6-v2`, and retrieves them through FAISS. LangChain calls the configured OpenAI model with that context.

Only the IPC PDF is bundled at the default application path. Missing PDFs are reported explicitly; a different domain is never silently substituted. `/chatbot/status` reports configuration availability, which the interface uses to disable unavailable chat tabs' input. A configured status is not an end-to-end provider/model health check.

Conversation history is maintained separately per domain in the current browser page. The backend receives the last 40 messages on each request and caches only retrieval chains without conversation memory. A new browser visitor has no prior visitor's history. Refreshing clears conversation history.

The first chat can take longer while the embedding model downloads and the PDF index is built. Embedding arrays are cached without pickle under `backend/instance/embeddings`; their cache key includes the PDF contents, model, and chunking configuration, so restarts reuse them and changed inputs rebuild them. Internet access is needed for the initial Hugging Face model download and for OpenAI calls. If the AI provider has no credits, rejects the key, or is temporarily unavailable, the assistant returns clearly labeled document excerpts from local retrieval. Those passages are not AI-generated answers. After adding API credits or replacing a rejected key, restart the backend to retry AI generation. Missing PDFs and local model/index failures are reported as errors. Structured source citations and legal-answer accuracy evaluation remain future work.

## Feedback

Feedback requires a non-empty message; subject and email are optional. Valid submissions persist in SQLite. Invalid inputs return validation errors that the UI displays.

## Verification

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
cd ../frontend
npm run lint
npx tsc --noEmit --incremental false
npm run build
```

The regression suite uses an isolated temporary database and mocks AI calls. It covers configuration loading, demo and invalid corpus search, invalid input, duplicate graph names, feedback persistence, missing chatbot configuration, request-scoped chat history, and removal of the public account endpoints. It does not validate legal correctness or replace an end-to-end live AI check.

## Scope and remaining work

This is a local prototype. The demo corpus is small, supplied documents are historical research material, and no current-law completeness or answer-accuracy claim is made. Production authentication/access controls, source citations, labeled retrieval evaluation, per-session history persistence, and corpus provenance need separate work. The original Flask, Streamlit, notebook, and Llama experiments are preserved; the supported local application is `backend/` plus `frontend/`.

## Contributors and project history

Developed as **CSE508 Winter 2024, Group 44**, with contributions from:

- Harsh Patel — MT23056
- Sahil More — MT23079
- Sarthak Pol — MT23082
- Vinayak Katoch — MT23105
- Yashwant Rana — MT23107

The original notebooks, Flask/Streamlit components and Llama experiments remain in the repository. The `backend/` and `frontend/` directories contain the later FastAPI/Next.js application; [the refactor commit](https://github.com/YashwantRana23/CSE508_Winter2024_Project/commit/d681f4b01e1ca9872389c9a47ae59097a888d7a0) is attributed to `yashwant938`. This is collaborative work, not a sole-authorship claim.

Original project references: [legal-document structuring corpus](https://arxiv.org/abs/2201.13125), [legal judgment prediction](https://arxiv.org/abs/2112.06370), [Indian court judgment NER](https://arxiv.org/abs/2211.03442), and [LegalEval](https://arxiv.org/abs/2304.09548).

