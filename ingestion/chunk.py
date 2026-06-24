"""Adaptive chunking.

Slides carry little text but strong per-slide structure, so one slide maps to
one chunk (token-based splitting would glue several slides together). Prose
documents would instead be split into ~500-token windows with overlap; that
path is added when a prose document is first ingested.

Each chunk carries {course, chapter, page} metadata used to build citations.
"""

import logging
import uuid

from ingestion.schema import Chunk, Page

logger = logging.getLogger(__name__)


def _chunk_id(course: str, page: int) -> str:
    """Stable UUID so re-ingesting a course overwrites rather than duplicates.

    Qdrant point ids must be unsigned ints or UUIDs, hence uuid5 over a stable key.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{course}-p{page}"))


def chunk_pages(pages: list[Page], *, log_sample: int = 3) -> list[Chunk]:
    """Turn extracted pages into retrievable chunks.

    Empty pages (e.g. title or section dividers with no transcribable content)
    are dropped. A few chunks are logged for visual inspection before the
    pipeline is trusted.
    """
    chunks: list[Chunk] = []
    for page in pages:
        if page.doc_type != "slides":
            raise NotImplementedError(f"chunking for doc_type={page.doc_type!r}")
        if not page.text.strip():
            continue
        chunks.append(
            Chunk(
                id=_chunk_id(page.course, page.page),
                course=page.course,
                page=page.page,
                text=page.text,
                chapter=page.chapter,
            )
        )

    for chunk in chunks[:log_sample]:
        logger.info("chunk %s (p.%d):\n%s\n", chunk.id, chunk.page, chunk.text[:400])

    return chunks
