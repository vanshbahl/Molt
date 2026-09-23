"""Conservative, binding-aware site matching.

A site is matched only through LibCST's ``QualifiedNameProvider``: the
expression must resolve to the rule's qualified name through an import, and
to nothing else. Spelling alone never authorises an edit. Outcomes per site:

* ``apply``: every structural constraint holds; the transformer may rewrite.
* ``abstain``: the site plausibly refers to the target but safety cannot be
  established (ambiguous binding, star import, **kwargs, conflicting keys,
  side effects, name collisions...). The reason is recorded.

Anything else (unrelated receivers, local shadowing, already-migrated code)
is not a candidate and produces no record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import libcst as cst
from libcst.helpers import get_full_name_for_node
from libcst.metadata import (
    ExpressionContext,
    ExpressionContextProvider,
    MetadataWrapper,
    PositionProvider,
    QualifiedNameProvider,
    QualifiedNameSource,
    ScopeProvider,
)

from .models import Abstain, ChangeImport, RenameSymbol, ReplaceCall
from .parser import ImportFacts
from .transformer import Unsafe, plan_call_edits

APPLY = "apply"
ABSTAIN = "abstain"

NO_MATCH = "no_match"
MATCH = "match"
AMBIGUOUS = "ambiguous"


@dataclass
class Decision:
    node: cst.CSTNode
    decision: str  # APPLY | ABSTAIN
    reason: str
    line: int
    column: int
    extra_nodes: list = field(default_factory=list)  # e.g. Name references renamed alongside an import


def classify(qualified_names, target: str) -> str:
    names = {q.name for q in qualified_names}
    if target not in names:
        return NO_MATCH
    if len(qualified_names) == 1 and next(iter(qualified_names)).source == QualifiedNameSource.IMPORT:
        return MATCH
    return AMBIGUOUS


def _describe(qualified_names) -> str:
    return ", ".join(sorted(f"{q.name} ({q.source.name.lower()})" for q in qualified_names))


class _Base(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider, QualifiedNameProvider)

    def __init__(self) -> None:
        super().__init__()
        self.decisions: list = []

    def record(self, node, decision, reason, extra=None):
        pos = self.get_metadata(PositionProvider, node).start
        self.decisions.append(Decision(node, decision, reason, pos.line, pos.column + 1, list(extra or [])))

    def qnames(self, node):
        return self.get_metadata(QualifiedNameProvider, node, set())


# --------------------------------------------------------------------------
# rename_symbol
# --------------------------------------------------------------------------


class RenameSymbolMatcher(_Base):
    METADATA_DEPENDENCIES = (PositionProvider, QualifiedNameProvider, ScopeProvider, ExpressionContextProvider)

    def __init__(self, op: RenameSymbol, facts: ImportFacts, module: cst.Module):
        super().__init__()
        self.op = op
        self.star = op.module in facts.star_modules
        self.names_in_module = set()
        self.strings_in_module = set()
        module.visit(_NameAndStringCollector(self.names_in_module, self.strings_in_module))

    # Import statements are handled explicitly; never descend into them.
    def visit_Import(self, node: cst.Import) -> bool:
        return False

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        if node.relative or node.module is None or isinstance(node.names, cst.ImportStar):
            return False
        if get_full_name_for_node(node.module) != self.op.module:
            return False
        for alias in node.names:
            if get_full_name_for_node(alias.name) != self.op.old_attr:
                continue
            if alias.asname is not None:
                self.record(alias, APPLY, f"from-import of {self.op.qualified_old_name} with local alias")
                continue
            self._rename_bare_import(node, alias)
        return False

    def _rename_bare_import(self, stmt: cst.ImportFrom, alias: cst.ImportAlias) -> None:
        old, new = self.op.old_attr, self.op.new_attr
        if new in self.names_in_module:
            self.record(alias, ABSTAIN, f"name {new!r} is already used in this module; renaming the binding could collide")
            return
        if old in self.strings_in_module:
            self.record(alias, ABSTAIN, f"string literal {old!r} (e.g. __all__ or getattr) refers to the old name")
            return
        scope = self.get_metadata(ScopeProvider, stmt, None)
        assignments = list(scope.assignments[old]) if scope is not None else []
        if len(assignments) != 1:
            self.record(alias, ABSTAIN, f"{old!r} is bound {len(assignments)} times in this scope; references are ambiguous")
            return
        refs = []
        for access in assignments[0].references:
            if not isinstance(access.node, cst.Name):
                self.record(alias, ABSTAIN, f"{old!r} is referenced from a non-name position (e.g. a string annotation)")
                return
            refs.append(access.node)
        self.record(alias, APPLY, f"from-import of {self.op.qualified_old_name}; {len(refs)} reference(s) renamed", refs)

    def visit_Attribute(self, node: cst.Attribute) -> Optional[bool]:
        verdict = classify(self.qnames(node), self.op.qualified_old_name)
        if verdict == NO_MATCH:
            return True
        ctx = self.get_metadata(ExpressionContextProvider, node, ExpressionContext.LOAD)
        if verdict == AMBIGUOUS:
            self.record(node, ABSTAIN, f"binding is ambiguous: {_describe(self.qnames(node))}")
        elif ctx != ExpressionContext.LOAD:
            self.record(node, ABSTAIN, f"{self.op.qualified_old_name} is assigned or deleted here, not just read")
        else:
            self.record(node, APPLY, f"attribute resolves to {self.op.qualified_old_name} via import")
        return False

    def visit_Name(self, node: cst.Name) -> None:
        # Bare names bound by `from m import old` are handled with their import.
        # Under `from m import *` the binding is unresolvable: abstain.
        if self.star and node.value == self.op.old_attr and not self.qnames(node):
            ctx = self.get_metadata(ExpressionContextProvider, node, None)
            if ctx == ExpressionContext.LOAD:
                self.record(node, ABSTAIN, f"{node.value!r} may come from `from {self.op.module} import *`; binding unresolvable")


class _NameAndStringCollector(cst.CSTVisitor):
    def __init__(self, names: set, strings: set):
        super().__init__()
        self.names, self.strings = names, strings

    def visit_Name(self, node: cst.Name) -> None:
        self.names.add(node.value)

    def visit_SimpleString(self, node: cst.SimpleString) -> None:
        try:
            value = node.evaluated_value
        except Exception:  # pragma: no cover - malformed escapes
            return
        if isinstance(value, str):
            self.strings.add(value)


# --------------------------------------------------------------------------
# replace_call (and rename/add/remove_argument)
# --------------------------------------------------------------------------


def _has_keyword(call: cst.Call, keyword: str) -> bool:
    return any(a.keyword is not None and a.keyword.value == keyword for a in call.args)


def _has_double_star(call: cst.Call) -> bool:
    return any(a.star == "**" for a in call.args)


class ReplaceCallMatcher(_Base):
    def __init__(self, op: ReplaceCall):
        super().__init__()
        self.op = op

    def _is_candidate(self, call: cst.Call) -> bool:
        if self.op.trigger_keyword is None:  # add_argument: calls lacking the keyword
            return not _has_keyword(call, self.op.argument_edits[0].keyword)
        return _has_keyword(call, self.op.trigger_keyword) or _has_double_star(call)

    def visit_Call(self, node: cst.Call) -> None:
        verdict = classify(self.qnames(node.func), self.op.target_call)
        if verdict == NO_MATCH or not self._is_candidate(node):
            return
        if verdict == AMBIGUOUS:
            self.record(node, ABSTAIN, f"callee binding is ambiguous: {_describe(self.qnames(node.func))}")
            return
        planned = plan_call_edits(node, self.op)
        if isinstance(planned, Unsafe):
            self.record(node, ABSTAIN, str(planned))
        elif planned.deep_equals(node):
            return  # every edit was a no-op at this site
        else:
            self.record(node, APPLY, f"call resolves to {self.op.target_call} via import; all edits apply")


# --------------------------------------------------------------------------
# abstain / change_import (declared or not-yet-implemented work: flag only)
# --------------------------------------------------------------------------


class AbstainMatcher(_Base):
    def __init__(self, op: Abstain):
        super().__init__()
        self.op = op

    def visit_Call(self, node: cst.Call) -> None:
        if classify(self.qnames(node.func), self.op.target_call) != MATCH:
            return
        kw = self.op.when_keyword_absent
        if kw is not None and _has_keyword(node, kw):
            return
        hidden = " (it may be inside **kwargs)" if kw and _has_double_star(node) else ""
        self.record(node, ABSTAIN, f"declared abstention: {self.op.reason}{hidden}")


class ChangeImportMatcher(_Base):
    def __init__(self, op: ChangeImport):
        super().__init__()
        self.op = op

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        if node.relative or node.module is None or isinstance(node.names, cst.ImportStar):
            return False
        if get_full_name_for_node(node.module) == self.op.old_module:
            for alias in node.names:
                if get_full_name_for_node(alias.name) == self.op.name:
                    self.record(alias, ABSTAIN, "change_import is valid in the schema but not implemented by engine 0.1")
        return False


def match_operation(wrapper: MetadataWrapper, op, facts: ImportFacts) -> list:
    if isinstance(op, RenameSymbol):
        visitor = RenameSymbolMatcher(op, facts, wrapper.module)
    elif isinstance(op, ReplaceCall):
        visitor = ReplaceCallMatcher(op)
    elif isinstance(op, Abstain):
        visitor = AbstainMatcher(op)
    elif isinstance(op, ChangeImport):
        visitor = ChangeImportMatcher(op)
    else:  # pragma: no cover
        raise AssertionError(f"unknown operation {op!r}")
    wrapper.visit(visitor)
    return visitor.decisions
