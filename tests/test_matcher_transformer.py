"""Matching and transformation behaviour on concrete source snippets.

Each test states the exact expected output (or the absence of any edit).
"""

import json
import textwrap
from pathlib import Path

import pytest

from molt.engine import transform_source
from molt.schema import load_rule, parse_rule

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE_PATH = REPO_ROOT / "migrations" / "pyjwt-1-to-2" / "rule.json"
RULE = load_rule(RULE_PATH)


def run(src, rule=RULE):
    out, sites = transform_source(textwrap.dedent(src), rule)
    return out, sites


def changed(sites):
    return [s for s in sites if s.decision == "changed"]


def abstained(sites):
    return [s for s in sites if s.decision == "abstained"]


def custom_rule(*ops):
    data = json.loads(RULE_PATH.read_text())
    data["operations"] = list(ops)
    return parse_rule(data)


# ---------------------------------------------------------------------------
# The frozen M0 exemplar is reproduced exactly
# ---------------------------------------------------------------------------


def _exemplar_blocks():
    md = (REPO_ROOT / "experiments" / "pilot_evidence_packet.md").read_text(encoding="utf-8")

    def block(marker):
        start = md.index("```python", md.index(marker)) + len("```python\n")
        return md[start : md.index("```", start)]

    return block("**Before"), block("**After")


def test_engine_reproduces_frozen_development_exemplar_exactly():
    before, after = _exemplar_blocks()
    out, sites = transform_source(before, RULE)
    assert out == after
    assert [s.op_id for s in changed(sites)] == ["rename-expired-signature", "decode-verify-expiration-into-options"]
    assert abstained(sites) == []


# ---------------------------------------------------------------------------
# Binding-aware matching
# ---------------------------------------------------------------------------


def test_import_alias_is_followed():
    out, sites = run("""
        import jwt as pyjwt
        try:
            pyjwt.decode(t, k, algorithms=["HS256"], verify_expiration=False)
        except pyjwt.ExpiredSignature:
            pass
    """)
    assert "pyjwt.decode(t, k, algorithms=[\"HS256\"], options={\"verify_exp\": False})" in out
    assert "except pyjwt.ExpiredSignatureError:" in out
    assert len(changed(sites)) == 2


def test_from_import_of_function_is_followed():
    out, _ = run("""
        from jwt import decode
        decode(t, k, algorithms=["HS256"], verify_expiration=True)
    """)
    assert 'decode(t, k, algorithms=["HS256"], options={"verify_exp": True})' in out


def test_from_import_of_old_name_renames_binding_and_references():
    out, sites = run("""
        from jwt import ExpiredSignature, decode


        def f(t):
            try:
                return decode(t, "k", algorithms=["HS256"])
            except ExpiredSignature:
                return isinstance(ExpiredSignature, type)
    """)
    assert "from jwt import ExpiredSignatureError, decode" in out
    assert "except ExpiredSignatureError:" in out
    assert "isinstance(ExpiredSignatureError, type)" in out
    assert "ExpiredSignature," not in out and "ExpiredSignature:" not in out
    assert len(changed(sites)) == 1  # one logical site: the binding and its references


def test_aliased_from_import_keeps_local_alias():
    out, _ = run("from jwt import InvalidIssuer as Bad\nraise Bad()\n")
    assert out == "from jwt import InvalidIssuerError as Bad\nraise Bad()\n"


UNRELATED = """
    import json


    class Codec:
        def decode(self, data, verify_expiration=False):
            return data


    def check(raw, codec, ExpiredSignature):
        codec.decode(raw, verify_expiration=True)
        json.loads(raw.decode("utf-8"))
        return ExpiredSignature


    def shadowed(jwt):
        return jwt.decode(1, verify_expiration=False), jwt.ExpiredSignature
"""


def test_unrelated_lookalikes_and_shadowing_are_untouched():
    src = textwrap.dedent(UNRELATED)
    out, sites = transform_source("import jwt\n" + src, RULE)
    assert out == "import jwt\n" + src
    assert sites == []


def test_already_migrated_code_is_a_no_op():
    before, after = _exemplar_blocks()
    out, sites = transform_source(after, RULE)
    assert out == after and sites == []


