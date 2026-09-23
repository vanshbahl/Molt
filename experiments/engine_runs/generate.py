#!/usr/bin/env python3
"""Regenerate the committed engine-result sample consumed by the dev console.

Runs the manual PyJWT reference rule against tests/fixtures/pyjwt_repo in
dry-run mode, verifying with the fixture's own test suite under the current
interpreter (needs PyJWT 2.x: `pip install -e '.[dev]'`). The fixture is not
modified. Output: experiments/engine_runs/pyjwt_fixture_result.json

    .venv/bin/python experiments/engine_runs/generate.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from molt.engine import apply_rule  # noqa: E402

RULE = REPO_ROOT / "migrations" / "pyjwt-1-to-2" / "rule.json"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "pyjwt_repo"
OUT = Path(__file__).resolve().parent / "pyjwt_fixture_result.json"


def main() -> int:
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]
    result = apply_rule(RULE, FIXTURE, verify_command=command, repo_label="tests/fixtures/pyjwt_repo")
    data = result.to_dict()
    data["rule"]["path"] = "migrations/pyjwt-1-to-2/rule.json"
    data["verification"]["command"] = ["python"] + command[1:]  # don't commit a local interpreter path
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{data['status']}: {data['reason']} -> {OUT.relative_to(REPO_ROOT)}")
    return 0 if data["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
