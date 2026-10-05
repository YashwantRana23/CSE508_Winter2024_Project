FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/backend/instance/huggingface

WORKDIR /app/backend
COPY backend/requirements-lock.txt ./requirements-lock.txt
# Install the locked CPU wheel first; the same version satisfies the full lock.
# This avoids pulling the Linux CUDA runtime into a CPU-only demo image.
RUN TORCH_VERSION="$(sed -n 's/^torch==//p' requirements-lock.txt | tr -d '\r')" \
    && test -n "$TORCH_VERSION" \
    && python -m pip install --no-cache-dir --no-deps --index-url https://download.pytorch.org/whl/cpu "torch==$TORCH_VERSION" \
    && python -m pip install --no-cache-dir -r requirements-lock.txt \
    && python -m pip check

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser \
    && mkdir -p /app/backend/instance /app/LegalLaw/Chatbot \
    && chown -R appuser:appuser /app
COPY --chown=appuser:appuser backend/app ./app
COPY --chown=appuser:appuser ["LegalLaw/Chatbot/Indian Penal Code Book.pdf", "/app/LegalLaw/Chatbot/Indian Penal Code Book.pdf"]

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
