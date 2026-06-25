"""Query rewriting for multi-query retrieval expansion.

A single user question often phrases a concept differently from the course
slides, so a lone dense query can miss relevant chunks. Expanding the question
into a few diverse paraphrases / sub-questions and retrieving for each one
widens recall before fusion. This is an opt-in recall booster: it never changes
the refusal guard, which is still applied after fusion in the retrieval layer.

The expansion is best-effort. The LLM call is wrapped so any failure (provider
error, malformed output) degrades gracefully to just the original question
rather than raising, keeping retrieval available even when rewriting fails.
"""

from core.config import get_llm
from core.obs import get_callbacks

_SYSTEM = (
    "You rewrite a student's question into diverse search queries for a course "
    "retrieval system.\n"
    "- Produce up to {n} alternative phrasings or focused sub-questions.\n"
    "- Keep the same language and the course's own terminology.\n"
    "- Cover synonyms and related angles so retrieval recall improves.\n"
    "- Output one query per line, plain text, no numbering, no extra commentary."
)


def _parse_rewrites(raw: str) -> list[str]:
    """Extract clean rewrite lines from the raw LLM output.

    Tolerates common list formatting (leading bullets, ``1.`` numbering) and
    blank lines. Returns the stripped, non-empty lines in order.
    """
    rewrites: list[str] = []
    for line in raw.splitlines():
        cleaned = line.strip().lstrip("-*•").strip()
        # Drop a leading "1." / "2)" style enumerator if the model added one.
        if cleaned[:1].isdigit():
            for sep in (".", ")", ":"):
                head, found, tail = cleaned.partition(sep)
                if found and head.strip().isdigit():
                    cleaned = tail.strip()
                    break
        if cleaned:
            rewrites.append(cleaned)
    return rewrites


def _dedupe(queries: list[str]) -> list[str]:
    """Drop case-insensitive duplicates while preserving first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        key = q.casefold()
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out


def expand_query(question: str, n: int = 3) -> list[str]:
    """Return the original question plus up to ``n`` LLM-generated rewrites.

    Asks the small ``router`` LLM for diverse paraphrases / sub-questions, then
    returns ``[question, *rewrites]`` de-duplicated (case-insensitive,
    order-preserving). The original always comes first so the primary query is
    never lost.

    Robust by construction: any error from the model, or output that yields no
    usable rewrites, falls back to ``[question]``. This function never raises,
    so the retrieval layer can call it unconditionally on the multi-query path.
    """
    if n <= 0:
        return [question]

    try:
        raw = (
            get_llm("router")
            .invoke(
                [
                    ("system", _SYSTEM.format(n=n)),
                    ("human", question),
                ],
                config={"callbacks": get_callbacks()},
            )
            .content
        )
    except Exception:
        # Provider/transport failure: degrade to the original question only.
        return [question]

    if not isinstance(raw, str):
        return [question]

    rewrites = _parse_rewrites(raw)[:n]
    return _dedupe([question, *rewrites])
