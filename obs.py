"""Optional LangFuse tracing for the LLM factory.

Tracing is fully opt-in: it activates only when LangFuse credentials are present
in the environment. The `langfuse` package is imported lazily inside the helpers,
so importing this module never requires the optional `obs` extra.
"""

import os

# Credentials that signal LangFuse should be enabled. Both keys are required.
_REQUIRED_ENV_VARS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")


def tracing_enabled() -> bool:
    """Return True when LangFuse is configured via environment variables."""
    return all(os.getenv(var) for var in _REQUIRED_ENV_VARS)


def get_callbacks() -> list:
    """Return LangChain callbacks for tracing, or an empty list when disabled.

    The `langfuse` import is deferred so this module stays importable without the
    optional extra. When LangFuse is not configured, no import is attempted.
    """
    if not tracing_enabled():
        return []

    # Lazy import: only reached when tracing is explicitly enabled. The handler
    # moved across LangFuse major versions, so try both known locations.
    try:
        from langfuse.langchain import CallbackHandler  # langfuse >= 3
    except ImportError:  # pragma: no cover - depends on installed version
        from langfuse.callback import CallbackHandler  # langfuse < 3

    # The handler reads LangFuse credentials from the environment.
    return [CallbackHandler()]
