"""Security system tests.

IDs (PT-01, XSS-01, CFG-03 ...) match the test cases in
activities/sprint2/Security_Architecture_and_Testing_Plan.md.

Tests marked xfail(strict=True) cover known findings that aren't fixed yet.
When a finding is fixed, its test starts passing, strict mode turns that into
a failure, and that is the reminder to remove the xfail marker.
"""

from __future__ import annotations

import urllib.parse

import pytest

# Text that would only appear if a file outside static/ leaked
LEAK_MARKERS = [
    "from flask import",      # web/app.py
    "genotype,status",        # core/results/growth_comparison.csv
    "root:x:0:0",             # /etc/passwd
    "gunicorn",               # site-packages source
]

TRAVERSAL_PATHS = {
    "PT-01": "/static/../app.py",
    "PT-02a": "/static/..%2fapp.py",
    "PT-02b": "/static/%2e%2e/app.py",
    "PT-02c": "/static/%2e%2e%2fapp.py",
    "PT-03": "/static/..%252fapp.py",
    "PT-04": "/static/..%5capp.py",
    "PT-05a": "/static//etc/passwd",
    "PT-05b": "/static/%2fetc%2fpasswd",
    "PT-05c": "/static/../../../../etc/passwd",
    "PT-06": "/static/css/main.css%00.js",
    "PT-extra-results": "/static/%2e%2e%2f%2e%2e%2fcore/results/growth_comparison.csv",
}

XSS_PAYLOADS = {
    "XSS-01": "<script>alert(1)</script>",
    "XSS-02": '"><img src=x onerror=alert(1)>',
    "XSS-03": "javascript:alert(1)",
    "XSS-04": "{{7*7}}",
}


@pytest.mark.parametrize("path", list(TRAVERSAL_PATHS.values()), ids=list(TRAVERSAL_PATHS))
def test_path_traversal_is_blocked(raw_get, path):
    status, headers, body = raw_get(path)

    # A redirect is fine only if following it still leads nowhere
    hops = 0
    while 300 <= status < 400 and hops < 3:
        location = urllib.parse.urlsplit(headers.get("location", ""))
        status, headers, body = raw_get(location.path or "/")
        hops += 1

    assert status in (400, 404), f"{path} returned {status}"
    for marker in LEAK_MARKERS:
        assert marker not in body, f"{path} leaked {marker!r}"


@pytest.mark.parametrize("payload", list(XSS_PAYLOADS.values()), ids=list(XSS_PAYLOADS))
def test_form_input_is_never_reflected(client, base_url, payload):
    r = client.post(f"{base_url}/", data={"genes": payload}, timeout=10)
    assert r.status_code == 200
    assert payload not in r.text
    assert "That combination isn&#39;t in the dataset." in r.text


@pytest.mark.parametrize("method", ["PUT", "DELETE", "PATCH", "TRACE"])
def test_unused_http_methods_are_rejected(client, base_url, method):
    assert client.request(method, f"{base_url}/", timeout=10).status_code == 405


def test_not_running_flask_dev_server(client, base_url):
    """F1: production must not use the Werkzeug dev server or its debugger."""
    r = client.get(f"{base_url}/", timeout=10)
    assert "werkzeug" not in r.headers.get("Server", "").lower()
    assert client.get(f"{base_url}/console", timeout=10).status_code == 404


def test_error_pages_hide_internals(client, base_url):
    r = client.get(f"{base_url}/no-such-page", timeout=10)
    for leak in ("Traceback", "File \"", "site-packages", "/app/web"):
        assert leak not in r.text


# --- known findings, not fixed yet ------------------------------------------

@pytest.mark.xfail(strict=True, reason="F2: security headers not added yet (CFG-03, XSS-07, XSS-08)")
def test_security_headers_present(client, base_url):
    for path in ("/", "/api/curves", "/static/css/main.css"):
        h = client.get(f"{base_url}{path}", timeout=10).headers
        assert "Content-Security-Policy" in h, path
        assert h.get("X-Content-Type-Options") == "nosniff", path
        assert "frame-ancestors" in h.get("Content-Security-Policy", "") or "X-Frame-Options" in h, path


@pytest.mark.xfail(strict=True, reason="F3: no request size limit yet (CFG-02)")
def test_large_request_is_rejected(client, base_url):
    r = client.post(f"{base_url}/", data={"genes": "a" * 20_000}, timeout=10)
    assert r.status_code == 413
