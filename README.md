# Molt

**Molt studies when reusable LLM-authored migration logic is worthwhile for breaking Python dependency upgrades.** It compares verified correctness, cost, and reliability against repository-local LLM patching, and measures the migration coverage lost by constraining the reusable logic.

**Status: M0 open (one external blocker); M1 engine foundation started.** There is a deterministic rule engine for one migration family (PyJWT), an executable rule schema and a minimal CLI. There is still no admitted benchmark, no LLM rule generation, and no experimental result. This repository contains a research design, [milestone roadmap](DOCS/ROADMAP.md), [related-work review](DOCS/RELATED_WORK.md), [plain-English glossary](DOCS/GLOSSARY.md), [M0 candidate scorecards](DOCS/CANDIDATES.md), and a first slice of a [dated experiment protocol](experiments/protocol.md). A small, developer-only [test console](console/) exists for visually inspecting these artifacts and future module output; it is not a product UI.

## Research question

> For a known breaking Python dependency upgrade, when does one constrained migration rule bundle, authored from a small development-repository set and repaired only against that set, achieve a better verified-success–cost frontier on independent held-out repositories than repository-local LLM patching, including patching given one frozen development exemplar; and what coverage does the constraint sacrifice?

A bundle is one shared migration artifact containing composable operations, not a collection of repository-specific patches. The study concerns unseen client repositories of **known migrations**, not unseen dependency changes. This formulation is a proposed experiment, not a claim of literature priority.

| Question | What Molt will test |
| --- | --- |
| **RQ1 — Reuse and correctness** | How do reusable rules compare with direct patching, with and without a development exemplar, in verified repository success, unrelated edits, missed edits, and abstention across migrations? |
| **RQ2 — Economics conditional on correctness** | At what repository counts and budgets, if any, does reuse improve cost per verified success and cumulative cost, accounting for caching, setup, verification, failures, and retries? |
| **RQ3 — Repair transfer** | Does repairing one shared rule on several development repositories improve held-out outcomes, or does it overfit? |
| **RQ4 — Price of constraint and matching evidence** | How much required migration work is inexpressible in the bounded DSL, and, in an optional controlled ablation, does metadata-aware matching reduce unrelated edits enough to justify its coverage/abstention cost? |

A null or negative result can answer each question. Lower cost with weaker correctness is not automatically a better result.

## What prior work already establishes

LLM-assisted transformation synthesis, reusable codemods, declarative rules, deterministic application, cross-project transfer, and iterative refinement are established ideas. Molt uses these as experimental machinery.

