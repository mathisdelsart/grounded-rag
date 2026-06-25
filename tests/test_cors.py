"""CORS middleware behavior.

The app configures CORS at import time from ``Settings.cors_origins`` (default:
local dev origins), so these tests exercise the default configuration: an
allowed origin is echoed (incl. on the preflight), a disallowed origin is not.
"""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)

ALLOWED = "http://localhost:3000"


def test_allowed_origin_is_echoed():
    response = client.get("/health", headers={"Origin": ALLOWED})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ALLOWED


def test_preflight_for_allowed_origin_succeeds():
    response = client.options(
        "/ask",
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == ALLOWED


def test_disallowed_origin_is_not_echoed():
    response = client.get("/health", headers={"Origin": "http://evil.example.com"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != "http://evil.example.com"