def test_transformation_is_idempotent_and_deterministic():
    src = (REPO_ROOT / "tests" / "fixtures" / "pyjwt_repo" / "app" / "auth.py").read_text()
    first, _ = transform_source(src, RULE)
    again, _ = transform_source(src, RULE)
    second, sites = transform_source(first, RULE)
    assert first == again
    assert second == first and changed(sites) == []


# ---------------------------------------------------------------------------
# Formatting and comments
# ---------------------------------------------------------------------------


def test_multiline_merge_preserves_comments_and_layout():
    out, _ = run("""
        import jwt


        def f(token):
            return jwt.decode(
                token,
                "k",  # key comment
                algorithms=["HS256"],
                options={"verify_aud": False},  # audience is checked upstream
                verify_expiration=False,
            )
    """)
    assert out == textwrap.dedent("""
        import jwt


        def f(token):
            return jwt.decode(
                token,
                "k",  # key comment
                algorithms=["HS256"],
                options={"verify_aud": False, "verify_exp": False},  # audience is checked upstream
            )
    """)


def test_multiline_dict_with_trailing_comma_gets_new_line_entry():
    out, _ = run("""
        import jwt
        jwt.decode(
            t,
            k,
            verify_expiration=flag,
            options={
                'verify_aud': False,
            },
            algorithms=["HS256"],
        )
    """)
    assert out == textwrap.dedent("""
        import jwt
        jwt.decode(
            t,
            k,
            options={
                'verify_aud': False,
                'verify_exp': flag,
            },
            algorithms=["HS256"],
        )
    """)


def test_non_trivial_value_is_moved_in_place_when_no_dict_exists():
    out, sites = run('import jwt\njwt.decode(t, k, algorithms=["HS256"], verify_expiration=cfg.get("exp"))\n')
    assert 'options={"verify_exp": cfg.get("exp")}' in out
    assert len(changed(sites)) == 1


def test_unrelated_lines_and_comments_are_byte_identical():
    src = (REPO_ROOT / "tests" / "fixtures" / "pyjwt_repo" / "app" / "auth.py").read_text()
    out, _ = transform_source(src, RULE)
    before_lines, after_lines = src.splitlines(), out.splitlines()
    edited = {i for i, (a, b) in enumerate(zip(before_lines, after_lines)) if a != b}
    for i, line in enumerate(before_lines):
        if "#" in line and i not in edited:
            assert line in after_lines


# ---------------------------------------------------------------------------
# Conservative abstention
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("src, reason_fragment", [
    ('import jwt\njwt.decode(t, k, algorithms=["HS256"], verify_expiration=False, **extra)\n', "**kwargs"),
    ('import jwt\njwt.decode(t, k, algorithms=["HS256"], options=opts, verify_expiration=False)\n', "not a dict literal"),
    ('import jwt\njwt.decode(t, k, algorithms=["HS256"], options={"verify_exp": True}, verify_expiration=False)\n', "already sets"),
    ('import jwt\njwt.decode(t, k, algorithms=["HS256"], options={**base}, verify_expiration=False)\n', "unpacking"),
    ('import jwt\njwt.decode(t, k, algorithms=["HS256"], options={key: 1}, verify_expiration=False)\n', "non-literal key"),
    ('import jwt\njwt.decode(t, k, algorithms=["HS256"], options={}, verify_expiration=check())\n', "evaluation order"),
])
def test_unsafe_call_sites_abstain_without_editing(src, reason_fragment):
    out, sites = run(src)
    assert out == src
    reasons = [s.reason for s in abstained(sites) if s.op_id == "decode-verify-expiration-into-options"]
    assert reasons and reason_fragment in reasons[0]


def test_conditional_import_makes_binding_ambiguous():
    src = textwrap.dedent("""
        try:
            import jwt
        except ImportError:
            jwt = None
        jwt.decode(t, k, algorithms=["HS256"], verify_expiration=False)
    """)
    out, sites = run(src)
    assert out == src
    assert "ambiguous" in abstained(sites)[0].reason


def test_star_import_abstains_on_bare_old_name():
    src = "from jwt import *\ntry:\n    pass\nexcept ExpiredSignature:\n    pass\n"
    out, sites = run(src)
    assert out == src
    assert "import *" in abstained(sites)[0].reason