| Closest work | Established overlap or necessary comparison |
| --- | --- |
| [BigBag](https://arxiv.org/abs/2606.24446) | Agent-generated executable AST transformations for breaking Java updates and cross-project transfer. |
| [SPELL](https://arxiv.org/abs/2602.01107) | Python migration scripts in PolyglotPiranha, synthesized from generated examples with iterative refinement. |
| [MELT](https://arxiv.org/abs/2308.14687) | Python API migration rules, Comby type guards, and client evaluation. |
| [Allain et al.](https://arxiv.org/abs/2609.03592) | Recent synthesis evaluation across Comby, GritQL, and Ast-Grep, including migration, reuse, and token measurement. |
| [Cummins et al.](https://arxiv.org/abs/2410.08806) | Reusable transforms compared with direct rewriting on small Python programs. |
| [RuleFlow](https://arxiv.org/abs/2602.09051) | Explicit amortization motivation for reusable compiler optimizations. See the [economics review](DOCS/RELATED_WORK.md#ruleflow). |
| [Google migration system](https://arxiv.org/abs/2504.09691) | Industrial evidence for direct LLM editing with validation and human review. |

The [source-backed comparison](DOCS/RELATED_WORK.md) records representations, feedback, transfer protocols, oracles, cost treatment, and remaining distinctions. It also retains REFAZER, LASE, Meditor, transformation infrastructure, and repository benchmarks. A different engine or a smaller language alone does not establish a research contribution.

## Planned comparison and information boundary

| Arm | Method |
| --- | --- |
| A | Direct repository-local LLM inspect/edit/test loop. |
| B | The same direct loop plus **one frozen development exemplar migration and patch** per migration. |
| C | Molt using the initial generated bundle, without repair. |
| D | Molt using development-only repair, paired with C's initial proposal. |
| E | Frozen regex/text substitutions. |
| F | Official/expert codemod where available; missing availability is reported. |

A and B are essential practitioner baselines. Both begin with fresh repository state and conversation, inspect only their assigned held-out repository, and receive the same public migration evidence and verification contract. B additionally receives one development exemplar selected and frozen before evaluation; it receives no other repository-specific migration patches. Neither direct arm sees hidden probes, other held-out patches/results, or Molt's held-out outcomes. Prompt caching may reuse the stable input prefix, not cross-repository solution memory.

C and D are authored with development examples and are frozen before held-out application. **Molt makes no LLM calls during held-out application.** Every arm starts from the same clean target-upgrade state with the same dependency delta, allowed edit paths, and final oracle. Method-specific information and setup effort are recorded explicitly.

## Correctness and economics

Admission requires a passing old-version baseline and an attributable failure after the controlled upgrade. Repository families stay in one partition. Verification combines unchanged tests, frozen external migration probes, required typechecks where pre-registered, policy compliance, and manual audit. Tests alone cannot establish correctness. Unsupported cases, failed proposals, abstentions, and unresolved infrastructure failures remain visible in the frozen denominator.

The descriptive cost model for one migration is:

```text
C_direct(n) = nL
C_Molt(n)   = R + nD
```

`L` is mean direct patching cost including retries; `R` includes rule generation and repair; `D` is deterministic application cost. With comparable monetary units and constant costs, equality occurs at `n = R / (L - D)` when `L > D`. There is no eventual saving under this model when `L <= D`. Success rates, cache hits, and repository difficulty need not be constant, so this crossing alone is insufficient.

The primary economic measure is **total cost / verified successful repositories**, reported alongside success counts and rates. Zero successes means no finite cost per success. Report LLM-only and full costs separately, including setup, development verification, application, final verification, failures, and abstentions. The [roadmap](DOCS/ROADMAP.md#economics-and-prompt-caching) defines full-cost equations, cumulative curves, marginal costs, ordering sensitivity, and break-even limitations.

Use realistic provider caching when available, with identical stable evidence prefixes where possible. Record uncached input tokens, cached input tokens, output tokens, reasoning tokens where exposed, actual billed cost, provider/model, and price schedule date. Do not disable caching to favor Molt; disclose unobservable or uncontrollable behavior.

## Bounded rules as a trade-off

Rules are versioned JSON data (`molt.rule.v2`, validated by JSON Schema plus semantic checks; see [DOCS/RULE_SPEC.md](DOCS/RULE_SPEC.md)) applied by fixed LibCST primitives: `rename_symbol`, `change_import` (schema only, not yet in the engine), `rename_argument`, `add_argument`, `remove_argument`, a structured `replace_call`, and declared `abstain`. Values are typed literals; there is no raw-code field. Generated rules cannot contain arbitrary Python, executable predicates, shell commands, or repository-specific patches. Determinism, idempotence, and schema validity are engineering properties, not semantic guarantees.

Measure required-site expressibility, unsupported-site rate, schema-valid generation, incorrect/out-of-contract edits, rule complexity, abstention, and verified success; reviewer effort is optional. Expanding the DSL toward arbitrary programs weakens the constraint, while keeping it tiny may exclude much of Tier 2. Neither outcome should be hidden by selecting only easy cases.

The proposed matcher uses [LibCST qualified-name and scope metadata](https://libcst.readthedocs.io/en/latest/metadata.html), with conservative handling of ambiguity. It cannot infer every receiver's runtime type. Compare it, if feasible, with the same primitive semantics using name/syntax-only matching, and optionally an equivalent external rule language. This ablation may find no useful metadata advantage. Pyright is initially a verifier, not an assumed symbol-resolution service.

## Staged scope and next milestone

Phase 0 investigates **at least 6–8 candidates**. A feasibility pilot targets approximately **three migrations**: a Tier 1 anchor, meaningful Tier 2 structure, and an ambiguity-sensitive or DSL-ceiling case, initially about **3–5 development repositories per pilot migration**. These are planning ranges, not admitted counts.

M0 must register an expansion rule using repository supply, admission effort, budget, oracle quality, and diversity. The preferred final target is **4–6 migrations with roughly 10–15 admitted independent repositories each, including development**; 5–6 migrations are preferable if affordable. A three-migration reduced study is acceptable if declared before held-out outcomes are inspected. No particular migration is selected: PyJWT, pandas, Pydantic, NumPy, HTTPX, bounded SQLAlchemy, and recent/low-exposure alternatives remain candidates.

Pilot repair budgets include **1, 2, 3, and 5 total proposals**, counting the initial proposal. Choose and freeze the V1 limit using development evidence only. Final migrations, repository counts/SHAs, model, exemplar, numeric budgets, and optional ablations remain unresolved.

**M0 status (2026-09-24): open, blocked on one external item.** The checklist with evidence is [protocol.md §19](experiments/protocol.md#19-m0-definition-of-done-status-2026-09-24). What is done:

- Eight candidate scorecards ([DOCS/CANDIDATES.md](DOCS/CANDIDATES.md)).
- A registered three-migration pilot: PyJWT anchor, SQLAlchemy Tier 2, Pydantic ambiguity/DSL ceiling.
- Reproducible zero-cost feasibility probes ([experiments/probes/](experiments/probes/)).
- An executable rule schema, `molt.rule.v2` ([DOCS/RULE_SPEC.md](DOCS/RULE_SPEC.md)).
- A DSL feasibility note ([DOCS/DSL_FEASIBILITY.md](DOCS/DSL_FEASIBILITY.md)).
- Numeric expansion, split, audit and stop policies, plus the direct-exemplar design. Every number is labelled empirical, policy or provisional.
- A hardened pilot runner.

The protocol is registered at v0.5.0 with a SHA-256 hash ([experiments/protocol.hash](experiments/protocol.hash)).

The V1 repair cap of 3 is a **provisional** default. The M5 development sweep selects the real value by a registered rule.

**The remaining blocker** is the measured PyJWT generation pilot on Gemini `gemini-3.7-flash`. The API cannot show whether a key's project has billing enabled, and the zero-cost constraint forbids risking a paid call. The pilot therefore runs only when the operator confirms Free Tier status:

```bash
.venv/bin/python experiments/run_pyjwt_pilot.py --env-file .env --confirm-free-tier
```

The cost figures in [experiments/pilot_estimate.json](experiments/pilot_estimate.json) are projections until that run exists.

**M1 foundation (started, not complete):** a deterministic LibCST engine in [src/molt/](src/molt/) with a minimal CLI. The engine flow, statuses and result format are in [DOCS/ENGINE.md](DOCS/ENGINE.md).

- The hand-written PyJWT rule ([migrations/pyjwt-1-to-2/rule.json](migrations/pyjwt-1-to-2/rule.json)) reproduces the frozen exemplar byte-for-byte.
- The same rule migrates a synthetic fixture repository from failing to passing under PyJWT 2.10.1.
- It abstains, with reasons, on ambiguous or unsafe sites.

There is no real admitted client repository, no multi-repository reuse (M2), no container harness (M4), and no LLM generation or repair yet.

## Quickstart (local, zero cost)

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q                                     # no network, no credentials
.venv/bin/molt apply migrations/pyjwt-1-to-2/rule.json tests/fixtures/pyjwt_repo \
    --verify ".venv/bin/python -m pytest -q -p no:cacheprovider tests" --diff   # dry run
python3 console/serve.py                                          # dev console on http://127.0.0.1:8420/
```

Dynamic Python behaviour, partial oracles, small samples and contamination limit conclusions. V1 excludes product dashboards, hosted services, automatic production PRs, and broader language or analysis platforms.
