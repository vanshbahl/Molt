"""Repository discovery and LibCST parsing.

File discovery is deliberately conservative: sorted order for determinism,
no symlinks followed, and test files excluded by default because the
experiment contract forbids methods from editing existing tests.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import libcst as cst
from libcst.helpers import get_full_name_for_node

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", ".env", ".tox", ".nox", "__pycache__",
    "node_modules", "site-packages", "build", "dist", ".mypy_cache", ".pytest_cache", ".eggs",
}
TEST_PATTERNS = ("test_*.py", "*_test.py", "conftest.py")
TEST_DIRS = {"tests", "test", "testing"}


def is_test_path(rel: Path) -> bool:
    return any(part in TEST_DIRS for part in rel.parts[:-1]) or any(
        fnmatch.fnmatch(rel.name, pat) for pat in TEST_PATTERNS
    )


def discover_python_files(repo: Path, include_tests: bool = False) -> list:
    """Repository-relative POSIX paths of candidate source files, sorted."""
    repo = Path(repo)
    found = []
    for dirpath, dirnames, filenames in os.walk(repo, followlinks=False):
        base = Path(dirpath)
        dirnames[:] = sorted(
            d for d in dirnames if d not in EXCLUDED_DIRS and not (base / d).is_symlink() and not d.endswith(".egg-info")
        )
        for name in filenames:
            path = base / name
            if not name.endswith(".py") or path.is_symlink():
                continue
            rel = path.relative_to(repo)
            if not include_tests and is_test_path(rel):
                continue
            found.append(rel.as_posix())
    return sorted(found)


@dataclass
class ParsedFile:
    rel_path: str
    source: bytes
    module: Optional[cst.Module] = None
    error: Optional[str] = None


def parse_source(source: bytes) -> cst.Module:
    return cst.parse_module(source)


def parse_file(repo: Path, rel_path: str) -> ParsedFile:
    source = (Path(repo) / rel_path).read_bytes()
    try:
        return ParsedFile(rel_path, source, module=parse_source(source))
    except cst.ParserSyntaxError as exc:
        return ParsedFile(rel_path, source, error=f"{exc.message} (line {exc.raw_line}, column {exc.raw_column})")


@dataclass
class ImportFacts:
    """Cheap, syntax-only facts about a module's imports (no metadata)."""

    modules: set = field(default_factory=set)  # top-level modules imported absolutely
    star_modules: set = field(default_factory=set)  # dotted modules with `from m import *`


class _ImportCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.facts = ImportFacts()

    def visit_Import(self, node: cst.Import) -> bool:
        for alias in node.names:
            name = get_full_name_for_node(alias.name)
            if name:
                self.facts.modules.add(name.split(".")[0])
        return False

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        if node.relative or node.module is None:
            return False
        name = get_full_name_for_node(node.module)
        if name:
            self.facts.modules.add(name.split(".")[0])
            if isinstance(node.names, cst.ImportStar):
                self.facts.star_modules.add(name)
        return False


def import_facts(module: cst.Module) -> ImportFacts:
    collector = _ImportCollector()
    module.visit(collector)
    return collector.facts