@pytest.mark.parametrize("src, fragment", [
    ("from jwt import ExpiredSignature\nExpiredSignatureError = 1\nraise ExpiredSignature\n", "already used"),
    ('from jwt import ExpiredSignature\n__all__ = ["ExpiredSignature"]\n', "string literal"),
    ("from jwt import ExpiredSignature\nExpiredSignature = ValueError\n", "bound 2 times"),
    ("import jwt\njwt.ExpiredSignature = ValueError\n", "assigned or deleted"),
])
def test_unsafe_renames_abstain(src, fragment):
    out, sites = run(src)
    assert out == src
    assert fragment in abstained(sites)[0].reason


def test_declared_abstention_flags_missing_algorithms():
    src = "import jwt\njwt.decode(token, key)\njwt.decode(token, key, algorithms=['HS256'])\n"
    out, sites = run(src)
    assert out == src
    flagged = abstained(sites)
    assert [(s.op_id, s.line) for s in flagged] == [("decode-missing-algorithms", 2)]
    assert "security decision" in flagged[0].reason


def test_nested_target_calls_are_both_transformed():
    out, _ = run('import jwt\njwt.decode(jwt.decode(a, b, algorithms=["x"], verify_expiration=x), c, '
                 'algorithms=["x"], verify_expiration=y)\n')
    assert out == ('import jwt\njwt.decode(jwt.decode(a, b, algorithms=["x"], options={"verify_exp": x}), c, '
                   'algorithms=["x"], options={"verify_exp": y})\n')


# ---------------------------------------------------------------------------
# Single-edit primitives and typed values
# ---------------------------------------------------------------------------


def test_rename_remove_add_argument_primitives():
    rule = custom_rule(
        {"op": "rename_argument", "id": "ren", "target_call": "jwt.decode", "old_arg_name": "verify", "new_arg_name": "verify_signature"},
        {"op": "remove_argument", "id": "rem", "target_call": "jwt.decode", "arg_name": "leeway"},
        {"op": "add_argument", "id": "add", "target_call": "jwt.encode", "arg_name": "algorithm", "value": {"type": "str", "value": "HS256"}},
    )
    out, sites = transform_source(
        "import jwt\njwt.decode(t, k, verify=False, leeway=10)\njwt.encode(p, k)\njwt.encode(p, k, algorithm='RS256')\n", rule)
    assert out == ('import jwt\njwt.decode(t, k, verify_signature=False)\njwt.encode(p, k, algorithm="HS256")\n'
                   "jwt.encode(p, k, algorithm='RS256')\n")
    assert [s.op_id for s in changed(sites)] == ["ren", "rem", "add"]


def test_remove_argument_with_side_effects_abstains():
    rule = custom_rule({"op": "remove_argument", "id": "rem", "target_call": "jwt.decode", "arg_name": "leeway"})
    src = "import jwt\njwt.decode(t, k, leeway=compute())\n"
    out, sites = transform_source(src, rule)
    assert out == src and "side effects" in abstained(sites)[0].reason


def test_rename_argument_collision_abstains():
    rule = custom_rule({"op": "rename_argument", "id": "ren", "target_call": "jwt.decode", "old_arg_name": "a", "new_arg_name": "b"})
    src = "import jwt\njwt.decode(t, a=1, b=2)\n"
    out, sites = transform_source(src, rule)
    assert out == src and "duplicate" in abstained(sites)[0].reason


@pytest.mark.parametrize("value, rendered", [
    ({"type": "bool", "value": False}, "x=False"),
    ({"type": "int", "value": -3}, "x=-3"),
    ({"type": "str", "value": 'a"b'}, 'x="a\\"b"'),
    ({"type": "none"}, "x=None"),
])
def test_typed_values_render_as_literals(value, rendered):
    rule = custom_rule({"op": "add_argument", "id": "add", "target_call": "jwt.encode", "arg_name": "x", "value": value})
    out, _ = transform_source("import jwt\njwt.encode(p)\n", rule)
    assert out == f"import jwt\njwt.encode(p, {rendered})\n"


def test_change_import_is_flagged_not_silently_ignored():
    data = json.loads(RULE_PATH.read_text())
    data["applies_to"].pop("import_module")
    data["operations"] = [{"op": "change_import", "id": "ci", "old_module": "pydantic", "new_module": "pydantic_settings", "name": "BaseSettings"}]
    src = "from pydantic import BaseSettings\n"
    out, sites = transform_source(src, parse_rule(data))
    assert out == src and "not implemented" in abstained(sites)[0].reason
