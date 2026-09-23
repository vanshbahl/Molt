# Molt Rule Specification — `molt.rule.v2`

**Status:** registered in [experiments/protocol.md](../experiments/protocol.md) v0.5.0 (2026-09-24). Supersedes the v1 draft of 2026-09-10, whose `replace_call` carried its behaviour in a free-text `description` and whose `default_value` accepted raw code strings; neither could be executed deterministically.

Three artifacts define the rule language and must agree. Tests enforce the agreement:

| Artifact | Role |
| --- | --- |
| This document | Semantics: what each field means and when the engine edits or abstains. |
| [`experiments/rule_schema.json`](../experiments/rule_schema.json) | Structural layer (JSON Schema draft 2020-12). Byte-identical copy shipped as `src/molt/rule_schema.json` (`tests/test_rule_schema.py`). |
| [`src/molt/schema.py`](../src/molt/schema.py) | Structural + semantic validation (§5), then conversion to typed dataclasses (`src/molt/models.py`). |

The reference bundle is [`migrations/pyjwt-1-to-2/rule.json`](../migrations/pyjwt-1-to-2/rule.json). It is hand-written, not LLM output.

## 1. Principles

1. **Data, not code.** A rule contains identifiers, qualified names, enumerated edit kinds, and typed literals. It never contains Python source, regexes, predicates, visitors, shell commands, or file paths.
2. **Nothing executable hides in prose.** `description` and `reason` are documentation. The engine never reads them. Every behaviour is a typed field.
3. **Narrow on purpose.** v2 covers what the PyJWT anchor needs, plus the single-keyword primitives the roadmap names. Anything else is *unsupported*: it is reported, never approximated. The grammar is not grown to make a migration fit (roadmap Phase 0 decisions).
4. **Conservative by construction.** An edit is authorised only by binding evidence: the expression must resolve to the rule's qualified name through an import, and to nothing else. When that evidence is missing, the engine abstains and records why.
5. **LibCST-shaped.** Every field maps onto a LibCST concept: `QualifiedNameProvider` names, `cst.Arg` keywords, `cst.Dict` elements, and literal nodes.

## 2. Envelope

```json
{
  "schema_version": "molt.rule.v2",
  "bundle_id": "pyjwt-1-to-2-bounded",
  "bundle_version": "0.1.0",
  "applies_to": {"library": "PyJWT", "import_module": "jwt",
                 "old_version_range": ">=1.5,<2.0", "new_version_range": ">=2.0,<3.0"},
  "operations": [ ... 1–32 operations, applied in order ... ],
  "provenance": {"authored_by": "...", "generated_by": "...", "timestamp": "...", "source": "..."}
}
```

- `schema_version` is required and must be exactly `molt.rule.v2`.
- `bundle_id` is a lowercase slug. `bundle_version` is `MAJOR.MINOR.PATCH`.
- `applies_to` documents the dependency change; the engine installs nothing. The version ranges are PEP 440-style specifier sets. `import_module` is optional: when set, every qualified name in the bundle must live under it.
- `provenance` is optional and closed. Unknown fields are rejected everywhere.
- The canonical hash is SHA-256 of `json.dumps(rule, sort_keys=True, separators=(",", ":"))`, reported as `rule.sha256` in engine results.

## 3. Operations

Every operation has a required `op` and a required `id`, a slug unique within the bundle. Qualified names are dotted import paths with at least two components (`jwt.decode`).

### 3.1 `rename_symbol`

```json
{"op": "rename_symbol", "id": "rename-expired-signature",
 "qualified_old_name": "jwt.ExpiredSignature", "qualified_new_name": "jwt.ExpiredSignatureError"}
```

This op renames only the final component. Moving a symbol to another module is `change_import`.

