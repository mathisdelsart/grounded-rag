"""Ingestion entry point: document -> pages -> chunks -> Qdrant.

Usage:
    python -m ingestion.run path/to/course.pdf --course "Wavelet Transform"
    python -m ingestion.run path/to/notes.md  --course "Wavelet Transform"

The input type is detected by extension. PDFs go through the math-aware vision
pipeline (slides). Markdown (`.md`) and text (`.txt`) files are plain prose:
they are read straight from disk as UTF-8 and split into overlapping prose
windows -- no PyMuPDF, no vision model, no network. PDF-only flags (`--pages`,
`--max-pages`, `--dpi`, `--hybrid`, `--concurrency`) are no-ops for text inputs;
`--course`, `--sparse` and `--batch-size` apply to both.

Pages are processed in batches (extract -> chunk -> index per batch) so a crash
mid-run keeps the progress of earlier batches instead of losing everything. Chunk
ids are stable UUIDs, so re-running is idempotent: an interrupted run can simply
be re-run and already-indexed pages are overwritten cleanly.
"""

import argparse
import logging

from ingestion.chunk import chunk_pages
from ingestion.extract import extract_pdf
from ingestion.index import index_chunks
from ingestion.load import is_text_file, load_text_file
from ingestion.schema import Page

logger = logging.getLogger(__name__)


def _pdf_page_count(path: str) -> int:
    """Return the number of pages in a PDF (imported lazily, like extract_pdf)."""
    import fitz  # PyMuPDF, imported lazily so the ingestion extra is optional.

    doc = fitz.open(path)
    try:
        return doc.page_count
    finally:
        doc.close()


def _resolve_page_numbers(
    path: str, *, pages: list[int] | None, max_pages: int | None
) -> list[int]:
    """Resolve the ordered 1-based page numbers to ingest.

    Explicit `--pages` take priority (in the given order); otherwise the natural
    document order is used. `--max-pages` caps the selection to the first N pages
    so batching covers exactly the same pages the previous all-at-once flow did.
    """
    if pages:
        selected = list(pages)
    else:
        selected = list(range(1, _pdf_page_count(path) + 1))
    if max_pages is not None:
        selected = selected[:max_pages]
    return selected


def _format_pages(pages: list[int]) -> str:
    """Render a page list compactly for logs (first..last for a contiguous run)."""
    if len(pages) > 1 and pages == list(range(pages[0], pages[-1] + 1)):
        return f"{pages[0]}..{pages[-1]}"
    return ", ".join(str(p) for p in pages)


def _index_text_file(path: str, course: str, *, sparse: bool, batch_size: int) -> int:
    """Ingest a `.md`/`.txt` prose file: load -> chunk -> index in batches.

    The whole file is read once and split into prose windows (`Page`s); those
    windows are then chunked and indexed in batches of `batch_size`, mirroring
    the PDF path's per-batch indexing so a crash keeps earlier progress.
    PDF-only options (pages/dpi/vision/concurrency) do not apply here. Returns
    the total number of indexed chunks.
    """
    pages: list[Page] = load_text_file(path, course)
    if not pages:
        print(f"No content extracted from {path!r}; nothing to ingest.")
        return 0

    batches = [pages[i : i + batch_size] for i in range(0, len(pages), batch_size)]
    total_chunks = 0
    for batch_no, batch_pages in enumerate(batches, start=1):
        chunks = chunk_pages(batch_pages)
        index_chunks(chunks, sparse=sparse)
        total_chunks += len(chunks)
        logger.info(
            "batch %d/%d indexed: %d chunks (%d total so far)",
            batch_no,
            len(batches),
            len(chunks),
            total_chunks,
        )
    return total_chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest course material (PDF, Markdown or text) into Qdrant."
    )
    parser.add_argument("pdf", help="Path to the course file (.pdf, .md or .txt).")
    parser.add_argument("--course", required=True, help="Course name (used in citations).")
    parser.add_argument("--max-pages", type=int, default=None, help="Cap pages while iterating.")
    parser.add_argument(
        "--pages",
        type=int,
        nargs="+",
        default=None,
        help="Explicit 1-based pages to extract (e.g. --pages 10 11). Overrides order.",
    )
    parser.add_argument("--dpi", type=int, default=150, help="Rasterization resolution.")
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help="Route plain-text pages to free PyMuPDF extraction; vision only for "
        "math/figure-heavy pages. Default sends every page to the vision model.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Maximum number of vision transcriptions running at once.",
    )
    parser.add_argument(
        "--sparse",
        action="store_true",
        help="Also index bge-m3 lexical (sparse) vectors as Qdrant named vectors, "
        "enabling opt-in hybrid dense+sparse retrieval (HYBRID_RETRIEVAL=1). "
        "Creates a named-vector collection; choose one mode per collection.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Pages per extract->chunk->index batch. Indexing each batch as it "
        "is produced keeps prior progress if the run crashes mid-way.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")

    # Markdown/text inputs are plain prose: skip the PDF/vision pipeline and the
    # PDF-only flags (pages/dpi/hybrid/concurrency are no-ops here).
    if is_text_file(args.pdf):
        total_chunks = _index_text_file(
            args.pdf, args.course, sparse=args.sparse, batch_size=args.batch_size
        )
        if total_chunks:
            print(f"Ingested {total_chunks} chunks from {args.pdf!r} into course {args.course!r}.")
        return

    page_numbers = _resolve_page_numbers(args.pdf, pages=args.pages, max_pages=args.max_pages)
    if not page_numbers:
        print(f"No pages selected from {args.pdf!r}; nothing to ingest.")
        return

    batches = [
        page_numbers[i : i + args.batch_size] for i in range(0, len(page_numbers), args.batch_size)
    ]
    total_chunks = 0
    for batch_no, batch_pages in enumerate(batches, start=1):
        logger.info("batch %d/%d: pages %s", batch_no, len(batches), _format_pages(batch_pages))
        pages = extract_pdf(
            args.pdf,
            args.course,
            dpi=args.dpi,
            pages=batch_pages,
            hybrid=args.hybrid,
            concurrency=args.concurrency,
        )
        chunks = chunk_pages(pages)
        index_chunks(chunks, sparse=args.sparse)
        total_chunks += len(chunks)
        logger.info(
            "batch %d/%d indexed: %d chunks (%d total so far)",
            batch_no,
            len(batches),
            len(chunks),
            total_chunks,
        )

    print(f"Ingested {total_chunks} chunks from {args.pdf!r} into course {args.course!r}.")


if __name__ == "__main__":
    main()
