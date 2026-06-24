"""PDF extraction, math-aware.

The course material is slide decks where formulas are rendered as images or as
broken text that PyMuPDF cannot recover. Each page is therefore rasterized and
transcribed by a vision model into Markdown with LaTeX preserved, which keeps
the mathematics intact (the project's main grounding risk).
"""

import base64

import fitz  # PyMuPDF
from langchain_core.messages import HumanMessage

from config import get_llm
from ingestion.schema import Page

_PROMPT = (
    "You transcribe a single course slide into clean Markdown for a study tutor.\n"
    "Rules:\n"
    "- Preserve every formula exactly, as LaTeX: inline $...$, display $$...$$.\n"
    "- Keep titles, bullet points and tables as Markdown.\n"
    "- For figures/diagrams, add a short description in [square brackets].\n"
    "- Transcribe only what is on the slide. Do not add, explain or comment.\n"
    "- If the slide is empty, reply with an empty string."
)


def _render_page(page: "fitz.Page", dpi: int) -> str:
    """Rasterize a page to a base64-encoded PNG data URI."""
    pix = page.get_pixmap(dpi=dpi)
    b64 = base64.b64encode(pix.tobytes("png")).decode()
    return f"data:image/png;base64,{b64}"


def extract_pdf(
    path: str,
    course: str,
    *,
    dpi: int = 150,
    max_pages: int | None = None,
    pages: list[int] | None = None,
) -> list[Page]:
    """Extract a slide-deck PDF into per-slide Pages via vision transcription.

    Args:
        path: Path to the PDF file.
        course: Course name stored on every page for citations.
        dpi: Rasterization resolution; higher is sharper but larger.
        max_pages: Optional cap on the first N pages, to keep cost low.
        pages: Optional explicit 1-based page numbers to extract (overrides the
            natural order filter); useful to spend API calls only on math-heavy
            slides while validating.

    Returns:
        One Page per slide, in document order, with math preserved as LaTeX.
    """
    llm = get_llm("extract")
    doc = fitz.open(path)
    selected = set(pages) if pages else None
    result: list[Page] = []

    for i, page in enumerate(doc):
        page_no = i + 1
        if selected is not None and page_no not in selected:
            continue
        if max_pages is not None and len(result) >= max_pages:
            break
        image_uri = _render_page(page, dpi)
        message = HumanMessage(
            content=[
                {"type": "text", "text": _PROMPT},
                {"type": "image_url", "image_url": {"url": image_uri}},
            ]
        )
        text = llm.invoke([message]).content.strip()
        result.append(Page(course=course, page=page_no, text=text, doc_type="slides"))

    doc.close()
    return result
