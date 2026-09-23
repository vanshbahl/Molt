"""Typed, immutable representations of rules and engine results.

Rules are parsed from validated JSON into these dataclasses (see schema.py).
The engine consumes only these types, never the raw JSON, so every field the
engine acts on is explicit and typed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional, Union

SCHEMA_VERSION = "molt.rule.v2"
RESULT_SCHEMA_VERSION = "molt.engine_result.v1"

# ---------------------------------------------------------------------------
# Rule model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypedValue:
    """A typed literal inserted by add_keyword/add_argument. Never raw code."""

    type: str  # "bool" | "int" | "str" | "none"
    value: Union[bool, int, str, None] = None


@dataclass(frozen=True)
class ArgumentEdit:
    kind: str  # move_keyword_into_dict | rename_keyword | remove_keyword | add_keyword
    keyword: str
    dict_keyword: Optional[str] = None
    dict_key: Optional[str] = None
    when_dict_exists: str = "merge"
    new_keyword: Optional[str] = None
    value: Optional[TypedValue] = None


@dataclass(frozen=True)
class RenameSymbol:
    id: str
    qualified_old_name: str
    qualified_new_name: str
    op: str = "rename_symbol"

    @property
    def module(self) -> str:
        return self.qualified_old_name.rsplit(".", 1)[0]

    @property
    def old_attr(self) -> str:
        return self.qualified_old_name.rsplit(".", 1)[1]

    @property
    def new_attr(self) -> str:
        return self.qualified_new_name.rsplit(".", 1)[1]


@dataclass(frozen=True)
class ChangeImport:
    id: str
    old_module: str
    new_module: str
    name: str
    new_name: Optional[str] = None
    op: str = "change_import"


@dataclass(frozen=True)
class ReplaceCall:
    """Atomic keyword-argument restructuring at call sites of ``target_call``.

    ``rename_argument``/``add_argument``/``remove_argument`` are normalised to
    this form with a single edit; ``op`` keeps the name the rule author used.
    ``trigger_keyword`` is None only for add_argument (every call lacking the
    keyword is a candidate).
    """

    id: str
    target_call: str
    trigger_keyword: Optional[str]
    argument_edits: tuple
    op: str = "replace_call"


@dataclass(frozen=True)
class Abstain:
    id: str
    target_call: str
    reason: str
    when_keyword_absent: Optional[str] = None
    op: str = "abstain"


Operation = Union[RenameSymbol, ChangeImport, ReplaceCall, Abstain]


@dataclass(frozen=True)
class RuleBundle:
    bundle_id: str
    bundle_version: str
    library: str
    import_module: Optional[str]
    old_version_range: str
    new_version_range: str
    operations: tuple
    sha256: str  # hash of the canonical JSON serialisation

    def modules(self) -> set:
        """Top-level modules the rule's qualified names live in (file pre-filter)."""
        tops = set()
        for op in self.operations:
            for name in _qualified_names(op):
                tops.add(name.split(".")[0])
        if self.import_module:
            tops.add(self.import_module)
        return tops


def _qualified_names(op) -> list:
    if isinstance(op, RenameSymbol):
        return [op.qualified_old_name]
    if isinstance(op, ChangeImport):
        return [op.old_module]
    return [op.target_call]


# ---------------------------------------------------------------------------
# Result model (console-consumable; see DOCS/ENGINE.md)
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
ABSTAIN = "ABSTAIN"
UNVERIFIED = "UNVERIFIED"

CHANGED = "changed"
ABSTAINED = "abstained"


@dataclass
class Site:
    op_id: str
    op: str
    file: str
    line: int
    column: int
    decision: str  # "changed" | "abstained"
    reason: str
    before: str
    after: Optional[str] = None


@dataclass
class FileIssue:
    file: str
    kind: str  # "parse_error" | "invalid_output"
    detail: str


@dataclass
class Verification:
    command: list
    status: str  # "pass" | "fail" | "timeout" | "error" | "not_run"
    exit_code: Optional[int] = None
    duration_s: Optional[float] = None
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class EngineResult:
    status: str
    reason: str
    rule: dict
    repo: dict
    summary: dict
    sites: list = field(default_factory=list)
    file_issues: list = field(default_factory=list)
    rule_errors: list = field(default_factory=list)
    diff: str = ""
    verification: Optional[Verification] = None
    dry_run: bool = True
    written: bool = False
    engine_version: str = ""
    schema: str = RESULT_SCHEMA_VERSION

    def to_dict(self) -> dict:
        data = asdict(self)
        # Stable key order for the console and for byte-comparable reruns.
        order = [
            "schema", "engine_version", "status", "reason", "rule", "repo", "summary",
            "verification", "sites", "file_issues", "rule_errors", "diff", "dry_run", "written",
        ]
        return {k: data[k] for k in order}
