# Molt engine 0.1 (M1 foundation)

A deterministic, LibCST-based engine that applies one validated `molt.rule.v2` bundle to one Python repository and verifies the result. No model calls, no fuzzy matching. Rule language: [RULE_SPEC.md](RULE_SPEC.md).

## Flow

```text
rule.json ──► schema.py      JSON Schema + semantic validation ─► typed RuleBundle (or FAIL/rule_invalid)
repo/     ──► parser.py      discover *.py (sorted; skip tests, vendored dirs, symlinks) ─► LibCST parse
                             pre-filter: only files importing the rule's module
          ──► matcher.py     per operation, in order, fresh metadata:
                             QualifiedNameProvider/ScopeProvider ─► apply | abstain(reason) per site
          ──► transformer.py rewrite approved nodes only (formatting-preserving); re-parse every output
          ──► engine.py      unified diff; copy repo to a temp dir; write outputs there
          ──► verifier.py    run the verification command in the copy (no shell, timeout, credentials stripped)
          ──► EngineResult   PASS / FAIL / ABSTAIN / UNVERIFIED + evidence
                             (only with --write and PASS: publish files to the repo, via temp file + rename)
```

| Module | Responsibility |
| --- | --- |
| `models.py` | Frozen rule dataclasses and the result model |
| `schema.py` | Validation, canonical hash, typed loading |
| `parser.py` | File discovery, parsing, import facts |
| `matcher.py` | Binding-aware candidate detection and abstention |
| `transformer.py` | Atomic argument edits and node rewriting |
| `verifier.py` | Sandboxed-ish local command execution (not the Phase 4 container harness) |
| `engine.py` | Orchestration and classification |
| `cli.py` | `molt validate`, `molt apply` |

## Result statuses

| Status | When |
| --- | --- |
| `PASS` | ≥1 site changed, **no** site abstained, and the verification command exited 0 on the transformed copy. |
| `FAIL` | Rule invalid (`rule_invalid`), or verification failed, timed out or could not start (`verification_fail`, `verification_timeout`, `verification_error`). |
| `ABSTAIN` | Nothing was safely changed (`no_safe_transformation`: every candidate abstained; `no_applicable_sites`: nothing matched, e.g. already migrated), **or** verification passed but some sites abstained (`partial`: required sites still need a human). |
| `UNVERIFIED` | Sites changed but no verification command was given. An unrun check is never a pass. |

The repository is never modified unless `--write` is given **and** the status is `PASS`.

## CLI

```bash
molt validate migrations/pyjwt-1-to-2/rule.json
molt apply migrations/pyjwt-1-to-2/rule.json tests/fixtures/pyjwt_repo \
    --verify ".venv/bin/python -m pytest -q -p no:cacheprovider tests" --diff --json result.json
```

Output (actual run on 2026-09-24):

```text
Matched: 5
Changed: 5
Abstained: 0
Verification:
  <repo>/.venv/bin/python -m pytest -q -p no:cacheprovider tests: PASS
Result: PASS (all candidate sites changed and verification passed)
Written to repository: no (dry run)
```

Exit codes are 0 for PASS, 1 for FAIL, 3 for ABSTAIN and 4 for UNVERIFIED (2 is argparse usage errors).

## Result format — `molt.engine_result.v1` (console integration boundary)

`EngineResult.to_dict()` / `molt apply --json` emit this shape. The key order is stable. `tests/test_engine.py::test_result_dict_matches_documented_format` pins it.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema` | `"molt.engine_result.v1"` | Format version |
| `engine_version` | str | `molt.__version__` |
| `status`, `reason` | str | See statuses; `reason` starts with a machine-readable code (`partial:`, `no_applicable_sites:`, …) |
| `rule` | `{path, bundle_id, bundle_version, sha256}` | `sha256` is the canonical rule hash |
| `repo` | `{path, files_scanned, files_with_candidates, files_changed}` | |
| `summary` | `{matched, changed, abstained}` | `matched = changed + abstained` |
| `verification` | `{command, status, exit_code, duration_s, stdout_tail, stderr_tail}` | `status` ∈ pass/fail/timeout/error/not_run; tails ≤ 4000 chars |
| `sites[]` | `{op_id, op, file, line, column, decision, reason, before, after}` | `decision` ∈ changed/abstained; line/column are in the source as it stood when that operation ran |
| `file_issues[]` | `{file, kind, detail}` | `parse_error` or `invalid_output` |
| `rule_errors[]` | str | Validation issues when `rule_invalid` |
| `diff` | str | Unified diff, `a/`/`b/` prefixes, applies with `git apply` (tested) |
| `dry_run`, `written` | bool | |

The dev console's **Transform Diff** panel reads a committed sample of this format: `experiments/engine_runs/pyjwt_fixture_result.json`, served as `/data/engine_result.json`. Regenerate it with `.venv/bin/python experiments/engine_runs/generate.py`. A test fails if the sample drifts from current engine output.

## Guarantees tested

- Only binding-resolved sites change. Lookalikes, shadowed names and already-migrated code produce no edit.
- Ambiguity, `**kwargs`, non-literal dicts, key conflicts, side-effecting moves, name collisions, star imports and store contexts all abstain with reasons.
- The frozen PyJWT exemplar is reproduced byte-for-byte. Comments and layout survive multi-line merges.
- Output is idempotent (second run: zero sites) and deterministic (repeated runs give identical results). Every output file is re-parsed before anything is written. Test files are not transformed by default.
- The verification subprocess receives no `*KEY*`/`*TOKEN*`/`*SECRET*` variables.

## Not in 0.1 (deferred)

- `change_import` rewriting (sites are reported as abstentions).
- Positional/list argument edits (the SQLAlchemy pilot).
- Relative-import and re-export resolution.
- Container isolation (Phase 4); the verifier runs commands on the host.
- Multi-repository reuse runs (M2).
- LLM generation (Phase 3) and repair (Phase 5).
