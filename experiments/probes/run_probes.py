#!/usr/bin/env python3
"""Reproduce the M0 feasibility probes in fresh, isolated virtualenvs.

For every environment in PROBE_ENVS: create a venv, pip-install the pinned
packages from PyPI, run the probe scripts in this directory, parse their
`RESULT {...}` line, and classify old-pass / new-fail. Also reproduces the
PyJWT fixture repository's old-pass / new-fail / migrated-pass sequence using
the Molt engine (tests/fixtures/pyjwt_repo, a synthetic fixture, not an
admitted client repository).

Cost: zero. Needs network access to PyPI only; no API keys, no model calls.

    python3 experiments/probes/run_probes.py            # writes results/probe_run_<UTC date>.json + .txt
    python3 experiments/probes/run_probes.py --keep DIR # reuse/keep venvs in DIR
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
RESULTS = HERE / "results"

PROBE_ENVS = {
    "pyjwt-1.7.1": ["pyjwt==1.7.1", "pytest==8.3.3"],
    "pyjwt-2.10.1": ["pyjwt==2.10.1", "pytest==8.3.3"],
    "sqlalchemy-1.3.24": ["sqlalchemy==1.3.24"],
    "sqlalchemy-2.0.35": ["sqlalchemy==2.0.35"],
    "pydantic-1.10.14": ["pydantic==1.10.14"],
    "pydantic-2.9.2": ["pydantic==2.9.2"],
}


def _ok(result, *keys):
    return all(result.get(k, {}).get("ok") for k in keys)


# candidate_id -> (script, old env, new env, predicate(result) -> True when the API works)
SCRIPT_PROBES = {
    "pyjwt-1-to-2": ("pyjwt_algorithms.py", "pyjwt-1.7.1", "pyjwt-2.10.1",
                     lambda r: _ok(r, "decode_without_algorithms")),
    "pyjwt-1-to-2-bounded-task": ("pyjwt_bounded_task.py", "pyjwt-1.7.1", "pyjwt-2.10.1",
                                  lambda r: _ok(r, "old_exception_name")
                                  and _ok(r, "flat_verify_expiration")),
    "sqlalchemy-1.4-to-2.0": ("sqlalchemy_select.py", "sqlalchemy-1.3.24", "sqlalchemy-2.0.35",
                              lambda r: _ok(r, "select_list_form")),
    "pydantic-1-to-2": ("pydantic_imports.py", "pydantic-1.10.14", "pydantic-2.9.2",
                        lambda r: _ok(r, "BaseSettings_import")),
}


def run(cmd, cwd=None, timeout=900):
    env = {k: v for k, v in os.environ.items() if "KEY" not in k.upper() and "TOKEN" not in k.upper()}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def venv_python(root: Path, name: str, packages, log) -> Path:
    path = root / name
    py = path / "bin" / "python"
    if not py.exists():
        code, out, err = run([sys.executable, "-m", "venv", str(path)])
        if code:
            raise RuntimeError(f"venv {name} failed: {err}")
        code, out, err = run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", *packages])
        log.append(f"$ pip install {' '.join(packages)}  (exit {code})\n{err.strip()[-800:]}".rstrip())
        if code:
            raise RuntimeError(f"pip install for {name} failed: {err[-500:]}")
    return py


def parse_result(stdout: str):
    for line in stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):])
    return None


def classify(works: bool) -> str:
    return "pass" if works else "fail"


def fixture_probe(pythons, log):
    """Synthetic fixture: old-pass, new-fail, and Molt-migrated pass under the new version."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from molt.engine import apply_rule

    stages = {}
    with tempfile.TemporaryDirectory(prefix="molt-probe-fixture-") as tmp:
        for stage, env_name, migrate in (("old", "pyjwt-1.7.1", False), ("new", "pyjwt-2.10.1", False),
                                         ("migrated", "pyjwt-2.10.1", True)):
            repo = Path(tmp) / stage
            shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "pyjwt_repo", repo)
            cmd = [str(pythons[env_name]), "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]
            if migrate:
                result = apply_rule(REPO_ROOT / "migrations" / "pyjwt-1-to-2" / "rule.json", repo,
                                    verify_command=cmd, write=True)
                stages["migrated_engine_status"] = result.status
            code, out, err = run(cmd, cwd=repo)
            tail = (out.strip().splitlines() or [""])[-1]
            log.append(f"=== pyjwt fixture repo, {stage} ({env_name}) ===\n$ python -m pytest -q tests\n{tail}")
            stages[stage] = {"env": env_name, "status": classify(code == 0), "exit_code": code, "summary": tail}
    return stages


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--keep", help="directory in which to create (and keep) the probe venvs")
    parser.add_argument("--out", default=str(RESULTS), help="directory for the result files")
    args = parser.parse_args(argv)

    started = datetime.datetime.now(datetime.timezone.utc)
    venv_root = Path(args.keep) if args.keep else Path(tempfile.mkdtemp(prefix="molt-probes-"))
    venv_root.mkdir(parents=True, exist_ok=True)
    log = [f"Molt M0 feasibility probes — {started.isoformat()}",
           f"host python {platform.python_version()} on {platform.platform()}"]
    try:
        pythons = {name: venv_python(venv_root, name, pkgs, log) for name, pkgs in PROBE_ENVS.items()}
        probes = []
        for cid, (script, old_env, new_env, works) in SCRIPT_PROBES.items():
            entry = {"candidate_id": cid, "script": f"experiments/probes/{script}"}
            for side, env_name in (("old", old_env), ("new", new_env)):
                code, out, err = run([str(pythons[env_name]), str(HERE / script)])
                result = parse_result(out)
                log.append(f"=== {cid} [{side}: {env_name}] ===\n$ python {script}\n{out.strip()}\n{err.strip()[-600:]}".rstrip())
                entry[f"{side}_env"] = env_name
                entry[f"{side}_result"] = {"status": classify(bool(result) and works(result)) if result else "error",
                                           "observed": result, "exit_code": code}
            entry["reproduced_old_pass_new_fail"] = (entry["old_result"]["status"], entry["new_result"]["status"]) == ("pass", "fail")
            probes.append(entry)
        fixture = fixture_probe(pythons, log)
    finally:
        if not args.keep:
            shutil.rmtree(venv_root, ignore_errors=True)

    record = {
        "generated_at": started.isoformat(),
        "method": "fresh venv per environment; pip install pinned packages from PyPI; run probe script; parse RESULT line",
        "host": {"python": platform.python_version(), "platform": platform.platform()},
        "environments": PROBE_ENVS,
        "probes": probes,
        "pyjwt_fixture_repo": fixture,
        "caveat": "Single-script reproductions and a synthetic fixture; not repository admission evidence.",
    }
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"probe_run_{started.strftime('%Y%m%d')}"
    (out_dir / f"{stem}.json").write_text(json.dumps(record, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    (out_dir / f"{stem}.txt").write_text("\n\n".join(log) + "\n", encoding="utf-8")
    for p in probes:
        print(f"{p['candidate_id']:28s} old={p['old_result']['status']:5s} new={p['new_result']['status']:5s}")
    print(f"{'pyjwt fixture repo':28s} old={fixture['old']['status']} new={fixture['new']['status']} "
          f"migrated={fixture['migrated']['status']} (engine {fixture.get('migrated_engine_status')})")
    print(f"-> {out_dir / stem}.json/.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
