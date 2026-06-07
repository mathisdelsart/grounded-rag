"""Shared state for the LangGraph graph."""

from typing import Any, TypedDict


class TutorState(TypedDict, total=False):
    """State passed between graph nodes."""

    student_id: str
    message: str
    intent: str  # explain | generate | grade | reexplain
    retrieved: list[Any]
    answer: str
    exercise: dict[str, Any]
    grade: dict[str, Any]
    history: list[Any]
