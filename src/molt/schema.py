"""Rule validation: JSON Schema (structural) + semantic checks, then typing.

Validation is two-layered and both layers must pass before the engine sees a
rule:

1. ``structural_errors``: the canonical JSON Schema
   (``experiments/rule_schema.json``, shipped as ``molt/rule_schema.json``).
2. ``semantic_errors``: cross-field rules JSON Schema cannot express
   (DOCS/RULE_SPEC.md section 5).

``load_rule`` returns a typed :class:`~molt.models.RuleBundle` or raises
:class:`RuleValidationError` carrying every issue found.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Union

from jsonschema import Draft202012Validator

from .models import (
    Abstain,
    ArgumentEdit,
    ChangeImport,
    RenameSymbol,
    ReplaceCall,
    RuleBundle,
    TypedValue,
)


@dataclass(frozen=True)
class Issue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class RuleValidationError(ValueError):
    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__("; ".join(str(i) for i in self.issues))


def load_schema() -> dict:
    text = resources.files("molt").joinpath("rule_schema.json").read_text(encoding="utf-8")
    return json.loads(text)


_VALIDATOR = None


def _validator() -> Draft202012Validator:
    global _VALIDATOR
    if _VALIDATOR is None:
        schema = load_schema()
        Draft202012Validator.check_schema(schema)
        _VALIDATOR = Draft202012Validator(schema)
    return _VALIDATOR


def _path(parts) -> str:
    out = "$"
    for p in parts:
        out += f"[{p}]" if isinstance(p, int) else f".{p}"
    return out


def _leaf_errors(err) -> list:
    """Reduce a oneOf failure to the errors of the branch its discriminator selected."""
    if not err.context:
        return [err]
    branches = {}
    for sub in err.context:
        branches.setdefault(sub.relative_schema_path[0], []).append(sub)
    selected = [errs for errs in branches.values() if not any(e.validator == "const" for e in errs)]
    if len(selected) == 1:
        out = []
        for sub in selected[0]:
            out.extend(_leaf_errors(sub))
        return out
    return [err]


def structural_errors(data) -> list:
    issues = []
    for err in _validator().iter_errors(data):
        for leaf in _leaf_errors(err):
            message = leaf.message
            if leaf.validator == "oneOf":
                message = "does not match any allowed variant (check 'kind'/'type' and its fields)"
            issues.append(Issue(_path(leaf.absolute_path), message))
    return sorted(set(issues), key=lambda i: (i.path, i.message))


# --------------------------------------------------------------------------
# Semantic layer
# --------------------------------------------------------------------------

_BOUND = re.compile(r"(<=|>=|<|>|==)\s*([0-9]+(?:\.[0-9]+)*)")


def _version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in v.split("."))


def _bounds(spec: str):
    lower = upper = None
    for opr, ver in _BOUND.findall(spec):
        v = _version_tuple(ver)
        if opr in (">=", ">", "=="):
            lower = v if lower is None else max(lower, v)
        if opr in ("<", "<=", "=="):
            upper = v if upper is None else min(upper, v)
    return lower, upper


def _edit_keywords(edit: dict) -> list:
    """Keywords an edit reads or writes."""
    kws = [edit["keyword"]]
    if edit["kind"] == "move_keyword_into_dict":
        kws.append(edit["dict_keyword"])
    if edit["kind"] == "rename_keyword":
        kws.append(edit["new_keyword"])
    return kws


def semantic_errors(data: dict) -> list:
    issues = []
    applies = data["applies_to"]
    ops = data["operations"]

    if applies["old_version_range"].replace(" ", "") == applies["new_version_range"].replace(" ", ""):
        issues.append(Issue("$.applies_to", "old and new version ranges are identical"))
    old_lo, old_hi = _bounds(applies["old_version_range"])
    new_lo, _ = _bounds(applies["new_version_range"])
    if old_hi is not None and new_lo is not None and new_lo < old_hi:
        issues.append(Issue("$.applies_to", "new_version_range overlaps old_version_range"))

    seen_ids = set()
    renamed_from = {}
    call_triggers = {}
    import_module = applies.get("import_module")

    for i, op in enumerate(ops):
        p = f"$.operations[{i}]"
        if op["id"] in seen_ids:
            issues.append(Issue(p + ".id", f"duplicate operation id {op['id']!r}"))
        seen_ids.add(op["id"])
        kind = op["op"]

        names = [op[k] for k in ("qualified_old_name", "qualified_new_name", "target_call") if k in op]
        if import_module:
            for n in names:
                if n.split(".")[0] != import_module:
                    issues.append(Issue(p, f"{n!r} is outside applies_to.import_module {import_module!r}"))

        if kind == "rename_symbol":
            old, new = op["qualified_old_name"], op["qualified_new_name"]
            if old == new:
                issues.append(Issue(p, "qualified_old_name equals qualified_new_name"))
            if old.rsplit(".", 1)[0] != new.rsplit(".", 1)[0]:
                issues.append(Issue(p, "rename_symbol may only rename the final component; use change_import to move modules"))
            if old in renamed_from:
                issues.append(Issue(p, f"{old!r} is already renamed by operation {renamed_from[old]!r}"))
            renamed_from[old] = op["id"]

        elif kind == "change_import":
            if (op["old_module"], op["name"]) == (op["new_module"], op.get("new_name", op["name"])):
                issues.append(Issue(p, "change_import does not change anything"))

        elif kind == "rename_argument":
            if op["old_arg_name"] == op["new_arg_name"]:
                issues.append(Issue(p, "old_arg_name equals new_arg_name"))

        elif kind == "replace_call":
            touched = []
            sources = []
            for j, edit in enumerate(op["argument_edits"]):
                ep = f"{p}.argument_edits[{j}]"
                kws = _edit_keywords(edit)
                if len(set(kws)) != len(kws):
                    issues.append(Issue(ep, "edit reads and writes the same keyword"))
                for kw in kws:
                    if kw in touched:
                        issues.append(Issue(ep, f"keyword {kw!r} is touched by more than one edit"))
                touched.extend(kws)
                if edit["kind"] == "add_keyword":
                    if edit["keyword"] == op["trigger_keyword"]:
                        issues.append(Issue(ep, "add_keyword cannot add the trigger keyword (the trigger must already be present)"))
                else:
                    sources.append(edit["keyword"])
            if op["trigger_keyword"] not in sources:
                issues.append(Issue(p, "trigger_keyword must be the keyword of a move/rename/remove edit"))

        if kind in ("replace_call", "rename_argument", "remove_argument"):
            trigger = op.get("trigger_keyword") or op.get("old_arg_name") or op.get("arg_name")
            key = (op["target_call"], trigger)
            if key in call_triggers:
                issues.append(Issue(p, f"conflicts with operation {call_triggers[key]!r} (same call and trigger keyword)"))
            call_triggers[key] = op["id"]

    for old, op_id in renamed_from.items():
        for op in ops:
            if op["op"] == "rename_symbol" and op["qualified_new_name"] == old:
                issues.append(Issue("$.operations", f"rename chain through {old!r} is order-dependent"))
    return issues


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def rule_sha256(data: dict) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def validate_rule(data) -> list:
    """Return every issue (structural first; semantic only if structure is valid)."""
    if not isinstance(data, dict):
        return [Issue("$", "rule must be a JSON object")]
    issues = structural_errors(data)
    if issues:
        return issues
    return semantic_errors(data)


def _typed_value(raw):
    return None if raw is None else TypedValue(type=raw["type"], value=raw.get("value"))


def _edit(raw: dict) -> ArgumentEdit:
    return ArgumentEdit(
        kind=raw["kind"],
        keyword=raw["keyword"],
        dict_keyword=raw.get("dict_keyword"),
        dict_key=raw.get("dict_key"),
        when_dict_exists=raw.get("when_dict_exists", "merge"),
        new_keyword=raw.get("new_keyword"),
        value=_typed_value(raw.get("value")),
    )


def _operation(raw: dict):
    kind = raw["op"]
    if kind == "rename_symbol":
        return RenameSymbol(raw["id"], raw["qualified_old_name"], raw["qualified_new_name"])
    if kind == "change_import":
        return ChangeImport(raw["id"], raw["old_module"], raw["new_module"], raw["name"], raw.get("new_name"))
    if kind == "replace_call":
        edits = tuple(_edit(e) for e in raw["argument_edits"])
        return ReplaceCall(raw["id"], raw["target_call"], raw["trigger_keyword"], edits)
    if kind == "rename_argument":
        edit = ArgumentEdit(kind="rename_keyword", keyword=raw["old_arg_name"], new_keyword=raw["new_arg_name"])
        return ReplaceCall(raw["id"], raw["target_call"], raw["old_arg_name"], (edit,), op=kind)
    if kind == "remove_argument":
        edit = ArgumentEdit(kind="remove_keyword", keyword=raw["arg_name"])
        return ReplaceCall(raw["id"], raw["target_call"], raw["arg_name"], (edit,), op=kind)
    if kind == "add_argument":
        edit = ArgumentEdit(kind="add_keyword", keyword=raw["arg_name"], value=_typed_value(raw["value"]))
        return ReplaceCall(raw["id"], raw["target_call"], None, (edit,), op=kind)
    if kind == "abstain":
        return Abstain(raw["id"], raw["target_call"], raw["reason"], raw.get("when_keyword_absent"))
    raise AssertionError(f"unreachable: schema admitted unknown op {kind!r}")


def parse_rule(data) -> RuleBundle:
    issues = validate_rule(data)
    if issues:
        raise RuleValidationError(issues)
    applies = data["applies_to"]
    return RuleBundle(
        bundle_id=data["bundle_id"],
        bundle_version=data["bundle_version"],
        library=applies["library"],
        import_module=applies.get("import_module"),
        old_version_range=applies["old_version_range"],
        new_version_range=applies["new_version_range"],
        operations=tuple(_operation(o) for o in data["operations"]),
        sha256=rule_sha256(data),
    )


def load_rule(source: Union[str, Path, dict]) -> RuleBundle:
    if isinstance(source, dict):
        return parse_rule(source)
    try:
        data = json.loads(Path(source).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuleValidationError([Issue("$", f"invalid JSON: {exc}")]) from exc
    return parse_rule(data)