| Site | Behaviour |
| --- | --- |
| `jwt.ExpiredSignature` (any import alias of `jwt`), read | Rename the attribute. |
| `from jwt import ExpiredSignature as E` | Rename the imported name and keep the local alias. |
| `from jwt import ExpiredSignature` | Rename the import and every reference to that binding, found with `ScopeProvider`. |
| Binding ambiguous (for example a conditional import plus a local assignment) | Abstain. |
| Attribute assigned or deleted (`jwt.ExpiredSignature = X`) | Abstain. |
| Bare-name rename where the new name is already used in the module, the binding has more than one assignment, or a string literal equals the old name (`__all__`, `getattr`) | Abstain. |
| `from jwt import *`, then a bare `ExpiredSignature` | Abstain; the binding cannot be resolved. |
| Local variable or parameter named `jwt`, or an unrelated library | Not a candidate; left untouched. |

### 3.2 `replace_call` — structured call restructuring

```json
{"op": "replace_call", "id": "decode-verify-expiration-into-options",
 "target_call": "jwt.decode",
 "trigger_keyword": "verify_expiration",
 "argument_edits": [
   {"kind": "move_keyword_into_dict", "keyword": "verify_expiration",
    "dict_keyword": "options", "dict_key": "verify_exp", "when_dict_exists": "merge"}
 ]}
```

- **Candidates** are calls whose callee resolves to `target_call` and that pass `trigger_keyword=` (or pass `**kwargs`, which may hide the keyword).
- **`argument_edits`** (1–8) apply **atomically** at each candidate site. If any edit is unsafe, the whole site abstains and nothing changes. An edit whose keyword is absent is a no-op at that site.
- The callee is never changed. Positional arguments are never touched.

| Edit `kind` | Fields | Effect | Abstains when |
| --- | --- | --- | --- |
| `move_keyword_into_dict` | `keyword`, `dict_keyword`, `dict_key`, `when_dict_exists` (`merge` default, or `abstain`) | No `dict_keyword=` present: replace `keyword=v` in place with `dict_keyword={"dict_key": v}`. Present: remove `keyword=v` and append `"dict_key": v` to the existing dict literal. | `dict_keyword=` is not a dict literal; it contains `**` unpacking or a non-literal key; it already sets `dict_key`; merging would move a value that is not side-effect free; `when_dict_exists` is `abstain`. |
| `rename_keyword` | `keyword`, `new_keyword` | `keyword=v` → `new_keyword=v` | `new_keyword=` already passed. |
| `remove_keyword` | `keyword` | Drop `keyword=v`. | `v` is not side-effect free. |
| `add_keyword` | `keyword`, `value` (typed) | Append `keyword=<literal>` if absent. | Never, beyond the `**kwargs` rule below. |

At every candidate site, a call with `**kwargs` abstains.

"Side-effect free" is deliberately narrow: literals, bare names, and `not`/`-`/`+` of those. Attribute access is excluded because properties can run code.

**Formatting.** Only the touched arguments and dict elements change. Comments, argument layout, trailing commas, and closing-bracket indentation are preserved. The key uses the existing dict's quote style, or `"` when a new dict is created. Dropping a comment attached to the *removed* keyword argument is a known limitation.

### 3.3 Single-keyword primitives

These are shorthand for a one-edit `replace_call` and behave identically:

| Op | Fields | Equivalent |
| --- | --- | --- |
| `rename_argument` | `target_call`, `old_arg_name`, `new_arg_name` | trigger `old_arg_name`, `rename_keyword` |
| `remove_argument` | `target_call`, `arg_name` | trigger `arg_name`, `remove_keyword` |
| `add_argument` | `target_call`, `arg_name`, `value` | every call lacking `arg_name`, `add_keyword` |

### 3.4 Typed values

`value` fields accept only these literal shapes; raw code strings are rejected:

```json
{"type": "bool", "value": false}    {"type": "int", "value": -3}
{"type": "str",  "value": "HS256"}  {"type": "none"}
```

They render as `False`, `-3`, `"HS256"`, and `None`. Integers are bounded to ±10⁹; strings are at most 200 characters, emitted with escaping.

### 3.5 `abstain` — declared human-decision sites

```json
{"op": "abstain", "id": "decode-missing-algorithms", "target_call": "jwt.decode",
 "when_keyword_absent": "algorithms",
 "reason": "Choosing permitted algorithms is a security decision the rule must not infer."}
```

The engine flags every call to `target_call`, or only calls lacking `when_keyword_absent`, as an abstained site carrying `reason`. It never edits them. A flagged site in a repository makes the engine result non-PASS: it is a required site that still needs a human.

