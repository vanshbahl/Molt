"""End-to-end engine behaviour: PASS / FAIL / ABSTAIN / UNVERIFIED with evidence."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from molt import cli
from molt.engine import apply_rule, transform_source
from molt.models import RESULT_SCHEMA_VERSION
from molt.schema import load_rule

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE_PATH = REPO_ROOT / "migrations" / "pyjwt-1-to-2" / "rule.json"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pyjwt_repo"
PYTEST = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]


def _pyjwt2_available():
    try:
        import jwt
    except ImportError:
        return False
    return int(jwt.__version__.split(".")[0]) >= 2


needs_pyjwt2 = pytest.mark.skipif(not _pyjwt2_available(), reason="PyJWT 2.x (pip install -e '.[dev]') required")


@pytest.fixture
def repo(tmp_path):
    dst = tmp_path / "pyjwt_repo"
    shutil.copytree(FIXTURE, dst)
    return dst


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def make_repo(root: Path, files: dict) -> Path:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# PASS
# ---------------------------------------------------------------------------


@needs_pyjwt2
def test_fixture_fails_under_pyjwt2_before_migration(repo):
    """Sanity: the fixture really is broken by the upgrade (old-pass is in experiments/probes)."""
    proc = subprocess.run(PYTEST, cwd=repo, capture_output=True, text=True)
    assert proc.returncode != 0


@needs_pyjwt2
def test_pass_changes_all_sites_and_verifies_in_a_copy(repo):
    before = tree_hash(repo)
    result = apply_rule(RULE_PATH, repo, verify_command=PYTEST)
    assert result.status == "PASS", (result.reason, result.verification)
    assert result.summary == {"matched": 5, "changed": 5, "abstained": 0}
    assert result.repo["files_changed"] == 2
    assert result.verification.status == "pass" and "4 passed" in result.verification.stdout_tail
    assert tree_hash(repo) == before, "dry run must not modify the repository"
    assert not result.written


@needs_pyjwt2
def test_write_publishes_only_on_pass_and_result_is_idempotent(repo):
    result = apply_rule(RULE_PATH, repo, verify_command=PYTEST, write=True)
    assert result.status == "PASS" and result.written
    assert subprocess.run(PYTEST, cwd=repo, capture_output=True).returncode == 0
    again = apply_rule(RULE_PATH, repo, verify_command=PYTEST)
    assert again.status == "ABSTAIN" and again.reason.startswith("no_applicable_sites")
    assert again.diff == "" and again.summary["matched"] == 0


@needs_pyjwt2
def test_diff_applies_cleanly_and_matches_written_result(repo, tmp_path):
    result = apply_rule(RULE_PATH, repo, verify_command=PYTEST)
    patched = tmp_path / "patched"
    shutil.copytree(FIXTURE, patched)
    patch_file = tmp_path / "change.diff"
    patch_file.write_text(result.diff, encoding="utf-8")
    subprocess.run(["git", "apply", str(patch_file)], cwd=patched, check=True,
                   capture_output=True)
    apply_rule(RULE_PATH, repo, verify_command=PYTEST, write=True)
    assert tree_hash(patched) == tree_hash(repo)
    assert result.diff.count("+++ b/") == 2 and "+++ b/app/codec.py" not in result.diff


def test_repeated_runs_produce_identical_results(repo):
    a = apply_rule(RULE_PATH, repo).to_dict()
    b = apply_rule(RULE_PATH, repo).to_dict()
    for d in (a, b):
        d["verification"]["duration_s"] = None
    assert a == b


# ---------------------------------------------------------------------------
# FAIL
# ---------------------------------------------------------------------------


@needs_pyjwt2
def test_incomplete_rule_fails_real_verification(repo, tmp_path):
    data = json.loads(RULE_PATH.read_text())
    data["operations"] = [op for op in data["operations"] if op["op"] != "replace_call"]
    result = apply_rule(data, repo, verify_command=PYTEST, write=True)
    assert result.status == "FAIL" and result.reason.startswith("verification_fail")
    assert "test_expired_token_still_decodes_when_expiry_disabled" in result.verification.stdout_tail
    assert not result.written
    assert tree_hash(repo) == tree_hash(FIXTURE), "FAIL must never write"


def test_failing_command_gives_fail(repo):
    result = apply_rule(RULE_PATH, repo, verify_command=[sys.executable, "-c", "import sys; sys.exit(3)"])
    assert result.status == "FAIL" and result.verification.exit_code == 3


def test_verification_timeout_gives_fail(repo):
    result = apply_rule(RULE_PATH, repo, verify_command=[sys.executable, "-c", "import time; time.sleep(5)"], timeout_s=0.5)
    assert result.status == "FAIL" and result.verification.status == "timeout"


def test_missing_verifier_executable_gives_fail(repo):
    result = apply_rule(RULE_PATH, repo, verify_command=["/nonexistent/molt-verifier"])
    assert result.status == "FAIL" and result.verification.status == "error"


def test_invalid_rule_fails_before_touching_anything(repo):
    data = json.loads(RULE_PATH.read_text())
    data["operations"][3]["argument_edits"][0]["dict_key"] = "import os"
    before = tree_hash(repo)
    result = apply_rule(data, repo, verify_command=PYTEST, write=True)
    assert result.status == "FAIL" and result.reason.startswith("rule_invalid")
    assert result.rule_errors and result.sites == [] and result.diff == ""
    assert tree_hash(repo) == before


def test_verification_environment_excludes_credentials(repo, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")
    monkeypatch.setenv("SOME_SERVICE_TOKEN", "fake")
    probe = "import os, sys; sys.exit(1 if {'GEMINI_API_KEY', 'SOME_SERVICE_TOKEN'} & set(os.environ) else 0)"
    result = apply_rule(RULE_PATH, repo, verify_command=[sys.executable, "-c", probe])
    assert result.verification.status == "pass"


# ---------------------------------------------------------------------------
# ABSTAIN / UNVERIFIED
# ---------------------------------------------------------------------------


def test_no_safe_transformation_gives_abstain(tmp_path):
    root = make_repo(tmp_path / "r", {
        "svc/tokens.py": (
            "import jwt\n\n\n"
            "def read(token, key, **opts):\n"
            "    return jwt.decode(token, key, verify_expiration=False, **opts)\n\n\n"
            "def legacy(token, key):\n"
            "    return jwt.decode(token, key)\n"
        ),
    })
    before = tree_hash(root)
    result = apply_rule(RULE_PATH, root, verify_command=[sys.executable, "-c", "pass"], write=True)
    assert result.status == "ABSTAIN" and result.reason.startswith("no_safe_transformation")
    assert result.summary == {"matched": 3, "changed": 0, "abstained": 3}
    assert {s.op_id for s in result.sites} == {"decode-verify-expiration-into-options", "decode-missing-algorithms"}
    assert result.verification.status == "not_run"
    assert tree_hash(root) == before and result.diff == ""


def test_partial_migration_with_abstentions_is_not_pass(tmp_path):
    root = make_repo(tmp_path / "r", {
        "svc/errors.py": "import jwt\n\nEXPIRED = jwt.ExpiredSignature\n",
        "svc/read.py": "import jwt\n\n\ndef read(t, k):\n    return jwt.decode(t, k)\n",
    })
    result = apply_rule(RULE_PATH, root, verify_command=[sys.executable, "-c", "pass"], write=True)
    assert result.status == "ABSTAIN" and result.reason.startswith("partial")
    assert (result.summary["changed"], result.summary["abstained"]) == (1, 1)
    assert not result.written


def test_repository_without_the_library_abstains(tmp_path):
    root = make_repo(tmp_path / "r", {"pkg/a.py": "import json\nprint(json.dumps({}))\n"})
    result = apply_rule(RULE_PATH, root, verify_command=[sys.executable, "-c", "pass"])
    assert result.status == "ABSTAIN" and result.reason.startswith("no_applicable_sites")
    assert result.repo["files_with_candidates"] == 0


def test_no_verification_command_is_unverified_not_pass(repo):
    result = apply_rule(RULE_PATH, repo, write=True)
    assert result.status == "UNVERIFIED" and result.verification.status == "not_run"
    assert not result.written and result.summary["changed"] == 5


def test_parse_errors_are_reported_and_other_files_still_processed(tmp_path):
    root = make_repo(tmp_path / "r", {
        "a.py": "print 'py2'\n",
        "b.py": "import jwt\nX = jwt.InvalidIssuer\n",
    })
    result = apply_rule(RULE_PATH, root, verify_command=[sys.executable, "-c", "pass"])
    assert [(i.file, i.kind) for i in result.file_issues] == [("a.py", "parse_error")]
    assert result.status == "PASS" and result.summary["changed"] == 1


def test_test_files_are_never_transformed_by_default(repo):
    result = apply_rule(RULE_PATH, repo)
    assert all(not s.file.startswith("tests/") for s in result.sites)


# ---------------------------------------------------------------------------
# Result format (console integration boundary)
# ---------------------------------------------------------------------------


def test_result_dict_matches_documented_format(repo):
    data = apply_rule(RULE_PATH, repo, verify_command=[sys.executable, "-c", "pass"]).to_dict()
    json.dumps(data)  # must be JSON-serialisable
    assert list(data) == ["schema", "engine_version", "status", "reason", "rule", "repo", "summary", "verification",
                          "sites", "file_issues", "rule_errors", "diff", "dry_run", "written"]
    assert data["schema"] == RESULT_SCHEMA_VERSION
    assert set(data["sites"][0]) == {"op_id", "op", "file", "line", "column", "decision", "reason", "before", "after"}
    assert data["rule"]["sha256"] == load_rule(RULE_PATH).sha256


def test_committed_console_sample_is_current():
    """experiments/engine_runs/pyjwt_fixture_result.json is regenerated by
    experiments/engine_runs/generate.py; it must match current engine output."""
    sample_path = REPO_ROOT / "experiments" / "engine_runs" / "pyjwt_fixture_result.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    fresh = apply_rule(RULE_PATH, FIXTURE, repo_label="tests/fixtures/pyjwt_repo").to_dict()
    for key in ("status", "summary", "sites", "diff", "rule"):
        if key == "rule":
            assert sample[key]["sha256"] == fresh[key]["sha256"]
        elif key != "status":
            assert sample[key] == fresh[key], key


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@needs_pyjwt2
def test_cli_apply_dry_run_output(repo, capsys, tmp_path):
    out_json = tmp_path / "result.json"
    code = cli.main(["apply", str(RULE_PATH), str(repo), "--verify", " ".join(PYTEST), "--json", str(out_json)])
    out = capsys.readouterr().out
    assert code == 0
    for line in ("Matched: 5", "Changed: 5", "Abstained: 0", "Verification:", "Result: PASS", "no (dry run)"):
        assert line in out
    assert json.loads(out_json.read_text())["status"] == "PASS"
    assert tree_hash(repo) == tree_hash(FIXTURE)


def test_cli_exit_codes(tmp_path, capsys):
    root = make_repo(tmp_path / "r", {"a.py": "import jwt\njwt.decode(t, k)\n"})
    assert cli.main(["apply", str(RULE_PATH), str(root), "--verify", f"{sys.executable} -c pass"]) == 3
    assert cli.main(["validate", str(RULE_PATH)]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": "molt.rule.v2"}', encoding="utf-8")
    assert cli.main(["validate", str(bad)]) == 1
    assert "INVALID" in capsys.readouterr().out


def test_transform_source_helper_matches_engine(repo):
    src = (repo / "app" / "auth.py").read_text()
    out, _ = transform_source(src, load_rule(RULE_PATH))
    result = apply_rule(RULE_PATH, repo)
    assert "+    return jwt.decode(token, SECRET, algorithms=[\"HS256\"], options={\"verify_exp\": False})" in result.diff
    assert 'options={"verify_exp": False}' in out
