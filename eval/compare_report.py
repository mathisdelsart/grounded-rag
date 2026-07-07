"""Render a side-by-side Markdown comparison of two benchmark runs.

Takes the two metrics dicts written by :func:`eval.benchmark.write_results`
(one per provider, e.g. OpenAI and Groq) and produces a single Markdown table
comparing them column by column, with a delta column for the rate metrics.

The core ``render_comparison`` function is pure (no I/O) and tolerant of missing
keys, so it works on any subset of the metrics. ``write_comparison`` and
``render_comparison_from_files`` are thin I/O wrappers. No LLM is involved.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Rate metrics rendered as percentages, in display order.
_RATE_METRICS: tuple[tuple[str, str], ...] = (
    ("refusal_accuracy", "Refusal accuracy"),
    ("faithfulness_rate", "Faithfulness"),
    ("relevance_rate", "Relevance"),
    ("citation_rate", "Citation rate"),
    ("retrieval_hit_rate", "Retrieval hit rate"),
    ("answer_keyword_rate", "Answer-keyword rate"),
)

# Latency metrics rendered in milliseconds.
_LATENCY_METRICS: tuple[tuple[str, str], ...] = (
    ("retrieval_p50_ms", "Retrieval latency p50"),
    ("retrieval_p95_ms", "Retrieval latency p95"),
)

# Plain integer counters reported below the table, when present.
_COUNT_METRICS: tuple[tuple[str, str], ...] = (
    ("total", "Total cases"),
    ("judged", "Judged cases"),
    ("retrieval_checked", "Retrieval checked"),
)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _percent(value: Any) -> str:
    return f"{value:.0%}" if _is_number(value) else "n/a"


def _ms(value: Any) -> str:
    return f"{value:.0f} ms" if _is_number(value) else "n/a"


def _delta_percent(a: Any, b: Any) -> str:
    """Signed percentage-point delta (b - a), or ``n/a`` if either is missing."""
    if _is_number(a) and _is_number(b):
        pts = (b - a) * 100.0
        return f"{pts:+.1f} pts"
    return "n/a"


def _delta_ms(a: Any, b: Any) -> str:
    if _is_number(a) and _is_number(b):
        return f"{b - a:+.0f} ms"
    return "n/a"


def _label(metrics: Mapping[str, Any], fallback: str) -> str:
    provider = metrics.get("provider")
    return str(provider) if provider else fallback


def render_comparison(
    metrics_a: Mapping[str, Any],
    metrics_b: Mapping[str, Any],
    *,
    label_a: str | None = None,
    label_b: str | None = None,
    title: str = "Benchmark comparison",
) -> str:
    """Render two metrics dicts as a side-by-side Markdown report (pure, no I/O).

    Column labels default to each run's ``provider`` field, falling back to
    ``A``/``B``. Any metric absent from both dicts is skipped, so partial dicts
    render cleanly. The delta column is ``B - A``.
    """
    col_a = label_a or _label(metrics_a, "A")
    col_b = label_b or _label(metrics_b, "B")
    lines: list[str] = [f"# {title}", ""]

    lines.append(f"| Metric | {col_a} | {col_b} | Delta (B - A) |")
    lines.append("| --- | --- | --- | --- |")

    any_row = False
    for key, label in _RATE_METRICS:
        if key not in metrics_a and key not in metrics_b:
            continue
        any_row = True
        a, b = metrics_a.get(key), metrics_b.get(key)
        lines.append(f"| {label} | {_percent(a)} | {_percent(b)} | {_delta_percent(a, b)} |")
    for key, label in _LATENCY_METRICS:
        if key not in metrics_a and key not in metrics_b:
            continue
        any_row = True
        a, b = metrics_a.get(key), metrics_b.get(key)
        lines.append(f"| {label} | {_ms(a)} | {_ms(b)} | {_delta_ms(a, b)} |")
    if not any_row:
        lines.append("| _(no metrics)_ | n/a | n/a | n/a |")

    counters = [
        (label, metrics_a.get(key), metrics_b.get(key))
        for key, label in _COUNT_METRICS
        if key in metrics_a or key in metrics_b
    ]
    if counters:
        lines.extend(["", "## Counts", ""])
        lines.append(f"| Metric | {col_a} | {col_b} |")
        lines.append("| --- | --- | --- |")
        for label, a, b in counters:
            va = a if a is not None else "n/a"
            vb = b if b is not None else "n/a"
            lines.append(f"| {label} | {va} | {vb} |")

    return "\n".join(lines) + "\n"


def write_comparison(
    metrics_a: Mapping[str, Any],
    metrics_b: Mapping[str, Any],
    path: Path,
    *,
    label_a: str | None = None,
    label_b: str | None = None,
    title: str = "Benchmark comparison",
) -> None:
    """Render the comparison and write it to ``path`` (creating parent dirs)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_comparison(metrics_a, metrics_b, label_a=label_a, label_b=label_b, title=title),
        encoding="utf-8",
    )


def render_comparison_from_files(
    path_a: Path,
    path_b: Path,
    *,
    label_a: str | None = None,
    label_b: str | None = None,
    title: str = "Benchmark comparison",
) -> str:
    """Load two metrics JSON files and render the comparison (convenience helper)."""
    metrics_a = json.loads(Path(path_a).read_text(encoding="utf-8"))
    metrics_b = json.loads(Path(path_b).read_text(encoding="utf-8"))
    return render_comparison(metrics_a, metrics_b, label_a=label_a, label_b=label_b, title=title)


def main(argv: list[str] | None = None) -> int:
    """CLI: write a Markdown comparison of two benchmark metrics JSON files."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare two benchmark metrics JSON files side by side."
    )
    parser.add_argument("metrics_a", type=Path, help="First run's metrics JSON.")
    parser.add_argument("metrics_b", type=Path, help="Second run's metrics JSON.")
    parser.add_argument("--label-a", default=None, help="Column label for the first run.")
    parser.add_argument("--label-b", default=None, help="Column label for the second run.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the Markdown to this path; otherwise print to stdout.",
    )
    args = parser.parse_args(argv)

    md = render_comparison_from_files(
        args.metrics_a, args.metrics_b, label_a=args.label_a, label_b=args.label_b
    )
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
        print(f"wrote comparison: {args.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
