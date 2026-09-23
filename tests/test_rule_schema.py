"""Rule schema: valid rules are accepted and typed; prohibited rules are rejected."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from molt.models import ReplaceCall, RenameSymbol, TypedValue
from molt.schema import RuleValidationError, canonical_json, load_rule, parse_rule, rule_sha256, validate_rule

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE_PATH = REPO_ROOT / "migrations" / "pyjwt-1-to-2" / "rule.json"


def reference():
    return json.loads(RULE_PATH.read_text(encoding="utf-8"))


def test_packaged_schema_is_identical_to_registered_schema():
    registered = (REPO_ROOT / "experiments" / "rule_schema.json").read_bytes()
    packaged = (REPO_ROOT / "src" / "molt" / "rule_schema.json").read_bytes()
    assert packaged == registered, "src/molt/rule_schema.json drifted from experiments/rule_schema.json"


def test_schema_is_a_valid_draft_2020_12_schema():
    Draft202012Validator.check_schema(json.loads((REPO_ROOT / "experiments" / "rule_schema.json").read_text()))


def test_reference_rule_is_valid_and_typed():
    rule = load_rule(RULE_PATH)
    assert rule.bundle_id == "pyjwt-1-to-2-bounded"
    assert [op.op for op in rule.operations] == ["rename_symbol"] * 3 + ["replace_call", "abstain"]
    move = rule.operations[3]
    assert isinstance(move, ReplaceCall)
    edit = move.argument_edits[0]
    assert (edit.kind, edit.keyword, edit.dict_keyword, edit.dict_key) == (
        "move_keyword_into_dict", "verify_expiration", "options", "verify_exp")
    assert rule.modules() == {"jwt"}


def test_canonical_hash_ignores_key_order_and_whitespace():
    data = reference()
    reordered = json.loads(json.dumps(data, sort_keys=True, indent=7))
    assert rule_sha256(data) == rule_sha256(reordered)
    assert canonical_json(data) == canonical_json(reordered)


def test_single_edit_primitives_normalise_to_replace_call():
    data = reference()
    data["operations"] = [
        {"op": "rename_argument", "id": "a", "target_call": "jwt.decode", "old_arg_name": "verify", "new_arg_name": "verify_signature"},
        {"op": "remove_argument", "id": "b", "target_call": "jwt.decode", "arg_name": "verify_iat"},
        {"op": "add_argument", "id": "c", "target_call": "jwt.encode", "arg_name": "algorithm", "value": {"type": "str", "value": "HS256"}},
    ]
    ops = parse_rule(data).operations
    assert [(o.op, o.trigger_keyword, o.argument_edits[0].kind) for o in ops] == [
        ("rename_argument", "verify", "rename_keyword"),
        ("remove_argument", "verify_iat", "remove_keyword"),
        ("add_argument", None, "add_keyword"),
    ]
    assert ops[2].argument_edits[0].value == TypedValue("str", "HS256")


def mutate(fn):
    data = reference()
    fn(data)
    return data


INVALID = {
    "unknown_top_level_field": lambda d: d.update(extra=1),
    "missing_schema_version": lambda d: d.pop("schema_version"),
    "wrong_schema_version": lambda d: d.update(schema_version="molt.rule.v1"),
    "unknown_operation": lambda d: d["operations"].append({"op": "run_script", "id": "x", "script": "rm -rf /"}),
    "unknown_operation_field": lambda d: d["operations"][0].update(visitor="class V(cst.CSTTransformer): ..."),
    "missing_operation_id": lambda d: d["operations"][0].pop("id"),
    "raw_code_default_value": lambda d: d["operations"].append(
        {"op": "add_argument", "id": "x", "target_call": "jwt.decode", "arg_name": "leeway", "default_value": "__import__('os')"}),
    "raw_code_typed_value": lambda d: d["operations"].append(
        {"op": "add_argument", "id": "x", "target_call": "jwt.decode", "arg_name": "leeway", "value": {"type": "code", "value": "f()"}}),
    "mistyped_typed_value": lambda d: d["operations"].append(
        {"op": "add_argument", "id": "x", "target_call": "jwt.decode", "arg_name": "leeway", "value": {"type": "int", "value": "10"}}),
    "free_text_replace_call": lambda d: d["operations"].__setitem__(3, {
        "op": "replace_call", "id": "x", "target_qualified_call": "jwt.decode",
        "description": "Restructure verify_expiration into options", "captures": ["token", "key"]}),
    "replace_call_without_edits": lambda d: d["operations"][3].update(argument_edits=[]),
    "code_in_qualified_name": lambda d: d["operations"][0].update(qualified_old_name="jwt.x(__import__('os'))"),
    "single_component_qualified_name": lambda d: d["operations"][3].update(target_call="decode"),
    "path_specific_target": lambda d: d["operations"][3].update(target_call="app/auth.py:jwt.decode"),
    "empty_abstain_reason": lambda d: d["operations"][4].update(reason=""),
    "too_many_operations": lambda d: d.update(operations=[
        {"op": "abstain", "id": f"a{i}", "target_call": "jwt.decode", "reason": "r"} for i in range(33)]),
    "bad_version_range": lambda d: d["applies_to"].update(old_version_range="any old version"),
    # semantic layer
    "duplicate_ids": lambda d: d["operations"][1].update(id=d["operations"][0]["id"]),
    "rename_moves_module": lambda d: d["operations"][0].update(qualified_new_name="jwt.exceptions.ExpiredSignatureError"),
    "rename_to_itself": lambda d: d["operations"][0].update(qualified_new_name="jwt.ExpiredSignature"),
    "rename_chain": lambda d: d["operations"].append(
        {"op": "rename_symbol", "id": "chain", "qualified_old_name": "jwt.ExpiredSignatureError", "qualified_new_name": "jwt.Expired"}),
    "duplicate_rename": lambda d: d["operations"].append(dict(d["operations"][0], id="again")),
    "trigger_not_edited": lambda d: d["operations"][3].update(trigger_keyword="leeway"),
    "edit_touches_keyword_twice": lambda d: d["operations"][3]["argument_edits"].append(
        {"kind": "remove_keyword", "keyword": "verify_expiration"}),
    "conflicting_call_operations": lambda d: d["operations"].append(dict(d["operations"][3], id="dup-call")),
    "identical_version_ranges": lambda d: d["applies_to"].update(new_version_range=d["applies_to"]["old_version_range"]),
    "overlapping_version_ranges": lambda d: d["applies_to"].update(new_version_range=">=1.7,<3.0"),
    "outside_import_module": lambda d: d["operations"][0].update(
        qualified_old_name="os.ExpiredSignature", qualified_new_name="os.ExpiredSignatureError"),
}


@pytest.mark.parametrize("name", sorted(INVALID))
def test_prohibited_rules_are_rejected_before_execution(name):
    data = mutate(INVALID[name])
    issues = validate_rule(data)
    assert issues, f"{name} should be rejected"
    with pytest.raises(RuleValidationError):
        parse_rule(data)


def test_old_v1_free_text_bundle_is_rejected():
    legacy = {
        "bundle_id": "pyjwt-1-to-2-bounded", "bundle_version": "0.1.0",
        "applies_to": {"library": "pyjwt", "old_version_range": "<2.0", "new_version": ">=2.0"},
        "operations": [{"op": "replace_call", "target_qualified_call": "jwt.decode", "description": "..."}],
    }
    assert validate_rule(legacy)


def test_errors_name_the_offending_field():
    data = mutate(lambda d: d["operations"][3]["argument_edits"][0].update(dict_key="verify exp"))
    issues = validate_rule(data)
    assert any(i.path == "$.operations[3].argument_edits[0].dict_key" for i in issues), issues


def test_non_object_rule_rejected():
    assert validate_rule([1, 2]) and validate_rule("rule")


def test_invalid_json_file_rejected(tmp_path):
    bad = tmp_path / "rule.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(RuleValidationError):
        load_rule(bad)


def test_every_rule_json_in_repo_validates():
    """Every committed rule bundle must agree with the schema."""
    paths = sorted((REPO_ROOT / "migrations").glob("*/rule*.json"))
    assert RULE_PATH in paths
    for path in paths:
        assert validate_rule(json.loads(path.read_text(encoding="utf-8"))) == [], path


def test_rename_symbol_parts():
    rename = load_rule(RULE_PATH).operations[0]
    assert isinstance(rename, RenameSymbol)
    assert (rename.module, rename.old_attr, rename.new_attr) == ("jwt", "ExpiredSignature", "ExpiredSignatureError")


def test_typed_value_variants_accepted():
    for value in ({"type": "bool", "value": True}, {"type": "int", "value": -3},
                  {"type": "str", "value": "HS256"}, {"type": "none"}):
        data = copy.deepcopy(reference())
        data["operations"].append({"op": "add_argument", "id": "v", "target_call": "jwt.encode", "arg_name": "x", "value": value})
        assert validate_rule(data) == [], value
