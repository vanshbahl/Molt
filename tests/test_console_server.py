"""Regression tests for the console server's exposure boundary and tab router."""

import http.client
import importlib.util
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSOLE = REPO_ROOT / "console"

spec = importlib.util.spec_from_file_location("console_serve", CONSOLE / "serve.py")
serve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve)

FORBIDDEN_PATHS = [
    "/.env",
    "/../.env",
    "/%2e%2e/.env",
    "/..%2f.env",
    "/%2e%2e%2f.env",
    "/data/../.env",
    "/data/.env",
    "/data/..%2f..%2f.env",
    "/.git/config",
    "/../.git/config",
    "/../experiments/pilot_config.json",
    "/data/pilot_config.json/../../.env",
    "/data/nonexistent.json",
    "/serve.py",
    "/../README.md",
    "/..\\.env",
]


@pytest.mark.parametrize("path", FORBIDDEN_PATHS)
def test_resolver_rejects_everything_outside_console_and_allowlist(path):
    assert serve.resolve_request(path) is None


def test_resolver_serves_console_files_and_allowlisted_data():
    assert serve.resolve_request("/") == CONSOLE / "index.html"
    assert serve.resolve_request("/panels/_util.js") == CONSOLE / "panels" / "_util.js"
    assert serve.resolve_request("/data/candidates.json") == REPO_ROOT / "experiments" / "candidates.json"


def test_allowlist_never_contains_secrets_or_directories():
    for name, rel in serve.DATA_ALLOWLIST.items():
        assert "/" not in name and not name.startswith(".")
        assert ".env" not in rel and not any(part.startswith(".") for part in Path(rel).parts)
        target = REPO_ROOT / rel
        assert not target.is_dir()


def test_bind_host_is_loopback_only():
    assert serve.BIND_HOST == "127.0.0.1"


@pytest.fixture
def live_server():
    server = serve.make_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


def _get(server, path):
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, body


def test_live_server_binds_loopback(live_server):
    assert live_server.server_address[0] == "127.0.0.1"


@pytest.mark.parametrize("path", FORBIDDEN_PATHS)
def test_live_server_never_serves_forbidden_paths(live_server, path):
    status, body = _get(live_server, path)
    assert status == 404
    assert b"GEMINI_API_KEY" not in body


def test_live_server_serves_console_and_data(live_server):
    status, body = _get(live_server, "/")
    assert status == 200 and b"Molt dev console" in body
    status, _ = _get(live_server, "/data/pilot_config.json")
    assert status == 200


def test_live_server_is_read_only(live_server):
    conn = http.client.HTTPConnection("127.0.0.1", live_server.server_address[1], timeout=5)
    conn.request("POST", "/data/pilot_config.json", body=b"{}")
    assert conn.getresponse().status == 405
    conn.close()


def test_tab_router_does_not_clear_rendered_panels():
    """Regression: revisiting an already-loaded tab rendered a blank panel
    because the first visit to another tab ran `root.innerHTML = ""`."""
    app = (CONSOLE / "app.js").read_text(encoding="utf-8")
    assert 'root.innerHTML = ""' not in app
    assert "c.hidden = c !== container" in app
