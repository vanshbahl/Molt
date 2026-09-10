# PyJWT 1→2 bounded-task evidence packet — M0 pilot v0.1.0

**Status: real M0 artifact, ready to send, not yet sent.** This is the exact evidence packet that would be
placed in the user turn of the priced pilot's rule-generation request (see
[pilot_config.json](pilot_config.json)). It exists to (a) make the pilot's token/cost estimate
in [pilot_estimate.json](pilot_estimate.json) a measurement of a real artifact rather than a guess, and
(b) be usable unmodified the moment a billable API key is authorized. No model has read this packet yet.
Writing it required zero paid calls; it is data assembly, not an implementation of `inference/evidence.py`
(Phase 3), which does not exist.

Everything below the horizontal rule is the literal packet content.

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
   `jwt.decode(...)` was deprecated-with-warning in 1.x and is silently ignored (no error, no effect) in
   2.x. Code passing `verify_expiration=<bool>` to `jwt.decode(...)` must be rewritten to pass
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
silently ignored (no error — the expiration check still runs, so `decode_token` starts raising
`ExpiredSignatureError` instead of returning `None`).

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

Respond with **only** a JSON object shaped like this (informal pilot schema — this is NOT the frozen
Phase 1 `rules/schema.py` output, which does not exist yet; it is a minimal shape sufficient to judge
schema-plausibility and expressibility for this pilot only):

```json
{
  "bundle_id": "pyjwt-1-to-2-bounded",
  "bundle_version": "0.1.0",
  "applies_to": {"library": "pyjwt", "old_version_range": "<2.0", "new_version": ">=2.0"},
  "operations": [
    {
      "op": "rename_symbol",
      "qualified_old_name": "jwt.ExpiredSignature",
      "qualified_new_name": "jwt.ExpiredSignatureError"
    },
    {
      "op": "replace_call",
      "target_qualified_call": "jwt.decode",
      "description": "..."
    }
  ]
}
```

Use only these primitive `op` names: `rename_symbol`, `change_import`, `rename_argument`, `add_argument`,
`remove_argument`, `replace_call`. If a site cannot be safely expressed with these primitives, include an
`"abstain"` entry naming the site and the reason instead of inventing a new primitive or emitting
executable code.

---

**Packet ends above this line.** Below is bookkeeping, not part of the sent content.

- Total packet character count and the resulting rough token estimate are computed and recorded, with
  their method disclosed as an approximation, in [pilot_estimate.json](pilot_estimate.json).
- A system prompt (not shown here — see `pilot_config.json.system_prompt`) will accompany this user-turn
  content in the real request.
