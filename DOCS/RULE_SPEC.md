# Molt Rule Specification (V1 Canonical)

**Status: Frozen for M0.** This document formalizes the canonical representation of a Molt migration rule bundle for Milestone M0 and the subsequent V1 transformation engine. It resolves previous divergence between early exploratory roadmap sketches, console mock data, and the pilot evidence packet.

The machine-readable JSON Schema is located at [`experiments/rule_schema.json`](../experiments/rule_schema.json).

---

## 1. Design Principles

1. **Constrained & Deterministic:** Rules cannot contain arbitrary Python code, arbitrary AST visitors, executable lambdas, regexes, or shell commands.
2. **Discriminated Bounded Primitives:** Every operation is strictly typed and belongs to one of seven recognized primitive operations (`rename_symbol`, `change_import`, `rename_argument`, `add_argument`, `remove_argument`, `replace_call`, and `abstain`).
3. **Explicit Scope & Non-Goals:** Rules target a named library and version range. If an API break cannot be expressed with bounded primitives (e.g. security-sensitive algorithm selection), the rule must declare an `abstain` operation rather than attempting unbounded heuristic modification.

---

## 2. Rule Bundle Envelope

A migration rule bundle is serialized as a single JSON object with the following envelope:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `bundle_id` | `string` | Yes | Unique identifier for the migration rule bundle (e.g. `pyjwt-1-to-2-bounded`). |
| `bundle_version` | `string` | Yes | Version of this rule bundle definition (e.g. `0.1.0`). |
| `applies_to` | `object` | Yes | Declares target dependency: `{"library": str, "old_version_range": str, "new_version": str}`. |
| `operations` | `array` | Yes | Ordered sequence of bounded transformation operations. |
| `provenance` | `object` | No | Metadata regarding generation or authorship (`authored_by`, `generated_by`, `timestamp`). |

---

## 3. Supported Operation Primitives

### 3.1 `rename_symbol`
Renames an exported module attribute, function, or exception alias.
```json
{
  "op": "rename_symbol",
  "qualified_old_name": "jwt.ExpiredSignature",
  "qualified_new_name": "jwt.ExpiredSignatureError",
  "description": "Rename removed compatibility alias to standard exception name."
}
```

### 3.2 `change_import`
Rewrites import paths when a symbol or module is relocated.
```json
{
  "op": "change_import",
  "old_module": "pydantic",
  "new_module": "pydantic_settings",
  "old_name": "BaseSettings",
  "new_name": "BaseSettings"
}
```

### 3.3 `rename_argument`
Renames a keyword argument at a specific call site.
```json
{
  "op": "rename_argument",
  "target_call": "jwt.decode",
  "old_arg_name": "verify",
  "new_arg_name": "verify_signature"
}
```

### 3.4 `add_argument`
Inserts a required or default argument into a target call expression.
```json
{
  "op": "add_argument",
  "target_call": "sqlalchemy.select",
  "arg_name": "distinct",
  "default_value": "False"
}
```

### 3.5 `remove_argument`
Removes an obsolete or deprecated argument from a target call expression.
```json
{
  "op": "remove_argument",
  "target_call": "jwt.decode",
  "arg_name": "verify_expiration"
}
```

### 3.6 `replace_call`
Restructures a call site by capturing existing arguments and mapping them into a restructured call signature (e.g., merging flat keyword arguments into a dictionary argument).
```json
{
  "op": "replace_call",
  "target_qualified_call": "jwt.decode",
  "description": "Restructure flat verify_expiration kwarg into options={'verify_exp': <val>}",
  "captures": ["token", "key", "options"]
}
```

### 3.7 `abstain`
Explicitly declines to modify a site that exceeds bounded DSL capabilities or requires human policy decisions.
```json
{
  "op": "abstain",
  "target": "jwt.decode#algorithms",
  "reason": "Selection of permitted cryptographic verification algorithms is a security decision requiring caller-specific intent."
}
```

---

## 4. Alignment Across M0 Artifacts

This specification serves as the single source of truth for:
- The output target in [`experiments/pilot_evidence_packet.md`](../experiments/pilot_evidence_packet.md).
- The JSON Schema in [`experiments/rule_schema.json`](../experiments/rule_schema.json).
- The illustrative mock bundle in [`console/mock/rule_schema.json`](../console/mock/rule_schema.json).
- The Phase 1 engine implementation target (`src/molt/rules/schema.py`).
