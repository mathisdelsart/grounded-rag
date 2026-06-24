# Serving image for the FastAPI app and the Streamlit UI.
# Builds with uv against the pinned uv.lock and installs the extras needed to
# serve the API and the UI (api + agent + ui + embed). The query-side embedding
# model (bge-m3) is baked into the image so the first request is instant and
# needs no network. The heavy offline-only `ingestion` extra (marker-pdf, etc.)
# stays out.

FROM python:3.12-slim

# Copy the uv binary from the official distroless image (pinned major version).
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    HF_HOME=/app/.hf_cache \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies first for better layer caching. Only the lockfile and
# project metadata are needed to resolve and sync the environment.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --extra api --extra agent --extra ui --extra embed

# Pre-download the multilingual embedding model into the image's HF cache so the
# first query embeds instantly and the container needs no network for retrieval.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# Copy the application source needed at runtime. Root modules are copied with a
# glob so newly added top-level modules are picked up automatically; the named
# package directories cover the rest. This keeps local-only paths (worktrees,
# editor config, course PDFs) out of the image without enumerating them in
# .dockerignore.
COPY README.md ./
COPY *.py ./
COPY api/ ./api/
COPY agent/ ./agent/
COPY ingestion/ ./ingestion/
COPY eval/ ./eval/
COPY db/ ./db/
COPY ui/ ./ui/

# Run as an unprivileged user. The app reads no files it must own at runtime,
# so a plain non-root user (owning /app) is enough.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Probe the API liveness endpoint using the interpreter already in the image,
# so no extra packages (curl/wget) are needed. A non-zero exit marks unhealthy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=4).status == 200 else 1)"]

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
