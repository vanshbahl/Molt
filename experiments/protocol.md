# Molt experiment protocol

**Version 0.1.0 — dated 2026-09-05.** This is the first registered slice of the M0 protocol required by [ROADMAP.md](../DOCS/ROADMAP.md#phase-0--literature-candidate-feasibility--experimental-design). It freezes only the decisions this pass has actual evidence for (candidate research, two feasibility probes, and design choices the README/ROADMAP already committed to). Every other M0 requirement is listed under **Unresolved** with the reason it cannot responsibly be frozen yet. **This document does not close M0**, does not authorize engine implementation, model calls, or benchmark execution, and is not itself a completed pre-registration.

Amendment rule for this file: any future change updates the version and date above and appends an entry to [Amendment log](#amendment-log) — no silent edits to a frozen decision.

---

## 1. Research questions and hypotheses — **RESOLVED (adopted, not newly derived)**

RQ1–RQ4 and their falsifiable hypotheses are adopted verbatim from [ROADMAP.md](../DOCS/ROADMAP.md#research-questions-and-falsifiable-hypotheses) and [README.md](../README.md#research-question). Nothing in this pass changes them. Practical effect thresholds (e.g. a minimum meaningful cost-per-success gap, a minimum success-rate delta worth reporting as a finding) are **not** set here — they require development-cost measurements (M3–M7) that do not exist yet. **Unresolved: numeric practical-effect thresholds.**

---

## 2. Candidate investigation — **RESOLVED**

Eight candidates were investigated against primary sources (official changelogs/migration guides, fetched 2026-09-05) plus, for three of them, a real isolated-venv old-pass/new-fail reproduction. Full scorecards: [DOCS/CANDIDATES.md](../DOCS/CANDIDATES.md). Raw probe records: [feasibility_probes.json](feasibility_probes.json).

**Discovery queries used this pass** (for the pre-registration trail the roadmap asks for): official docs fetched directly for each of the roadmap's eight named leads; web searches run for existing-codemod discovery (`bump-pydantic` rules/status, `Ruff NPY201`, `sqlalchemy2-stubs` / SQLAlchemy codemod tooling, PyJWT codemod search, `httpx app= removed migration` replacement pattern, a general 2026 breaking-release sweep that surfaced pandas 3.0). Search date: 2026-09-05. Population boundary: the roadmap's own eight-lead list, plus whatever a direct replacement search surfaced when a lead failed admission (attrs → urllib3). **No repository-level discovery queries have been run yet** — that is Phase 6 curation, explicitly out of scope for this pass.

**Screened-out lead:** attrs modernization, rejected on direct evidence (old and new APIs coexist permanently, no break exists). Recorded in [DOCS/CANDIDATES.md](../DOCS/CANDIDATES.md#rejected-lead-attrs-modernization) per the roadmap's pre-registered replacement rule, replaced by urllib3 1→2.

---

## 3. Pilot migration selection — **RESOLVED (candidates and bounded scope only)**

| Role | Migration | Bounded task |
| --- | --- | --- |
| Tier 1 anchor | PyJWT 1.7.1 → 2.x | Exception rename (`ExpiredSignature`→`ExpiredSignatureError` etc.) + flat-kwarg→`options={}` restructuring. **Excludes** the `algorithms=` value-selection requirement (not safely inferable; see [CANDIDATES.md](../DOCS/CANDIDATES.md#1-pyjwt-171--2x)). |
| Meaningful Tier 2 | SQLAlchemy 1.3/1.4 → 2.0 | `select([col1, col2])` → `select(col1, col2)` list-to-positional unwrap only. **Excludes** `Query`→`select()`/`Session.execute()` ORM restructuring, `Query.get()`→`Session.get()`, and DML constructor changes. |
| Ambiguity / DSL-ceiling | Pydantic 1.10 → 2.x | Genuinely-removed imports only (confirmed: `from pydantic import BaseSettings`; likely by the same pattern `Color`/`PaymentCardNumber`, not independently probed). **Excludes** `.dict()`/`.json()`/inner `Config` class/`GenericModel` — probed and confirmed to be deprecation-only (still functional), which would violate the admission rule requiring an attributable failure. The excluded surface remains the vehicle for the DSL-ceiling *discussion*, not an admitted task. |

Rationale for this selection over the alternatives, and the registered post-pilot expansion order (NumPy → pandas 1→2 → urllib3 → HTTPX → pandas 3.0), are in [CANDIDATES.md's recommendation section](../DOCS/CANDIDATES.md#recommended-pilot-3-migrations). This selection was made using only development-facing evidence (public changelogs, a script the researcher wrote, no repository data of any kind) — it does not touch held-out material because no held-out material exists yet.

**Unresolved:**
- Exact development repository identities/SHAs (Phase 6 curation has not started).
- Whether SQLAlchemy's `select()` task or Pydantic's bounded import task will, once real repositories are screened, actually meet the "nonempty unchanged test suite that passes" and "attributable failure" admission bar at volume — the two probes here used one script each, not a repository test suite.
- Final Tier-2/ambiguity role split if, during Phase 6 screening, one of the three pilot migrations turns out to have too little admissible supply (fallback order registered in §7).

---

## 4. Development repository counts — **RESOLVED (adopt roadmap default, not a new decision)**

Adopt the roadmap's stated planning range: **3–5 development repositories per pilot migration** (9–15 total across the three pilot migrations), no specific repositories chosen. This is unchanged from [ROADMAP.md](../DOCS/ROADMAP.md#dataset-partitions-and-leakage-control) — restated here only so this protocol is self-contained. **Unresolved:** exact count per migration (depends on Phase 6 supply screening, not decided in advance of evidence).

---

## 5. Repair budget sweep — **RESOLVED (sweep set only)**

Adopt the roadmap's registered sweep: evaluate **1, 2, 3, and 5** total proposals (including the initial proposal) during development pilots, per [ROADMAP.md](../DOCS/ROADMAP.md#development-set-repair-policy). This is a restatement, not a new commitment. **Unresolved:** pilot spend ceiling for the sweep, the numeric minimum-useful-improvement/cost threshold for selecting among 1/2/3/5, tie-break/early-stopping handling, and — critically — the V1 numeric repair cap itself (explicitly gated on M3–M5 measured costs, which require paid generation calls not authorized by this pass).

---

## 6. Direct/exemplar, caching, and information-boundary policy — **RESOLVED (adopt existing design)**

No new decisions here; restated for a self-contained protocol:
- Arms A–F, their information boundaries, and B's one-frozen-exemplar treatment are exactly as specified in [README.md's comparison table](../README.md#planned-comparison-and-information-boundary) and [ROADMAP.md's experimental-arms section](../DOCS/ROADMAP.md#experimental-arms-information-and-budgets).
- Realistic provider prompt caching will be used when available; caching will not be disabled to favor Molt. Exact provider/cache-lifetime policy is **unresolved** (depends on model/provider selection, §9).

**Unresolved:** B's exemplar selection policy is *specified* (a qualifying complete migration selected by a recorded development-only ordering, per the roadmap) but *no exemplar has been selected* for any of the three pilot migrations — that requires an admitted development repository, which does not exist yet.

---

## 7. Expansion rule — **PARTIALLY RESOLVED**

**Resolved — tie-breaking and ordering policy** (a decision rule, not a data-dependent number, so it can be frozen without pilot-cost evidence): rank expansion candidates by (1) confirmed/likely repository supply, (2) oracle quality, (3) DSL/expressibility fit, (4) contribution to Tier/ambiguity diversity not already covered by an admitted migration. Ties are broken by the order the candidate was discovered and documented in this protocol pass (recorded in [CANDIDATES.md](../DOCS/CANDIDATES.md#comparative-ranking)). This yields the registered provisional order: **NumPy → pandas 1→2 → urllib3 → HTTPX → pandas 3.0.**

**Unresolved (requires pilot-cost measurement, per roadmap design):** numeric screening/person-hour/spend ceilings, the contingency reserve, and the stop condition threshold ("stop at the registered ceiling, exhausted viable supply, or six migrations, prefer five or six"). A rough, explicitly-labeled **projection** (not a ceiling) appears in §8 to give the expansion rule something to compare against once real costs exist.

---

## 8. Pilot cost projection — **RESOLVED as a labeled projection, not a budget commitment**

No paid generation or repair calls have been made; this pass made zero LLM calls. The following is a rough order-of-magnitude projection to satisfy the roadmap's "pilot cost estimate... can be projections" allowance, to be replaced with measured costs at M3–M7:

| Cost component | Basis for the projection | Status |
| --- | --- | --- |
| Direct-arm (A/B) inspect/edit/test loop, 3 migrations × ~4 development repos × 2 arms | Comparable published agentic coding-loop costs (not independently measured for Molt) | **Projection only** |
| Rule generation replicates (C), 3 migrations | Small number of independent generations per migration per the roadmap's replicate-selection policy (count itself unresolved, §1) | **Projection only** |
| Repair sweep (D), 1/2/3/5 proposals × 3 migrations | Scales with the sweep in §5; exact model/token cost unknown until §9 is resolved | **Projection only** |
| Verification compute | Low expected for PyJWT/SQLAlchemy's bounded tasks (no external DB service needed per [CANDIDATES.md](../DOCS/CANDIDATES.md)); pandas/Pydantic setup is low-moderate | **Qualitative only** |
| Curation/admission person-hours | Not started (Phase 6) | **Not estimated** |
| Audit person-hours | Depends on unresolved sample size (§1) | **Not estimated** |

**This table is intentionally not turned into a dollar figure.** Doing so before a model/provider is chosen (§9) and before any real generation call has been billed would fabricate false precision, which the roadmap explicitly warns against ("Do not treat six arms as six equivalent paid-agent loops"). **Unresolved:** an actual numeric pilot cost estimate, pending §9.

---

## 9. Explicitly unresolved (carried forward, not newly opened)

Per [ROADMAP.md's decision-status section](../DOCS/ROADMAP.md#decision-status-after-this-documentation-pass), still unresolved after this pass:

- Model/provider/price schedule and cache settings.
- Numeric replicate counts beyond "a small number, policy TBD."
- The V1 repair cap (needs §5's sweep evidence).
- Exact DSL primitive semantics for two capabilities this pass's research newly surfaced as open questions: (a) whether restricted `replace_call` can unwrap a list argument into positional arguments (needed for the SQLAlchemy pilot task) and wrap a captured argument inside a new call under a renamed keyword (needed for HTTPX, expansion-only); (b) whether the frozen DSL as scoped can target a string literal in an argument/frequency-string position at all (needed only if pandas 3.0's offset-alias rename is ever pursued — it is an expansion candidate, not a pilot task, precisely so this question does not block the pilot). Both are Phase 1 fixture questions, not resolved by this document.
- Audit sample size/rubric, blinding logistics, and second-reviewer availability.
- Whether the optional RQ4 metadata-matching ablation (and any external-DSL comparator) is feasible — pandas' `.append()` ambiguity (§3, expansion candidate) and Pydantic's `.dict()`/`.json()` collision (§3, pilot) are the two strongest candidate fixtures for it, but feasibility itself is undecided.
- Final numeric migration/repository counts and split proportions (depends on Phase 6 supply screening this pass explicitly did not perform).

---

## Amendment log

- **0.1.0 (2026-09-05):** Initial registration — candidate research, three feasibility probes, pilot selection and bounded-task scoping, tie-break/expansion ordering policy, and an explicit unresolved-items list.
