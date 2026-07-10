"""Turn opaque LLM-provider capacity errors into an actionable message.

The free-tier default model (Groq) enforces small per-minute token budgets: a
long question, a large retrieved context, or a chatty history can trip it well
below any limit a paid model would handle without complaint. Left alone, the
raw provider error (``Error code: 413 - {'error': {...}}``) leaks straight to
the user with no indication of what to do about it. This module recognizes
that error shape and swaps in a message that tells the user to add their own
OpenAI/Anthropic key for requests like this.
"""

from fastapi import HTTPException, status

# Statuses the OpenAI-compatible provider SDKs (openai, groq, anthropic) use
# for "request too large" (413) and "rate limited" (429). Both mean the same
# thing for the free tier: this request exceeds what it can serve right now.
_CAPACITY_STATUS_CODES = (413, 429)

FREE_TIER_CAPACITY_MESSAGE = (
    "This request is too large for the free model. Add your own OpenAI or Anthropic "
    "API key (account menu) for requests like this -- it then runs on your own "
    "model, billed to your account."
)

OWN_KEY_CAPACITY_MESSAGE = (
    "Your API key hit its provider's rate or size limit for this request. Wait a "
    "moment and try again, or check your account's usage limits."
)


def describe_capacity_error(exc: Exception, *, used_own_key: bool) -> str | None:
    """Return a friendly message when `exc` is a provider capacity error, else None.

    Duck-typed on `status_code` rather than importing every provider SDK's
    exception classes, so this works regardless of which optional provider
    extras (e.g. `groq`) are installed in the running process.
    """
    if getattr(exc, "status_code", None) not in _CAPACITY_STATUS_CODES:
        return None
    return OWN_KEY_CAPACITY_MESSAGE if used_own_key else FREE_TIER_CAPACITY_MESSAGE


def raise_friendly_llm_error(exc: Exception, *, used_own_key: bool) -> None:
    """Re-raise `exc` as a clear 413 when it is a provider capacity error.

    Does nothing for any other exception, so callers write
    ``raise_friendly_llm_error(exc, used_own_key=...); raise`` to fall back to
    their existing handling (the global 500 handler) unchanged.
    """
    message = describe_capacity_error(exc, used_own_key=used_own_key)
    if message is not None:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=message) from exc
