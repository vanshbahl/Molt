"""Run a verification command against a transformed copy of a repository.

The command runs without a shell, in the copy's root, with a timeout and an
environment stripped of credential-like variables. This is the M1 local
verifier, not the Phase 4 container harness.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from .models import Verification
from .parser import EXCLUDED_DIRS

SECRET_NAME = re.compile(r"(API_?KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)
TAIL_CHARS = 4000


def sanitized_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not SECRET_NAME.search(k)}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MOLT_NO_NETWORK"] = "1"
    return env


def resolve_command(command, cwd: Path) -> list:
    """Make a relative executable path absolute w.r.t. the caller's cwd, since
    the command itself runs inside the temporary copy."""
    argv = list(command)
    if argv and os.sep in argv[0] and not os.path.isabs(argv[0]):
        argv[0] = str((Path(cwd) / argv[0]).resolve())
    return argv


def copy_repo(src: Path, dst: Path) -> None:
    shutil.copytree(
        src, dst, symlinks=True,
        ignore=shutil.ignore_patterns(*sorted(EXCLUDED_DIRS - {"build", "dist"})),
    )


def _tail(text: str) -> str:
    return text if len(text) <= TAIL_CHARS else "…" + text[-TAIL_CHARS:]


def run_verification(command, workdir: Path, timeout_s: float = 300) -> Verification:
    argv = list(command)
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            argv, cwd=workdir, env=sanitized_env(), capture_output=True, text=True, timeout=timeout_s
        )
    except subprocess.TimeoutExpired as exc:
        return Verification(argv, "timeout", None, round(time.perf_counter() - start, 3),
                            _tail(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                            f"timed out after {timeout_s}s")
    except OSError as exc:
        return Verification(argv, "error", None, round(time.perf_counter() - start, 3), "", str(exc))
    return Verification(
        argv,
        "pass" if proc.returncode == 0 else "fail",
        proc.returncode,
        round(time.perf_counter() - start, 3),
        _tail(proc.stdout),
        _tail(proc.stderr),
    )
