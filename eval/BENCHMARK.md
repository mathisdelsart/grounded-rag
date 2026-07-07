# Provider benchmark (Master Thesis course)

This benchmark runs the full pipeline (retrieve -> answer -> judge) over
`eval/thesis_benchmark.jsonl`, a 27-case set drawn from a DRL / MicroRTS
master thesis indexed in Qdrant. It is meant to be run twice - once per LLM
provider - and then compared side by side, to show the grounded RAG system
behaves consistently across a paid (OpenAI) and a free-tier (Groq) model.

## Dataset

`eval/thesis_benchmark.jsonl` uses the same schema as `eval/dataset.jsonl`
(`question`, `expect_refusal`, `note`, `expect_keywords`) plus an optional
`category` field:

- **factual** (13) - single-fact questions with an expected answer + keywords.
- **math** (3) - formulas / arithmetic grounded in the thesis.
- **synthesis** (6) - short reasoning questions grounded in the thesis.
- **refuse** (5) - out-of-scope questions that must be refused ("not covered").

That is 22 answer-cases and 5 refuse-cases, 27 total.

## Metrics per run

- **refusal accuracy** - refuse-cases refused and answer-cases answered.
- **faithfulness / relevance** - the existing LLM judge (judge #2).
- **citation rate** - answered answer-cases whose text carries a `[n]` marker.
- **retrieval hit rate** - answer-cases whose retrieved chunks contain a keyword.
- **answer-keyword rate** - answered answer-cases whose answer text contains a keyword.
- **retrieval latency p50/p95** - from the `retrieval` timer stage (needs `LATENCY_ENABLED`).

## Running it (real runs make paid API calls)

Prerequisites: Qdrant up with the thesis indexed, DB migrated. Add `--course
"<name>"` to scope retrieval to the thesis if the collection holds several
courses; omit it to search the whole collection.

Run against OpenAI (default provider):

```bash
LATENCY_ENABLED=1 uv run python -m eval.benchmark \
  --out eval/bench-openai.json --latency-out eval/bench-openai-latency.json
```

Run against Groq (free tier):

```bash
LATENCY_ENABLED=1 LLM_PROVIDER=groq GROQ_API_KEY=... uv run python -m eval.benchmark \
  --out eval/bench-groq.json --latency-out eval/bench-groq-latency.json
```

Compare the two runs into a Markdown table:

```bash
uv run python -m eval.compare_report \
  eval/bench-openai.json eval/bench-groq.json \
  --out eval/bench-compare.md
```

The `provider` field stored in each JSON labels the columns automatically;
override with `--label-a` / `--label-b` if needed.
