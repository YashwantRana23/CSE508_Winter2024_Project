# Legal Lens 2.0

A source-backed research workspace for a historical Indian legal corpus. Search and the assistant share PDF-page retrieval, every returned passage has a source link, and the demo works without an API key. The dashboard opens directly; no signup is required.

**Corpus scope:** the bundled *Indian Penal Code Book* is historical research material. It is not a complete current-law collection. The app does not include a verified BNS/BNSS/BSA update, legal advice, or a measured answer-accuracy claim.

## What is included

- Shared BM25 and optional MiniLM semantic retrieval, combined using reciprocal rank fusion (RRF).
- PDF page numbers, source excerpts, a registered-source catalogue, and links to the original PDF page.
- A grounded assistant with explicit generated-answer, document-excerpt, and no-evidence states. Local excerpt mode does not need OpenAI credits.
- Local question scope/intent classification using cached MiniLM embeddings and two small logistic-regression heads, with an explicit uncertain result.
- A research workspace with source inspection and a downloadable Markdown research brief.
- Browser conversation history, source availability, feedback persistence, and the existing document-similarity graph.
- A Windows launcher, optional Docker Compose packaging, and build-only GitHub checks.

See [architecture](ARCHITECTURE.md), the [five-minute demo](docs/DEMO.md), [deployment notes](docs/DEPLOYMENT.md), [release scope](docs/RELEASE.md), and the [verification record](docs/VERIFICATION.md).

## Run locally on Windows

Requirements: Python 3.12, Node.js 22, npm. The Python lock originated from a Windows/Python 3.12 environment.

