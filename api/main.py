"""FastAPI application exposing the tutor endpoints.

Endpoints:
    GET  /health     health check
    POST /ask        answer a question, grounded in the course (explain path)
    POST /exercise   generate an exercise (never returns the reference solution)
    POST /grade      grade a student's answer

The layer stays thin: each route delegates to the existing grounded functions
and graph nodes. No retrieval or prompting logic is reimplemented here.
"""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent.nodes.generate import generate
from agent.nodes.grade import grade
from answer import answer

app = FastAPI(title="grounded-rag", description="Course tutor grounded in your own material.")


class AskRequest(BaseModel):
    """A question to answer from the course."""

    question: str
    k: int = Field(default=5, ge=1)


class AskResponse(BaseModel):
    """A grounded answer, refused when the course does not cover the question."""

    answer: str
    refused: bool
    sources: list[str]


class ExerciseRequest(BaseModel):
    """A notion to build a practice exercise on."""

    notion: str


class ExerciseResponse(BaseModel):
    """A course-grounded exercise. The reference solution is withheld."""

    problem: str
    refused: bool


class GradeRequest(BaseModel):
    """A student's answer to grade, optionally against a prior exercise."""

    message: str
    exercise: dict[str, Any] | None = None


class GradeResponse(BaseModel):
    """The judge's verdict on the student's answer."""

    score: int
    feedback: str


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> dict[str, Any]:
    """Answer a question grounded in the course, or refuse if uncovered."""
    result = answer(request.question, k=request.k)
    return {
        "answer": result["answer"],
        "refused": result["refused"],
        "sources": result["sources"],
    }


@app.post("/exercise", response_model=ExerciseResponse)
def exercise(request: ExerciseRequest) -> dict[str, Any]:
    """Generate a course-grounded exercise on the requested notion.

    The reference solution stays server-side and is never returned.
    """
    state = generate({"message": request.notion})
    built = state["exercise"]
    return {"problem": built["problem"], "refused": built["refused"]}


@app.post("/grade", response_model=GradeResponse)
def grade_answer(request: GradeRequest) -> dict[str, Any]:
    """Grade the student's answer, optionally against a prior exercise."""
    state: dict[str, Any] = {"message": request.message}
    if request.exercise is not None:
        state["exercise"] = request.exercise
    verdict = grade(state)["grade"]
    return {"score": verdict["score"], "feedback": verdict["feedback"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)
