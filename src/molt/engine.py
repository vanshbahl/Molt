"""End-to-end deterministic application of one rule bundle to one repository.

Flow (DOCS/ENGINE.md):

    load + validate rule -> discover files -> parse -> pre-filter by import
    -> for each operation in order: fresh metadata, match, rewrite
    -> re-parse every output -> unified diff
    -> copy repo to a temp dir, write outputs, run verification there
    -> classify PASS / FAIL / ABSTAIN / UNVERIFIED
    -> (only with write=True and PASS) publish files to the repo

The repository itself is never modified unless ``write=True`` and the
result is PASS; all outputs are validated before any byte is written.
"""

from __future__ import annotations

import difflib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

import libcst as cst
from libcst.metadata import MetadataWrapper

from . import ENGINE_VERSION
from .matcher import APPLY, match_operation
from .models import (
    ABSTAIN,
    ABSTAINED,
    CHANGED,
    FAIL,
    PASS,
    UNVERIFIED,
    EngineResult,
    FileIssue,
    RuleBundle,
    Site,
    Verification,
)
from .parser import discover_python_files, import_facts, parse_file, parse_source
from .schema import RuleValidationError, load_rule
from .transformer import SiteRewriter, rewrite_functions
from .verifier import copy_repo, run_verification

SNIPPET_CHARS = 300


def _snippet(module: cst.Module, node: cst.CSTNode) -> str:
    code = module.code_for_node(node)
    return code if len(code) <= SNIPPET_CHARS else code[: SNIPPET_CHARS - 1] + "…"


@dataclass
class FileOutcome:
    rel_path: str
    before: bytes
    after: bytes
    sites: list


def transform_module(module: cst.Module, rule: RuleBundle, rel_path: str):
    """Apply every operation in order to one module. Returns (module, sites)."""
    sites = []
    for op in rule.operations:
        wrapper = MetadataWrapper(module)
        decisions = match_operation(wrapper, op, import_facts(wrapper.module))
        if not decisions:
            continue
        rewrites = {}
        for d in decisions:
            if d.decision == APPLY:
                rewrites.update(rewrite_functions(op, d))
        rewriter = SiteRewriter(rewrites)
        new_module = wrapper.module.visit(rewriter) if rewrites else wrapper.module
        for d in decisions:
            applied = d.decision == APPLY
            produced = rewriter.produced.get(id(d.node))
            sites.append(Site(
                op_id=op.id, op=op.op, file=rel_path, line=d.line, column=d.column,
                decision=CHANGED if applied else ABSTAINED, reason=d.reason,
                before=_snippet(wrapper.module, d.node),
                after=_snippet(new_module, produced) if applied and produced is not None else None,
            ))
        module = new_module
    return module, sites


def transform_source(source: Union[str, bytes], rule: RuleBundle, rel_path: str = "<string>"):
    """Convenience for tests: transform one source string."""
    raw = source.encode("utf-8") if isinstance(source, str) else source
    module, sites = transform_module(parse_source(raw), rule, rel_path)
    return module.code, sites


def unified_diff(outcomes: Sequence[FileOutcome]) -> str:
    chunks = []
    for o in outcomes:
        if o.before == o.after:
            continue
        chunks.extend(difflib.unified_diff(
            o.before.decode("utf-8", "surrogateescape").splitlines(keepends=True),
            o.after.decode("utf-8", "surrogateescape").splitlines(keepends=True),
            fromfile=f"a/{o.rel_path}", tofile=f"b/{o.rel_path}",
        ))
    return "".join(chunks)


def _write_files(root: Path, outcomes: Sequence[FileOutcome]) -> None:
    for o in outcomes:
        if o.before == o.after:
            continue
        target = root / o.rel_path
        tmp = target.with_name(f".{target.name}.molt-tmp")
        tmp.write_bytes(o.after)
        os.replace(tmp, target)


def _rule_summary(rule: Optional[RuleBundle], rule_path: str) -> dict:
    if rule is None:
        return {"path": rule_path}
    return {"path": rule_path, "bundle_id": rule.bundle_id, "bundle_version": rule.bundle_version, "sha256": rule.sha256}


