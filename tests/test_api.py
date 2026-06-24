"""Tests for the FastAPI service.

No real LLM, vector store, or network call is made: the underlying grounded
function and graph nodes are monkeypatched in the ``api.main`` namespace, so the
routes are exercised in isolation. The module is skipped when the optional
``api`` extra (FastAPI) is not installed, so CI without extras collects cleanly.
"""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

import api.main as api_main  # noqa: E402
from api.main import app  # noqa: E402

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_grounded_answer_and_sources(monkeypatch):
    captured = {}

    def fake_answer(question, *, k=5):
        captured["question"] = question
        captured["k"] = k
        return {
            "answer": "A wavelet is ... (Course, p.11)",
            "refused": False,
            "sources": ["(Course, p.11)"],
            "raw": "A wavelet is ... [1]",
        }

    monkeypatch.setattr(api_main, "answer", fake_answer)

    response = client.post("/ask", json={"question": "What is a wavelet?", "k": 3})
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "answer": "A wavelet is ... (Course, p.11)",
        "refused": False,
        "sources": ["(Course, p.11)"],
    }
    # The request reached the grounded function with its parameters intact.
    assert captured == {"question": "What is a wavelet?", "k": 3}
    # The internal raw model output is not exposed by the API.
    assert "raw" not in body


def test_ask_uses_default_k(monkeypatch):
    captured = {}

    def fake_answer(question, *, k=5):
        captured["k"] = k
        return {"answer": "ok", "refused": False, "sources": [], "raw": "ok"}

    monkeypatch.setattr(api_main, "answer", fake_answer)

    response = client.post("/ask", json={"question": "anything"})
    assert response.status_code == 200
    assert captured["k"] == 5


def test_ask_surfaces_refusal(monkeypatch):
    def fake_answer(question, *, k=5):
        return {
            "answer": "This is not covered in the course material.",
            "refused": True,
            "sources": [],
            "raw": "This is not covered in the course material.",
        }

    monkeypatch.setattr(api_main, "answer", fake_answer)

    response = client.post("/ask", json={"question": "off-topic"})
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["sources"] == []


def test_exercise_returns_problem_without_solution(monkeypatch):
    captured = {}

    def fake_generate(state):
        captured["message"] = state["message"]
        return {
            "exercise": {"problem": "Compute X.", "solution": "X = 42.", "refused": False},
            "retrieved": ["(Course, p.7)"],
        }

    monkeypatch.setattr(api_main, "generate", fake_generate)

    response = client.post("/exercise", json={"notion": "integrals"})
    assert response.status_code == 200
    body = response.json()
    assert body == {"problem": "Compute X.", "refused": False}
    assert captured["message"] == "integrals"
    # The reference solution must never leak to the client.
    assert "solution" not in body


def test_exercise_surfaces_refusal(monkeypatch):
    def fake_generate(state):
        return {
            "exercise": {
                "problem": "This is not covered in the course material.",
                "solution": "",
                "refused": True,
            },
            "retrieved": [],
        }

    monkeypatch.setattr(api_main, "generate", fake_generate)

    response = client.post("/exercise", json={"notion": "off-topic"})
    assert response.status_code == 200
    assert response.json()["refused"] is True


def test_grade_returns_score_and_feedback(monkeypatch):
    captured = {}

    def fake_grade(state):
        captured["state"] = state
        return {"grade": {"score": 80, "feedback": "Good method."}}

    monkeypatch.setattr(api_main, "grade", fake_grade)

    response = client.post(
        "/grade",
        json={"message": "X = 42", "exercise": {"solution": "X = 42"}},
    )
    assert response.status_code == 200
    assert response.json() == {"score": 80, "feedback": "Good method."}
    # Both the answer and the optional reference exercise reached the node.
    assert captured["state"]["message"] == "X = 42"
    assert captured["state"]["exercise"] == {"solution": "X = 42"}


def test_grade_without_exercise(monkeypatch):
    captured = {}

    def fake_grade(state):
        captured["state"] = state
        return {"grade": {"score": 0, "feedback": "No reference provided."}}

    monkeypatch.setattr(api_main, "grade", fake_grade)

    response = client.post("/grade", json={"message": "X = 42"})
    assert response.status_code == 200
    assert response.json()["feedback"] == "No reference provided."
    # No exercise key is forwarded when the request omits it.
    assert "exercise" not in captured["state"]


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/ask", {}),
        ("/exercise", {}),
        ("/grade", {}),
    ],
)
def test_missing_required_field_is_422(path, body):
    response = client.post(path, json=body)
    assert response.status_code == 422
