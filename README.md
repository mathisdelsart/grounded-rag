# grounded-rag

A grounded RAG-LLM that answers **strictly from your own documents** — with systematic
citations and a faithfulness guard, and that **refuses** anything its sources don't cover.

**Use case in this repository:** a study assistant over university courses (slides, exercises, summaries).

## Why

General assistants lose your documents between conversations, drift to out-of-source content,
and cannot cite verifiable references. `grounded-rag` keeps a persistent indexed knowledge base,
cites every answer (chapter and page), and runs a faithfulness check to avoid hallucinations.
If the sources don't cover a question, it says so.

## Features

1. **Ask** — retrieve the relevant passage, explain, and cite the source.
2. **Generate** — create an exercise calibrated to the source material's notation.
3. **Grade** — score an answer with feedback (LLM-as-a-judge).
4. **Re-explain** — rephrase while keeping conversation memory.

## Stack

Python, LangChain, LangGraph, FastAPI, Qdrant, LangFuse, Docker, GitHub Actions.

- Embeddings: local multilingual (`BAAI/bge-m3`)
- PDF extraction: PyMuPDF and Marker (math-aware)
- Model-agnostic LLM factory: swap models via environment variables, no code change

## Quickstart

```bash
uv sync                       # install dependencies
docker compose up -d qdrant   # start the vector database
cp .env.example .env          # then fill in your API key
```

## Roadmap

- [ ] **Phase 1** — Walking-skeleton RAG: PDF to Qdrant to sourced CLI answers
- [ ] **Phase 2** — Agentic: LangGraph router with generate and grade nodes
- [ ] **Phase 3** — Quality: faithfulness judge, LangFuse, reference eval set in CI
- [ ] **Phase 4** — Production: FastAPI, Docker, CI