def apply_rule(
    rule_source: Union[str, Path, dict],
    repo: Union[str, Path],
    *,
    verify_command: Optional[Sequence[str]] = None,
    write: bool = False,
    include_tests: bool = False,
    timeout_s: float = 300,
    repo_label: Optional[str] = None,
) -> EngineResult:
    repo = Path(repo).resolve()
    rule_label = rule_source if isinstance(rule_source, (str, Path)) else "<dict>"
    repo_info = {"path": repo_label or repo.name, "files_scanned": 0, "files_with_candidates": 0, "files_changed": 0}
    base = dict(engine_version=ENGINE_VERSION, dry_run=not write, repo=repo_info)

    try:
        rule = load_rule(rule_source)
    except RuleValidationError as exc:
        return EngineResult(
            status=FAIL, reason="rule_invalid: the rule failed schema/semantic validation; nothing was applied",
            rule=_rule_summary(None, str(rule_label)), summary=_summary([]), rule_errors=[str(i) for i in exc.issues],
            verification=Verification([], "not_run"), **base,
        )

    rule_modules = rule.modules()
    outcomes, sites, issues = [], [], []
    files = discover_python_files(repo, include_tests=include_tests)
    repo_info["files_scanned"] = len(files)
    for rel in files:
        parsed = parse_file(repo, rel)
        if parsed.module is None:
            issues.append(FileIssue(rel, "parse_error", parsed.error))
            continue
        if not (import_facts(parsed.module).modules & rule_modules):
            continue  # no import of the rule's library: no candidate syntax
        repo_info["files_with_candidates"] += 1
        new_module, file_sites = transform_module(parsed.module, rule, rel)
        after = new_module.bytes
        if after != parsed.source:
            try:
                parse_source(after)  # every output must re-parse before anything is written
            except cst.ParserSyntaxError as exc:
                issues.append(FileIssue(rel, "invalid_output", str(exc)))
                file_sites = [_as_abstained(s, "engine produced unparsable output; file left unchanged") for s in file_sites]
                after = parsed.source
        sites.extend(file_sites)
        outcomes.append(FileOutcome(rel, parsed.source, after, file_sites))

    changed_files = [o for o in outcomes if o.before != o.after]
    repo_info["files_changed"] = len(changed_files)
    summary = _summary(sites)
    result = EngineResult(
        status=ABSTAIN, reason="", rule=_rule_summary(rule, str(rule_label)), summary=summary,
        sites=sites, file_issues=issues, diff=unified_diff(outcomes), **base,
    )

    if not changed_files:
        result.reason = ("no_safe_transformation: every candidate site abstained" if summary["abstained"]
                         else "no_applicable_sites: nothing in the repository matches the rule")
        result.verification = Verification(list(verify_command or []), "not_run")
        return result

    if verify_command:
        with tempfile.TemporaryDirectory(prefix="molt-verify-") as tmp:
            workdir = Path(tmp) / "repo"
            copy_repo(repo, workdir)
            _write_files(workdir, changed_files)
            result.verification = run_verification(verify_command, workdir, timeout_s)
    else:
        result.verification = Verification([], "not_run")

    v = result.verification.status
    if v == "not_run":
        result.status, result.reason = UNVERIFIED, "no verification command: the transformation is untested"
    elif v != "pass":
        result.status, result.reason = FAIL, f"verification_{v}: the transformed repository did not pass"
    elif summary["abstained"]:
        result.status = ABSTAIN
        result.reason = f"partial: verification passed but {summary['abstained']} site(s) abstained and still need a human"
    else:
        result.status, result.reason = PASS, "all candidate sites changed and verification passed"

    if write and result.status == PASS:
        _write_files(repo, changed_files)
        result.written = True
    return result


def _as_abstained(site: Site, reason: str) -> Site:
    site.decision, site.reason, site.after = ABSTAINED, reason, None
    return site


def _summary(sites) -> dict:
    changed = sum(1 for s in sites if s.decision == CHANGED)
    abstained = sum(1 for s in sites if s.decision == ABSTAINED)
    return {"matched": changed + abstained, "changed": changed, "abstained": abstained}
