# PyJWT 1→2 bounded-task evidence packet — M0 pilot v0.2.0

**Status: real M0 artifact, not yet sent to any model.** This is the exact user-turn content of the PyJWT
rule-generation pilot (see [pilot_config.json](pilot_config.json)). The runner
[run_pyjwt_pilot.py](run_pyjwt_pilot.py) appends the canonical rule schema
([rule_schema.json](rule_schema.json)) after it. v0.2.0 (2026-09-24, protocol v0.5.0) changed only the
"Output format" section, to target the executable `molt.rule.v2` schema, and corrected "silently ignored" to
"ignored with a generic DeprecationWarning" after the 2026-09-23 probe re-run observed that warning. The
task scope, exemplar code and negative examples are unchanged. No model had read v0.1.0 either.

Everything between the two horizontal rules is the literal packet content.

---

## Task

Produce **one JSON migration rule bundle** for the following bounded, frozen task. Do not solve anything
outside this bounded scope, even if you recognize a broader PyJWT 1→2 migration.

### Dependency change

- Library: PyJWT
- Old version: 1.7.1
- New (target) version: 2.x (verified against 2.10.1)
- Source: PyJWT changelog, https://pyjwt.readthedocs.io/en/stable/changelog.html

### In-scope edit sites (exactly two)

1. **Exception rename.** The compatibility alias `jwt.ExpiredSignature` (and, by the same documented
   pattern, `jwt.InvalidAudience`, `jwt.InvalidIssuer`) was removed in 2.x. Code that references
   `jwt.ExpiredSignature` (e.g. in an `except` clause or a direct reference) must be rewritten to reference
   `jwt.ExpiredSignatureError` instead (`jwt.InvalidAudience` → `jwt.InvalidAudienceError`,
   `jwt.InvalidIssuer` → `jwt.InvalidIssuerError`).
2. **Options restructuring.** The flat keyword argument `verify_expiration=<bool>` passed directly to
   `jwt.decode(...)` was deprecated-with-warning in 1.x and is ignored in 2.x (no error and no effect;
   only a generic "unsupported kwargs" DeprecationWarning). Code passing `verify_expiration=<bool>` to `jwt.decode(...)` must be rewritten to pass
   `options={"verify_exp": <bool>}` instead, merging into any existing `options=` dict at that call site
   rather than overwriting it.

### Explicitly out of scope — do not touch

- The `algorithms=` argument requirement on `jwt.decode(...)`. Whether to add `algorithms=[...]` and which
  algorithm(s) to select is a security decision this task must not attempt to infer or add.
- `jwt.encode(...)`'s return-type change (`bytes` → `str`).
- Any other PyJWT 1→2 change not named above.

## Frozen development exemplar (real, probed 2026-09-05)

This is the one development before/after example authorized for this generation attempt. It was produced
by running both PyJWT versions in isolated virtualenvs and recording actual behavior — see
[feasibility_probes.json#pyjwt-1-to-2-bounded-task](feasibility_probes.json) and
[probe_logs.txt](probe_logs.txt) for the raw captured output. It is not sourced from any client repository
(none is admitted yet); see [protocol.md](protocol.md) for why this is the only real artifact available
before Phase 6 curation.

**Before (PyJWT 1.7.1 — passes):**

```python
import jwt

def decode_token(token, secret):
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], verify_expiration=False)
    except jwt.ExpiredSignature:
        return None
```

**After (PyJWT 2.x — the migration this task must produce a rule for):**

```python
import jwt

def decode_token(token, secret):
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], options={"verify_exp": False})
    except jwt.ExpiredSignatureError:
        return None
```

**Confirmed behavior** (see probe records): on 1.7.1 both the old exception name and the flat kwarg work;
on 2.10.1 the old exception name raises `AttributeError` at the `except` clause, and the flat kwarg is
ignored apart from a generic DeprecationWarning (no error — the expiration check still runs, so
`decode_token` starts raising `ExpiredSignatureError` instead of returning `None`).

## Negative / adversarial examples (do not edit these)

```python
# Unrelated .decode()/.encode() on non-PyJWT receivers -- must NOT be touched.
raw_bytes.decode("utf-8")
some_dict = json.loads(payload.decode())
compressed.encode()

# Already-migrated code -- applying the rule again must be a no-op.
jwt.decode(token, secret, algorithms=["HS256"], options={"verify_exp": False})
except jwt.ExpiredSignatureError:
    ...
```

## Output format

Respond with **only** one JSON object that validates against the Molt rule schema `molt.rule.v2`
(the full JSON Schema is appended after this packet). The envelope for this task is fixed:

```json
{
  "schema_version": "molt.rule.v2",
  "bundle_id": "pyjwt-1-to-2-bounded",
  "bundle_version": "0.1.0",
  "applies_to": {"library": "PyJWT", "import_module": "jwt",
                 "old_version_range": ">=1.5,<2.0", "new_version_range": ">=2.0,<3.0"},
  "operations": []
}
```

Fill `operations` using only the schema's primitives: `rename_symbol`, `change_import`, `rename_argument`,
`add_argument`, `remove_argument`, `replace_call` (with `argument_edits` of kind `move_keyword_into_dict`,
`rename_keyword`, `remove_keyword` or `add_keyword`) and `abstain`. Every operation needs a unique lowercase
`id`. Values are typed literals such as `{"type": "bool", "value": false}`, never code strings. Behaviour
must be expressed in typed fields; `description` and `reason` are ignored by the engine. If an in-scope
site cannot be expressed, or an out-of-scope site needs a human decision, use an `abstain` operation that
names the `target_call` and the reason instead of inventing a primitive or emitting executable code.

---

**Packet ends above this line.** Below is bookkeeping, not part of the sent content.

- Total packet character count and the resulting rough token estimate are computed and recorded, with
  their method disclosed as an approximation, in [pilot_estimate.json](pilot_estimate.json).
- The runner sends a fixed system prompt (`DEFAULT_SYSTEM_PROMPT` in
  [run_pyjwt_pilot.py](run_pyjwt_pilot.py)) plus this packet body followed by the rule schema; the exact
  prompt SHA-256 is recorded in every result file.
