"""Tests for the answer-feedback endpoints (thumbs up/down).

No LLM, vector store, or network call is involved: feedback is pure persistence.
The API is bound to an in-memory SQLite database so the routes run in isolation.
The module is skipped when the optional ``api`` extra (FastAPI) is not installed,
so CI without extras collects cleanly.
"""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from api import runtime as api_main  # noqa: E402
from api.main import app  # noqa: E402
from db.models import Feedback, Student  # noqa: E402


@pytest.fixture
def client():
    """Bind the API to a fresh in-memory SQLite DB and yield a test client."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    api_main.configure_engine(engine)
    with TestClient(app) as test_client:
        yield test_client
    api_main._engine = None


def _post_feedback(client, **overrides):
    body = {
        "student_id": "s1",
        "rating": 1,
        "question": "What is a wavelet?",
        "answer": "A wavelet is ... (Course, p.11)",
    }
    body.update(overrides)
    return client.post("/feedback", json=body)


# --- persistence -------------------------------------------------------------


def test_feedback_persists_row_with_rating_and_qa(client):
    response = _post_feedback(client, rating=1, note="clear and well cited")
    assert response.status_code == 201
    feedback_id = response.json()["id"]
    assert isinstance(feedback_id, int)

    with api_main.get_session(api_main._engine) as session:
        row = session.scalar(select(Feedback).where(Feedback.id == feedback_id))
        assert row is not None
        assert row.rating == 1
        assert row.note == "clear and well cited"
        assert row.question == "What is a wavelet?"
        assert row.answer == "A wavelet is ... (Course, p.11)"
        # The feedback links to a get-or-created student.
        student = session.scalar(select(Student).where(Student.external_id == "s1"))
        assert student is not None
        assert row.student_id == student.id


def test_feedback_thumbs_down_without_note(client):
    response = _post_feedback(client, rating=-1)
    assert response.status_code == 201
    with api_main.get_session(api_main._engine) as session:
        row = session.scalar(select(Feedback).where(Feedback.id == response.json()["id"]))
        assert row is not None
        assert row.rating == -1
        assert row.note is None


# --- validation --------------------------------------------------------------


@pytest.mark.parametrize("rating", [0, 2, -2, 5, 100])
def test_feedback_rejects_invalid_rating(client, rating):
    response = _post_feedback(client, rating=rating)
    assert response.status_code == 422
    # Nothing was persisted.
    with api_main.get_session(api_main._engine) as session:
        assert session.scalar(select(Feedback)) is None


def test_feedback_requires_question_and_answer(client):
    response = client.post("/feedback", json={"student_id": "s1", "rating": 1})
    assert response.status_code == 422


# --- summary -----------------------------------------------------------------


def test_feedback_summary_counts_up_and_down(client):
    _post_feedback(client, rating=1)
    _post_feedback(client, rating=1)
    _post_feedback(client, rating=-1)

    response = client.get("/feedback/summary", params={"student_id": "s1"})
    assert response.status_code == 200
    assert response.json() == {"up": 2, "down": 1}


def test_feedback_summary_unknown_student_is_zero(client):
    response = client.get("/feedback/summary", params={"student_id": "nobody"})
    assert response.status_code == 200
    assert response.json() == {"up": 0, "down": 0}


# --- API-key authentication --------------------------------------------------

_API_KEY = "secret-key"


def _set_api_key(monkeypatch, key):
    from core.config import Settings

    settings = Settings(api_key=key)
    monkeypatch.setattr(api_main, "get_settings", lambda: settings)


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/feedback", {"student_id": "s1", "rating": 1, "question": "q", "answer": "a"}),
        ("get", "/feedback/summary?student_id=s1", None),
    ],
)
def test_feedback_rejects_missing_key(client, monkeypatch, method, path, body):
    _set_api_key(monkeypatch, _API_KEY)
    response = client.request(method, path, json=body)
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "path", "body", "expected"),
    [
        (
            "post",
            "/feedback",
            {"student_id": "s1", "rating": 1, "question": "q", "answer": "a"},
            201,
        ),
        ("get", "/feedback/summary?student_id=s1", None, 200),
    ],
)
def test_feedback_accepts_correct_key(client, monkeypatch, method, path, body, expected):
    _set_api_key(monkeypatch, _API_KEY)
    response = client.request(method, path, json=body, headers={"X-API-Key": _API_KEY})
    assert response.status_code == expected


def test_feedback_open_when_no_key_configured(client, monkeypatch):
    _set_api_key(monkeypatch, "")
    response = _post_feedback(client)
    assert response.status_code == 201


# --- existing endpoints unaffected -------------------------------------------


def test_health_still_ok_with_feedback_routes(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
