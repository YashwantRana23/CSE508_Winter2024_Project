# Local container deployment

## Verification status

Compose configuration has been validated with `docker compose config --quiet`. A full Linux image build and container startup have **not** been verified in this development session because the Docker Linux daemon was unavailable. Do not describe this release as container-tested until a build and the manual demo complete. The Windows launcher remains the working local startup path.

## Start with Docker Desktop

Enable Docker Desktop's Linux engine. From the repository root, with ports 3000 and 8000 free:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Open `http://localhost:3000/dashboard`. Backend API docs are at `http://localhost:8000/docs`. Both published ports bind to loopback. Initial image installation can be large because the backend includes PyTorch and the existing ML dependency lock.

The default container configuration is keyless. It supports lexical search and document excerpts immediately after the PDF index is ready. Without a downloaded embedding model, a hybrid request falls back to BM25 and displays the actual retrieval method.

### Optional local embedding model

Download the model once into the persistent cache:

```powershell
docker compose exec backend python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
docker compose restart backend
```

Use the same model name as `EMBEDDING_MODEL` if customized. This step needs network access; ordinary requests do not trigger a hidden download. Restart is convenient after setup; otherwise a prior model failure can be retried after one minute. The first hybrid request may need time to generate the document embeddings.

### Optional OpenAI generation

If `backend/.env` already contains your server-only provider configuration:

```powershell
docker compose --env-file backend/.env up -d --force-recreate backend
```

Only variables explicitly mapped in `compose.yaml` are passed to the container. The environment file is not copied into either image. You can instead provide `OPENAI_API_KEY` and `OPENAI_MODEL` through the shell's environment or your deployment secret system. Changing a provider credential requires recreating the backend. Use `docker compose config --quiet` for validation so resolved secret values are not printed.

### Browser address and custom domains

`NEXT_PUBLIC_API_URL` is a **build argument**, because the browser calls the API directly. The default is `http://localhost:8000`; `http://backend:8000` is only a container-network name and cannot be used by the user's browser. Rebuild the frontend after changing the address:

```powershell
$env:NEXT_PUBLIC_API_URL = 'http://localhost:8000'
docker compose build frontend
docker compose up -d frontend
```

The current CORS allowlist contains `http://localhost:3000` and `http://127.0.0.1:3000`. A remote host needs its actual origins added in the backend plus HTTPS and public-demo access/budget controls. This Compose file is not a complete internet-facing production deployment.

## Files and persistence

| Item | Location and behavior |
| --- | --- |
| Feedback database | Named `backend-data` volume at `/app/backend/instance`. |
| Document embeddings | Same persistent instance volume. Content/model changes invalidate cached arrays. |
| Hugging Face model | `HF_HOME=/app/backend/instance/huggingface` in the same volume. |
| Research PDFs | Repository `LegalLaw/Chatbot` mounted read-only at `/app/LegalLaw/Chatbot`. |
| Bundled fallback path | The backend image also contains the IPC PDF at its default application path. A bind mount overlays it in Compose. |
| Application source | Copied at image build time; rebuild after code changes. |
| Local `.env`, database, caches, logs | Excluded from the Docker build context. |

A custom corpus path must be available **inside the container** and explicitly mapped to a supported `CHATBOT_*_PDF` environment variable. Host paths such as `E:\...` are not container paths. Restart the backend after changing source files. Keep source permissions readable by the non-root application user.

Inspect or stop the demo:

```powershell
docker compose logs --tail 100 backend frontend
docker compose down
```

`down` preserves the named volume. Avoid deleting the volume if its feedback and cached model are needed. Review logs before sharing them; do not publish local environment files.

## Image choices and remaining verification

The backend uses Python 3.12 on Debian Bookworm; the frontend uses Node 22 on Debian Bookworm. Both run as non-root users. The frontend installs using `npm ci`, builds once, and starts with `next start`. The backend installs the pinned CPU build of PyTorch before the complete lock to avoid the CUDA runtime payload. All pinned package names are portable; the lock has no `pywin32`-style Windows-only dependency. The [official PyTorch CPU index](https://download.pytorch.org/whl/cpu/torch/) lists the pinned 2.14.1 CPU wheel for CPython 3.12/Linux x86-64. The complete lock still needs a successful Linux build to establish all dependency wheels and runtime compatibility. Linux x86-64 is the intended first target; ARM image compatibility is unverified.

CI has build/lint/type, dependency, Python syntax/import, and Compose configuration checks. It does not build the container images or run regression tests. A future packaging validation should record image build output, `/health`, a source search, a PDF citation, and an excerpt response before claiming container support is verified.
