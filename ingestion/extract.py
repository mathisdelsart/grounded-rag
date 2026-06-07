"""PDF extraction (math-aware).

Per-page strategy: PyMuPDF for standard text, Marker for math-heavy pages
(Markdown output with LaTeX preserved).
"""

# TODO: implement extract_pdf(path) -> list[Page]
