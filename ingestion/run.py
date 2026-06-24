"""Ingestion entry point: PDF -> pages -> chunks -> Qdrant.

Usage:
    python -m ingestion.run path/to/course.pdf --course "Wavelet Transform"
"""

import argparse
import logging

from ingestion.chunk import chunk_pages
from ingestion.extract import extract_pdf
from ingestion.index import index_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a course PDF into Qdrant.")
    parser.add_argument("pdf", help="Path to the course PDF.")
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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    pages = extract_pdf(
        args.pdf, args.course, dpi=args.dpi, max_pages=args.max_pages, pages=args.pages
    )
    chunks = chunk_pages(pages)
    index_chunks(chunks)
    print(f"Ingested {len(chunks)} chunks from {args.pdf!r} into course {args.course!r}.")


if __name__ == "__main__":
    main()