From the repository root, in PowerShell:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
if (!(Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
Push-Location frontend
npm ci
Pop-Location
.\start-local.ps1
```

Open the [dashboard](http://localhost:3000/dashboard), [API docs](http://localhost:8000/docs), or [health endpoint](http://localhost:8000/health). The launcher creates background processes and writes `*.stdout.log` / `*.stderr.log` in the project root. It leaves occupied ports alone. Stop an existing instance before restarting after backend changes.

Manual startup uses two terminals:

```powershell
cd backend
.\.venv\Scripts\python.exe run.py
```

```powershell
cd frontend
npm run dev -- --hostname 127.0.0.1
```

The default PDF is bundled and contains 1,871 physical pages. The older CSV preparation produced 1,844 text-bearing page records; these are pages from one book, not separate judgments. Try **What does Section 302 say about punishment for murder?** and inspect the cited source page. First PDF extraction can take time; later requests reuse in-memory resources.

### Enable semantic retrieval

BM25 retrieval works without downloading an embedding model. To enable hybrid retrieval, download the default model once from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

Then restart the backend, or wait one minute before retrying hybrid search. Request-time model loading only uses the local cache. If the model is absent or unavailable, the response reports a warning and the actual BM25 retrieval method. Embedding arrays persist under `backend/instance`; changed PDF/model inputs invalidate their cache. No pickle index is loaded.

### Local question classification

The assistant classifies question scope (historical, current, cross-era comparison, or uncertain) and intent (section lookup, explanation, comparison, unrelated, or uncertain). It reuses the cached MiniLM model above and bundled logistic-regression coefficients; no API key, runtime training, or request-time download is required. Question understanding is visible with each assistant response and included in exported briefs. It is a routing estimate, not legal advice or a probability of correctness.

If the encoder is missing, the configured model differs from the trained model, or a score fails the acceptance thresholds, classification becomes unavailable/uncertain and the assistant returns excerpts when evidence exists. Source search remains independent. The assistant does not silently change the chosen corpus. Explicit current-law/applicability checks still run when classification is unavailable; current/cross-era questions cannot be answered from historical or unverified sources. Incidental words such as “today” alone no longer trigger the scope guard.

See [classifier design, training and limitations](docs/CLASSIFICATION.md) and the [authored dataset/model card](backend/app/data/classification/README.md). This is a local task-specific classifier; it is not TypeSafe Jev or a reproduction of its architecture.

### Optional generated answers

Set `OPENAI_API_KEY` and an available `OPENAI_MODEL` in **backend/.env**, then restart the backend. A key alone does not guarantee API credits or model access. An absent key uses excerpts; provider failures also fall back to excerpts with a visible reason. Quota/authentication failures pause provider calls for five minutes; transient failures pause them for one minute. Requests retry after that cooldown. Updating an environment variable still requires a backend restart.

Questions requiring current-law, cross-era or dated-applicability verification are declined when the selected source is historical or unverified. Uncertain scope or intent uses excerpts, even in auto mode. Generated answers are a convenience layer over retrieved passages. Check the citations and source text yourself; validating a citation ID does not prove that a claim is legally correct. Only the last 40 submitted history messages are accepted. Conversation history stays in the current browser page and survives changes to the search method. Switching the corpus or refreshing clears it, as the composer states. The backend stores no shared conversation memory.

## Configuration

Process environment variables override `backend/.env`. Frontend variables belong in `frontend/.env.local` or the container build configuration. Secrets, databases, caches, and logs are Git-ignored.

| Setting | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional server-only credential for generated answers. Never use a public frontend variable. |
| `OPENAI_MODEL` | Generation model available to the API project; existing default is `gpt-3.5-turbo`. |
| `EMBEDDING_MODEL` | Cached SentenceTransformers model; default `sentence-transformers/all-MiniLM-L6-v2`. |
| `CHATBOT_IPC_PDF` | Optional replacement for the bundled PDF; replacements are marked unverified. |
| `CHATBOT_MURDER_PDF`, `CHATBOT_CHILD_PDF`, `CHATBOT_MATERNITY_PDF` | Optional PDFs for additional domains. Missing sources stay unavailable. |
| `DATABASE_URL` | Defaults to SQLite at `backend/instance/legal_lens.db`; currently stores feedback. |
| `DATA_PATH` | Optional CSV for the legacy `/search/bm25` endpoint. It does not replace the shared PDF source registry. |
| `NEXT_PUBLIC_API_URL` | Browser-accessible API base URL; defaults to `http://localhost:8000`. Baked into production builds. |
| `HF_HOME` | Optional Hugging Face model-cache location. |

## API at a glance

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Lightweight application health. |
| `GET /sources` | Registered source catalogue, availability, and historical/unverified labels. |
| `GET /sources/{document_id}/pdf` | Serve a registered PDF; source links use `?version=SHA256#page=N`. |
| `POST /search/retrieve` | Shared source retrieval: `query`, `domain`, `top_k` (1–20), `method` (`hybrid` or `bm25`). |
| `POST /questions/classify` | Local question classification: `question` (1–4,000 characters), independent of retrieval and generation. |
| `GET /chatbot/status` | Per-domain assistant availability and provider configuration information. |
| `POST /chatbot/{domain}` | `message`, optional `history`, retrieval `method`, and `answer_mode` (`auto` or `excerpts`). |
| `POST /feedback/submit` | Validated feedback written to SQLite. |

Shared retrieval returns page-aware sources plus the actual method and elapsed time. Version-pinned PDF links return HTTP 409 if the source has changed, so stale citations cannot silently open a different file. Chat returns `mode` (`generated`, `excerpts`, or `no_evidence`), `reason`, `sources`, retrieval metadata, local `classification`, and a request ID alongside the response text. Full schemas are in `/docs`.

The legacy `/search/bm25`, `/knowledge-graph/generate`, and `/rerank/cosine` routes remain for compatibility. The graph uses TF-IDF similarity over the first 50 words and ranks by average within-set similarity. It is a document-similarity visualization, not a legal entity graph or a query-aware reranker. The legacy CSV search uses a labeled three-document demo when `DATA_PATH` is unset; invalid configured files produce an error.

## Build checks

```powershell
.\backend\.venv\Scripts\python.exe -m compileall -q backend/app backend/run.py backend/prepare_corpus.py backend/scripts
.\backend\.venv\Scripts\python.exe -m pip check
Push-Location frontend
npm run lint
npx tsc --noEmit --incremental false
npm run build
Pop-Location
```

GitHub Actions runs dependency, syntax/import, frontend lint/type/build, and Compose configuration checks. It does not run the historical regression suite, use paid model calls, download an embedding model, or establish legal accuracy. Manual demo steps are documented separately; do not claim a check passed until its output is recorded.

## Scope and next steps

This release prioritizes a working local research demo. Current-law ingestion with official provenance, cross-encoder reranking, OCR, multilingual evaluation, persistent private workspaces, public-hosting access controls, and a labeled retrieval benchmark remain future work. A generation-provider outage should not block document retrieval. Network access is needed for installation, the optional model download, and generated answers.

The Docker configuration is a local packaging option; see [deployment status](docs/DEPLOYMENT.md) for its verification limits. The Windows launcher remains the supported local startup path.

## Contributors and project history

Developed as **CSE508 Winter 2024, Group 44**, with contributions from:

- Harsh Patel — MT23056
- Sahil More — MT23079
- Sarthak Pol — MT23082
- Vinayak Katoch — MT23105
- Yashwant Rana — MT23107

The original notebooks, Flask/Streamlit components and Llama experiments remain in the repository. The `backend/` and `frontend/` directories contain the later FastAPI/Next.js application; [the refactor commit](https://github.com/YashwantRana23/CSE508_Winter2024_Project/commit/d681f4b01e1ca9872389c9a47ae59097a888d7a0) is attributed to `yashwant938`. This is collaborative work, not a sole-authorship claim.

Original project references: [legal-document structuring corpus](https://arxiv.org/abs/2201.13125), [legal judgment prediction](https://arxiv.org/abs/2112.06370), [Indian court judgment NER](https://arxiv.org/abs/2211.03442), and [LegalEval](https://arxiv.org/abs/2304.09548).
