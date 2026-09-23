"""Parser: repository discovery and syntax facts."""

import os
from pathlib import Path

from molt.parser import discover_python_files, import_facts, parse_file, parse_source

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pyjwt_repo"


def write(root: Path, files: dict) -> Path:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def test_discovers_fixture_sources_sorted_and_excludes_tests():
    assert discover_python_files(FIXTURE) == ["app/__init__.py", "app/auth.py", "app/codec.py", "app/errors.py"]
    assert "tests/test_auth.py" in discover_python_files(FIXTURE, include_tests=True)


def test_discovery_skips_vendored_hidden_and_symlinked_paths(tmp_path):
    write(tmp_path, {
        "pkg/mod.py": "", ".venv/lib/x.py": "", "node_modules/y.py": "", "build/gen.py": "",
        "pkg/test_mod.py": "", "pkg/mod_test.py": "", "conftest.py": "", "notes.txt": "",
    })
    outside = tmp_path.parent / f"{tmp_path.name}-outside.py"
    outside.write_text("import jwt\n")
    os.symlink(outside, tmp_path / "pkg" / "linked.py")
    assert discover_python_files(tmp_path) == ["pkg/mod.py"]


def test_import_facts_find_module_usage():
    facts = import_facts(parse_source(
        b"import jwt as pyjwt\n"
        b"import os.path\n"
        b"from jwt.exceptions import InvalidTokenError\n"
        b"from . import sibling\n"
        b"from .jwt import local\n"
        b"from json import *\n"
    ))
    assert facts.modules == {"jwt", "os", "json"}
    assert facts.star_modules == {"json"}


def test_imports_inside_functions_are_seen():
    facts = import_facts(parse_source(b"def f():\n    from jwt import decode\n    return decode\n"))
    assert "jwt" in facts.modules


def test_parse_error_is_reported_not_raised(tmp_path):
    write(tmp_path, {"bad.py": "print 'python 2'\n"})
    parsed = parse_file(tmp_path, "bad.py")
    assert parsed.module is None and "line" in parsed.error


def test_parse_round_trips_bytes_exactly():
    source = FIXTURE.joinpath("app", "auth.py").read_bytes()
    assert parse_source(source).bytes == source