### 3.6 `change_import`

```json
{"op": "change_import", "id": "basesettings-moved", "old_module": "pydantic",
 "new_module": "pydantic_settings", "name": "BaseSettings"}
```

The schema accepts it; **engine 0.1 does not implement it**. Matching `from old_module import name` sites are reported as abstentions ("not implemented"), so they can never silently pass. It is needed for the Pydantic pilot and deferred with it.

## 4. Matching semantics (engine)

- Only `QualifiedNameProvider` results decide identity. A site **matches** when its qualified-name set is exactly one name, equal to the target, with source `IMPORT`.
- The target appearing alongside other names, or with a non-import source, is **ambiguous**, and the site abstains.
- A target that never appears is **not a candidate**.
- Operations run in bundle order. Each runs on the output of the previous one with freshly computed metadata, so no operation matches against stale names.
- Only files that import a module named by the rule are analysed. Test files, vendored directories, and symlinks are skipped by default (see `src/molt/parser.py`).
- Application is idempotent. Re-running on migrated output yields zero candidate sites (`tests/test_matcher_transformer.py`).

## 5. Validation rules

A rule must pass both layers before the engine sees it. Failures are reported per field as `Issue(path, message)`, and the engine returns `FAIL` / `rule_invalid` without touching any file.

**Structural ([rule_schema.json](../experiments/rule_schema.json)):**

- Closed objects everywhere (`additionalProperties: false`).
- Required fields per operation, and a discriminated `op` / `kind` / `type`.
- Identifier and qualified-name patterns, so no parentheses, spaces, paths, or code are possible.
- Semver `bundle_version` and PEP 440-style ranges.
- Size limits: ≤ 32 operations, ≤ 8 edits per `replace_call`, strings ≤ 500 characters.

**Semantic ([schema.py](../src/molt/schema.py) `semantic_errors`):**

1. Operation ids are unique.
2. Old and new version ranges are not identical, and the new lower bound is not below the old upper bound.
3. If `import_module` is set, every qualified name starts with it.
4. `rename_symbol` changes only the last component and is not a no-op. The same old name is not renamed twice, and there are no rename chains (`A→B`, `B→C`).
5. `change_import` and `rename_argument` are not no-ops.
6. In `replace_call`, no keyword is read or written by more than one edit, and no edit reads and writes the same keyword. `trigger_keyword` is the keyword of a move/rename/remove edit. `add_keyword` never targets the trigger.
7. No two call-restructuring operations share the same `(target_call, trigger keyword)`.

The rejection fixtures live in `tests/test_rule_schema.py` (28 prohibited cases plus the legacy v1 bundle).

## 6. Expressibility of the pilot tasks under v2

| Pilot site | v2 status | Evidence |
| --- | --- | --- |
| PyJWT: `jwt.ExpiredSignature` / `InvalidAudience` / `InvalidIssuer` → `…Error` | **Expressible** (`rename_symbol`) | Reference rule; engine PASS on `tests/fixtures/pyjwt_repo` |
| PyJWT: `verify_expiration=v` → `options={"verify_exp": v}`, merging into existing `options` | **Expressible** (`replace_call` / `move_keyword_into_dict`) | Frozen exemplar reproduced byte-for-byte (`test_engine_reproduces_frozen_development_exemplar_exactly`) |
| PyJWT: missing `algorithms=` | **Declared abstention** (`abstain`) | By design: security policy |
| SQLAlchemy: `select([a, b])` → `select(a, b)` | **Not expressible in v2**. No edit kind reads positional arguments or unwraps a list. | Recorded as unsupported. Adding a `unwrap_list_argument` edit requires a schema version bump and fixtures (protocol §9). |
| Pydantic: `from pydantic import BaseSettings` → `pydantic_settings` | Schema-expressible (`change_import`), **engine-unsupported in 0.1** | Reported as abstention |

## 7. Versioning

Any change to fields, edit kinds, or semantics bumps `schema_version`. It also needs a protocol amendment (protocol §14, item 6) and updates to this file, the JSON Schema, the reference rule, the evidence packet's output-format section, and tests in the same commit.
