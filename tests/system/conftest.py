"""Shared setup for the system tests.

These tests talk to a running copy of the web app over HTTP, the same way a
browser does. In CI that copy is the Docker image; locally you can point them
at any running server:

    SYSTEM_TEST_BASE_URL=http://localhost:5000 pytest tests/system -v
"""

from __future__ import annotations

import http.client
import os
import re
import time
import urllib.parse

import pytest
import requests

BASE_URL = os.environ.get("SYSTEM_TEST_BASE_URL", "http://localhost:8000").rstrip("/")
STARTUP_TIMEOUT_S = float(os.environ.get("SYSTEM_TEST_STARTUP_TIMEOUT", "60"))


@pytest.fixture(scope="session", autouse=True)
def server_is_up() -> None:
    """Wait for the app to answer before any test runs."""
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    last_error = None
    while time.monotonic() < deadline:
        try:
            if requests.get(f"{BASE_URL}/api/curves", timeout=5).status_code == 200:
                return
        except requests.RequestException as exc:  # not up yet
            last_error = exc
        time.sleep(1)
    pytest.exit(f"App at {BASE_URL} did not respond within {STARTUP_TIMEOUT_S:.0f}s: {last_error}", returncode=2)


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def client():
    with requests.Session() as session:
        yield session


@pytest.fixture
def csrf_token(client, base_url):
    response = client.get(f"{base_url}/")
    assert response.status_code == 200
    match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', response.text)
    assert match, "home page did not render a CSRF token"
    return match.group(1)


@pytest.fixture(scope="session")
def raw_get():
    """GET a path exactly as written.

    `requests` and browsers clean up paths like `/static/../app.py` before
    sending them. Path traversal tests need the raw path to reach the server,
    so this uses http.client, which sends it untouched.
    """
    parsed = urllib.parse.urlsplit(BASE_URL)

    def _get(path: str) -> tuple[int, dict[str, str], str]:
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=10)
        try:
            conn.request("GET", path)
            response = conn.getresponse()
            body = response.read().decode("utf-8", errors="replace")
            return response.status, {k.lower(): v for k, v in response.getheaders()}, body
        finally:
            conn.close()

    return _get
