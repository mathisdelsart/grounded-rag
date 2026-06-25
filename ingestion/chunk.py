"""Adaptive chunking.

Slides carry little text but strong per-slide structure, so one slide maps to
one chunk (token-based splitting would glue several slides together). Prose
documents (Markdown / text course files) are split upstream by
:mod:`ingestion.load` into overlapping word windows, each already a ready
``Page``; here each prose window likewise maps to one chunk.

Each chunk carries {course, chapter, page} metadata used to build citations.
"""

import logging
import uuid

from ingestion.schema import Chunk, Page

logger = logging.getLogger(__name__)


def _chunk_id(course: str, page: int, chapter: str | None) -> str:
    """Stable UUID so re-ingesting a course overwrites rather than duplicates.

    Qdrant point ids must be unsigned ints or UUIDs, hence uuid5 over a stable
    key. Slides have a globally unique page number within a course, so the key
    is ``course``+``page``. Prose ``page`` is only a per-document window index,
    so the document's ``chapter`` is folded in to keep windows from different
    files distinct. Slide keys are unchanged (``chapter`` is None there), so
    existing slide ids stay byte-identical.
    """
    key = f"{course}-p{page}" if chapter is None else f"{course}-{chapter}-p{page}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def chunk_pages(pages: list[Page], *, log_sample: int = 3) -> list[Chunk]:
    """Turn extracted pages into retrievable chunks.

    Both slide pages (one per slide) and prose windows (one per word window from
    :mod:`ingestion.load`) map one-to-one to a chunk; only the chunk-id key
    differs (see :func:`_chunk_id`). Empty pages (e.g. title or section dividers
    with no content) are dropped. A few chunks are logged for visual inspection
    before the pipeline is trusted.
    """
    chunks: list[Chunk] = []
    for page in pages:
        if page.doc_type not in ("slides", "prose"):
            raise NotImplementedError(f"chunking for doc_type={page.doc_type!r}")
        if not page.text.strip():
            continue
        chunks.append(
            Chunk(
                id=_chunk_id(page.course, page.page, page.chapter),
                course=page.course,
                page=page.page,
                text=page.text,
                chapter=page.chapter,
            )
        )

    for chunk in chunks[:log_sample]:
        logger.info("chunk %s (p.%d):\n%s\n", chunk.id, chunk.page, chunk.text[:400])

    return chunks
