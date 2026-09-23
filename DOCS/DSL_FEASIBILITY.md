# Bounded LibCST DSL vs Comby / ast-grep / GritQL — M0 feasibility note

**Dated 2026-09-24. Registered by [protocol.md §17](../experiments/protocol.md).** This note answers the roadmap's M0 requirement to "compare the planned small DSL with existing languages and record why implementing a bounded LibCST substrate is feasible for these RQs".

**Method and limits.** For Comby, ast-grep and GritQL this is a **desk review of their public documentation**. None of the three was installed or benchmarked on the PyJWT fixtures, and the comparison makes no performance claim. The Molt column, by contrast, is **executed evidence**: `src/molt/`, `tests/test_matcher_transformer.py` and `tests/test_engine.py`. Claims about the other tools are limited to their documented core model. Where a capability could not be confirmed from documentation, the table says *unverified* instead of guessing.

## What the RQs require from the rule representation

1. **A generation target that can be validated before execution** (RQ1/RQ3). A model's output must be rejectable as a whole, with per-field reasons, without running it.
2. **No raw-code escape hatch** (RQ4). If the representation lets a rule emit arbitrary replacement text, "rule generation" collapses into patch generation. The constraint whose coverage cost RQ4 measures would then not exist.
3. **Binding-aware matching with explicit abstention** (RQ1 unrelated edits, RQ4 matching ablation). The rule must distinguish `jwt.decode` from `codec.decode` and from a shadowed local `jwt`. When it cannot tell, it must abstain *with a recorded reason*.
4. **Expressibility labelling** (RQ4). The frozen grammar must make "unsupported" a crisp outcome.
5. **Formatting-preserving edits** for reviewable diffs.

## Comparison

| Requirement | Comby | ast-grep | GritQL | Molt v2 on LibCST |
| --- | --- | --- | --- | --- |
| Matching model | Structural templates with holes over balanced delimiters, strings and comments; language-light | tree-sitter AST patterns with metavariables; YAML rules with relational (`inside`/`has`) and `not` combinators | Declarative query language over syntax trees with `where` clauses and rewrites | LibCST CST + `QualifiedNameProvider`/`ScopeProvider` metadata |
| Import-alias / shadowing resolution (`import jwt as pyjwt`; a parameter named `jwt`) | No: syntactic (MELT added type guards via an external service) | No semantic binding resolution documented (syntax-only) | Unverified for Python | **Yes**: executed tests `test_import_alias_is_followed` and `test_unrelated_lookalikes_and_shadowing_are_untouched` |
| Replacement representation | Free-form rewrite template (arbitrary text with holes) | `fix` template (arbitrary text with metavariables) | Rewrite snippets (arbitrary code with metavariables) | Closed set of typed edits; values are typed literals only |
| Raw-code escape hatch in generated rules | Present (template text) | Present (`fix` text) | Present (rewrite text) | **Absent by schema** (`tests/test_rule_schema.py` rejects code strings) |
| PyJWT `verify_expiration=` → `options={...}` **merge** with key-conflict, `**kwargs` and side-effect abstention | Needs several ordered templates; conflict detection is not expressible in a template | Possible to match both shapes with multiple rules; conflict and `**` detection must be encoded as negative patterns per case; no side-effect notion | Unverified | **One operation** (`move_keyword_into_dict`); every abstention case is executed in `test_unsafe_call_sites_abstain_without_editing` |
| Abstention *with reasons* as a first-class output | No (match or no match) | No (match or no match) | No documented abstain outcome | Yes: every candidate site is `changed` or `abstained` with a reason |
| Validation of LLM output before execution | Template parse only | YAML/schema validation of rule shape; `fix` text unconstrained | Query parse; rewrite body unconstrained | JSON Schema (draft 2020-12) + semantic checks |
| Formatting/comment preservation | Good for untouched text | Good for untouched text | Good for untouched text | Good for untouched text; executed in `test_multiline_merge_preserves_comments_and_layout` |
| Python-native dependency | OCaml binary | Rust binary (pip wheel exists) | Rust CLI | Python packages (`libcst`, `jsonschema`), pip-installable |

## Decision

A **bounded LibCST substrate is feasible and preferable for these RQs**.

- It is the only option here that provides import-aware binding resolution *and* removes the raw-code escape hatch. That escape hatch is what RQ4's constraint is about.
- Feasibility is not argued, it is demonstrated. The M1 vertical slice reproduces the frozen PyJWT exemplar byte-for-byte. It migrates the fixture repository to a passing test suite under PyJWT 2.10.1, which fails before migration. Every unsafe or ambiguous case in the executed test suite abstains. The whole engine is about 1,500 lines of Python.

The existing languages are **not** rejected as research comparators. They remain candidates for:

- Arm E-adjacent baselines;
- the optional RQ4 ablation (c), "equivalent Comby/ast-grep/GritQL rules on the equivalence-controlled subset" (ROADMAP.md).

That ablation's feasibility is decided before M8, as the roadmap requires. This note does not claim that the Molt DSL is a novel formalism. The contribution sought is the measured trade-off, not the language.

## Known ceiling of v2 (recorded, not fixed)

- **SQLAlchemy `select([a, b])` → `select(a, b)`**: no v2 edit reads positional arguments or unwraps a list. Unsupported until a schema version adds such an edit, with fixtures and a protocol amendment.
- **String-literal targeting** (for example frequency strings): unsupported.
- **`change_import`**: in the schema, not yet in the engine; its sites are reported as abstentions.
