# Deploying the API service (CPU-only Docker image)

This document describes the production Docker image for the **API service**
(`api.main:app`). It is meant for **cloud deployment** on free or low-cost tiers
(e.g. Hugging Face Spaces, Render). The image is CPU-only: it installs a CPU build
of `torch` so no CUDA wheels are pulled, keeping it small enough for those tiers.

> **Local development is unchanged.** Day-to-day, only the vector store runs in
> Docker (`docker compose up -d qdrant`); the API and UI run on the host (`make
> api` / `make ui`). The default `torch` build is multi-gigabyte (CUDA), which is
> why the API is not containerized locally. This image exists for the cloud, where
> a self-contained, CPU-only artifact is what the platform expects.

## What the image contains

- Python 3.12 (matches `requires-python`).
- **CPU-only `torch`**, installed from the PyTorch CPU wheel index
  (`https://download.pytorch.org/whl/cpu`) before anything else, so no CUDA
  libraries are pulled.
- The runtime dependencies the API needs: base deps plus the `api` and `agent`
  extras, `langfuse` (optional tracing), and `sentence-transformers` for local
  `bge-m3` query embeddings and the cross-encoder reranker.
- The application source: `api/`, `core/`, `agent/`, `db/`, and `ingestion/`
  (only its schema/embed/index modules are imported by the retrieval path).

Deliberately **excluded**: Streamlit UI, the Ollama client (`local` extra), the
PDF ingestion runtime (PyMuPDF — offline only), and Alembic (the API creates its
tables via SQLAlchemy on startup, so no migration step runs on boot).

## Build

```bash
docker build -t grounded-rag-api .
```

The `torch` download is large (CPU wheels). The build caches it in its own layer,
so repeated builds are fast as long as the dependency layers are unchanged.

## Run

The API needs a reachable Qdrant collection and an LLM provider. Example with
OpenAI and a remote Qdrant:

```bash
docker run --rm -p 8000:8000 \
  -e QDRANT_URL="https://your-qdrant-host:6333" \
  -e OPENAI_API_KEY="sk-..." \
  grounded-rag-api
```

Fully local LLM via Ollama instead of OpenAI (point at an Ollama server reachable
from the container):

```bash
docker run --rm -p 8000:8000 \
  -e QDRANT_URL="https://your-qdrant-host:6333" \
  -e LLM_PROVIDER=ollama \
  -e OLLAMA_BASE_URL="http://your-ollama-host:11434" \
  grounded-rag-api
```

Then check `http://localhost:8000/health` and the docs at
`http://localhost:8000/docs`.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `QDRANT_URL` | yes | Qdrant endpoint holding the indexed course chunks (default `http://localhost:6333`). |
| `QDRANT_COLLECTION` | no | Collection name (default `courses`). |
| `OPENAI_API_KEY` | yes (OpenAI) | Provider key when using the default OpenAI models. |
| `LLM_PROVIDER` | no | Set to `ollama` to route every role to a local Ollama model (no `OPENAI_API_KEY` needed). |
| `OLLAMA_BASE_URL` | no | Ollama server URL when `LLM_PROVIDER=ollama` (default `http://localhost:11434`). |
| `LLM_<ROLE>` | no | Per-role model override (e.g. `LLM_GENERATE=gpt-4o`), provider prefix allowed. |
| `DATABASE_URL` | no | Relational store (default `sqlite:///./app.db`; set a Postgres URL for persistence). |
| `API_KEY` | no | When set, clients must send a matching `X-API-Key` header on the mutating endpoints and `/history`. `/health` stays open. |
| `RERANKER_MODEL` | no | Enables the cross-encoder reranker (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`). |
| `PORT` | no | Port the server binds to (default `8000`). See the Hugging Face note below. |

The full list of optional settings (reranker tuning, hybrid retrieval, LLM cache,
budget cap, LangFuse tracing) lives in `.env.example`.

## Port handling and Hugging Face Spaces

The container reads `$PORT` and falls back to `8000`. Hugging Face Spaces injects
`PORT` (commonly `7860`) and routes traffic to it, so the same image works there
with no change — Spaces sets the variable for you. On other platforms, set `PORT`
to match what the platform expects, or map the default `8000`.

> Persistence note: the default SQLite database lives inside the container and is
> lost on redeploy. For durable student history, point `DATABASE_URL` at a managed
> Postgres instance. Likewise, Qdrant must be a service the container can reach;
> this image does not bundle a vector store.
