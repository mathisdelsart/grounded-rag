"""grade node: LLM-as-a-judge correcting the student's answer.

Compares the student's answer to the reference solution and returns a score plus
a *detailed* correction (what is right, what to fix, and a complete model answer).
Distinct from the system-evaluation judge (faithfulness) under eval/.

This is judge #1 (the product feature). It marks the student's answer, ideally
against the reference solution of a previously generated exercise, and returns a
numeric score together with an actionable, grounded correction.
"""

import json
import re

from agent.persistence import persist_grade
from agent.state import TutorState
from core.config import get_llm
from core.obs import get_callbacks

_SYSTEM = (
    "You are a supportive but rigorous tutor correcting a student's answer.\n"
    "- Compare the student's answer to the reference solution when one is given.\n"
    "- Reward correct method and the course's notation; point out every error and gap.\n"
    "- Write the whole correction in the SAME LANGUAGE as the student's answer.\n"
    "\n"
    "Reply in EXACTLY this format and nothing else:\n"
    "SCORE: <integer 0-100>\n"
    "---\n"
    "<a detailed correction in Markdown, translating these headings into the "
    "student's language>:\n"
    "**What you got right** — what the answer covers correctly.\n"
    "**What to fix or add** — a point-by-point list of errors, imprecisions and "
    "anything missing.\n"
    "**Model answer** — a complete, correct answer grounded in the reference and "
    "the course's notation."
)

# "SCORE: 60" — requires the colon, so a legacy JSON `"score": 60` (quote before
# the colon) does not match here and instead falls through to the JSON branch.
_SCORE_RE = re.compile(r"score\s*:\s*(-?\d+)", re.IGNORECASE)


def _clamp(value: object) -> int:
    """Clamp a model-supplied score to the documented 0-100 range."""
    try:
        return max(0, min(100, int(value)))  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return 0


def _parse(raw: str) -> dict:
    """Parse the verdict, preferring the ``SCORE:`` + Markdown format.

    A detailed correction is many lines of Markdown, which models routinely break
    when asked to embed it in a JSON string, so the primary format keeps the score
    on its own line and the correction as free Markdown after a ``---`` divider.
    A legacy ``{"score", "feedback"}`` JSON verdict is still accepted as a
    fallback so older prompts (and the test suite) keep working.
    """
    text = raw.strip()

    score_match = _SCORE_RE.search(text)
    if score_match:
        if "---" in text:
            feedback = text.split("---", 1)[1].strip()
        else:
            feedback = text[score_match.end() :].strip()
        if feedback:
            return {"score": _clamp(score_match.group(1)), "feedback": feedback}

    # Fallback: a legacy JSON verdict, tolerating extra surrounding text.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return {
                "score": _clamp(data.get("score", 0)),
                "feedback": str(data.get("feedback", "")).strip(),
            }
        except (ValueError, TypeError):
            pass

    # Unparseable: surface the raw reply as feedback rather than guess a score.
    return {"score": 0, "feedback": text}


def grade(state: TutorState) -> TutorState:
    """Grade ``state['message']`` (the student's answer) and return a verdict.

    When the answer is graded against a stored exercise (``state['exercise']``
    carries its id) the verdict is persisted for the student via the optional
    persistence layer, which is a no-op without a student, exercise or database.
    """
    exercise = state.get("exercise") or {}
    reference = exercise.get("solution", "")
    message = state.get("message", "")

    human = f"Reference solution:\n{reference}\n\nStudent answer:\n{message}"
    raw = (
        get_llm("grade")
        .invoke(
            [("system", _SYSTEM), ("human", human)],
            config={"callbacks": get_callbacks()},
        )
        .content.strip()
    )

    # Keep raw parsing internal; the node returns only the clean verdict.
    verdict = _parse(raw)

    persist_grade(
        state.get("student_id"),
        exercise_id=exercise.get("id"),
        answer=message,
        score=verdict["score"],
        feedback=verdict["feedback"],
    )

    return {"grade": verdict}
