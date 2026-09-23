#!/usr/bin/env python3
"""Loopback-only static server for the Molt dev console.

Serves exactly two things:

* files inside ``console/`` (the document root), excluding dotfiles; and
* ``/data/<name>``: a fixed, explicit allowlist of read-only repository
  artifacts (``DATA_ALLOWLIST`` below).

Nothing else in the repository is reachable. In particular ``.env``, ``.git``,
``.venv`` and any path containing ``..`` or a dot-segment return 404. The
server always binds ``127.0.0.1``; there is no option to bind other
interfaces.

Usage (from anywhere):

    python3 console/serve.py            # http://127.0.0.1:8420/
    python3 console/serve.py --port 9000
"""

from __future__ import annotations

import argparse
import http.server
import posixpath
import sys
import urllib.parse
from functools import partial
from pathlib import Path

CONSOLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = CONSOLE_DIR.parent
BIND_HOST = "127.0.0.1"

# Published name -> repository-relative path. Add entries deliberately; never
# add a directory or a glob.
DATA_ALLOWLIST = {
    "candidates.json": "experiments/candidates.json",
    "feasibility_probes.json": "experiments/feasibility_probes.json",
    "probe_logs.txt": "experiments/probe_logs.txt",
    "pilot_config.json": "experiments/pilot_config.json",
    "pilot_estimate.json": "experiments/pilot_estimate.json",
    "ceilings.json": "experiments/ceilings.json",
    "rule_schema.json": "experiments/rule_schema.json",
    "pilot_evidence_packet.md": "experiments/pilot_evidence_packet.md",
    "CANDIDATES.md": "DOCS/CANDIDATES.md",
    "pyjwt_manual_rule.json": "migrations/pyjwt-1-to-2/rule.json",
    "engine_result.json": "experiments/engine_runs/pyjwt_fixture_result.json",
}

CONTENT_TYPES = {
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


def resolve_request(url_path: str) -> Path | None:
    """Map a request path to a file on disk, or None if it must not be served."""
    path = urllib.parse.unquote(urllib.parse.urlsplit(url_path).path)
    if "\x00" in path or "\\" in path:
        return None
    segments = [s for s in path.split("/") if s]
    # Reject any traversal or hidden segment before normalisation can hide it.
    if any(s == ".." or s.startswith(".") for s in segments):
        return None

    if segments[:1] == ["data"]:
        if len(segments) != 2 or segments[1] not in DATA_ALLOWLIST:
            return None
        target = (REPO_ROOT / DATA_ALLOWLIST[segments[1]]).resolve()
        return target if target.is_file() else None

    normalised = posixpath.normpath("/" + "/".join(segments)).lstrip("/")
    target = (CONSOLE_DIR / normalised).resolve()
    try:
        target.relative_to(CONSOLE_DIR)
    except ValueError:
        return None
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file() or target.name == Path(__file__).name:
        return None
    return target


class ConsoleHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):  # noqa: D401 - stdlib override
        target = resolve_request(self.path)
        if target is None:
            self.send_error(404, "Not found")
            return None
        try:
            f = open(target, "rb")
        except OSError:
            self.send_error(404, "Not found")
            return None
        data_len = target.stat().st_size
        self.send_response(200)
        ctype = CONTENT_TYPES.get(target.suffix) or self.guess_type(str(target))
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(data_len))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        return f

    def do_POST(self):  # read-only server
        self.send_error(405, "Read-only")

    do_PUT = do_DELETE = do_PATCH = do_POST

    def log_message(self, fmt, *args):
        sys.stderr.write("[console] " + (fmt % args) + "\n")


def make_server(port: int = 8420) -> http.server.ThreadingHTTPServer:
    handler = partial(ConsoleHandler, directory=str(CONSOLE_DIR))
    return http.server.ThreadingHTTPServer((BIND_HOST, port), handler)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8420)
    args = parser.parse_args(argv)
    server = make_server(args.port)
    print(f"Molt console on http://{BIND_HOST}:{server.server_address[1]}/ (console/ + /data allowlist only)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
