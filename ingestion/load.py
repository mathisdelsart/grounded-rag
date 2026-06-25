"""Plain-text course material loading (Markdown / text).

PDFs are slide decks where math is rendered as images, so they go through the
math-aware vision pipeline in :mod:`ingestion.extract`. Markdown (`.md`) and
text (`.txt`) files are plain prose: there is nothing to rasterize and no vision
model is needed. They are read straight from disk as UTF-8 and split into
overlapping prose windows, producing the same :class:`Page` contract the rest of
the pipeline (chunk -> embed -> index) consumes.

A prose ``Page`` differs from a slide ``Page`` only in ``doc_type`` ("prose")
and in how ``page``/``chapter`` are filled: there is no real page geometry, so
``page`` is a running 1-based window index and ``chapter`` is the file stem
(a stable, human-readable source label used in citations).
"""

import logging
import os

from ingestion.schema import Page

logger = logging.getLogger(__name__)

# Supported plain-text extensions. PyMuPDF and the vision model are bypassed
# entirely for these; everything else is treated as a PDF.
TEXT_EXTENSIONS = {".md", ".txt"}

# Prose windowing defaults. The course material is mostly French syllabi and
# summaries; bge-m3 embeddings work best on focused passages, so prose is split
# into roughly paragraph-sized windows with overlap to avoid cutting a concept
# exactly at a boundary. Sizes are measured in whitespace-separated words, used
# here as a cheap, dependency-free proxy for tokens (the project targets
# ~500-token windows for prose).
_DEFAULT_WINDOW_WORDS = 350
_DEFAULT_OVERLAP_WORDS = 50


def is_text_file(path: str) -> bool:
    """Return whether `path` is a plain-text (`.md`/`.txt`) input.

    Detection is purely by extension (case-insensitive), so callers can route
    the file before opening it. Anything not matching is treated as a PDF.
    """
    return os.path.splitext(path)[1].lower() in TEXT_EXTENSIONS


def split_prose(
    text: str,
    *,
    window_words: int = _DEFAULT_WINDOW_WORDS,
    overlap_words: int = _DEFAULT_OVERLAP_WORDS,
) -> list[str]:
    """Split prose into overlapping word windows.

    Words are split on whitespace and grouped into windows of `window_words`
    that overlap by `overlap_words`, so a passage straddling a boundary stays
    recoverable from at least one window. Word count is a deliberate, simple
    proxy for token count: it needs no tokenizer and keeps the loader free of
    the heavy embedding dependency. Empty or whitespace-only input yields no
    windows.
    """
    if overlap_words >= window_words:
        raise ValueError("overlap_words must be smaller than window_words")
    words = text.split()
    if not words:
        return []
    step = window_words - overlap_words
    windows: list[str] = []
    for start in range(0, len(words), step):
        window = words[start : start + window_words]
        windows.append(" ".join(window))
        if start + window_words >= len(words):
            break
    return windows


def load_text_file(
    path: str,
    course: str,
    *,
    window_words: int = _DEFAULT_WINDOW_WORDS,
    overlap_words: int = _DEFAULT_OVERLAP_WORDS,
) -> list[Page]:
    """Load a `.md`/`.txt` course file into prose Pages.

    The file is read as UTF-8 and split into overlapping prose windows (see
    :func:`split_prose`). Each window becomes one prose ``Page``:

    - ``course`` comes from the caller (used in citations);
    - ``chapter`` is the file stem, a stable source label for the document;
    - ``page`` is the 1-based window index (there is no real page geometry);
    - ``doc_type`` is ``"prose"`` so chunking uses the prose path.

    An empty or whitespace-only file yields no Pages (handled gracefully, like
    blank slides). No PyMuPDF, no vision model and no network access is used.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    chapter = os.path.splitext(os.path.basename(path))[0]
    windows = split_prose(text, window_words=window_words, overlap_words=overlap_words)
    if not windows:
        logger.warning("text file %r has no extractable content", path)
        return []

    pages = [
        Page(course=course, page=i, text=window, doc_type="prose", chapter=chapter)
        for i, window in enumerate(windows, start=1)
    ]
    for page in pages[:3]:
        logger.info("prose window %d (%s):\n%s\n", page.page, chapter, page.text[:400])
    return pages
