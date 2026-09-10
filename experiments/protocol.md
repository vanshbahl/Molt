# Molt experiment protocol

**Version 0.2.0 — dated 2026-09-05.** This revision closes the M0 blockers that development-only, zero-or-near-zero-cost evidence can close: model/provider selection (§10), the PyJWT pilot's frozen development exemplar (§11), and estimate-derived (not measured) numeric ceilings (§13). It also records, plainly, that the one blocker requiring an actual billed model call — real measured token usage, latency, retries, and monetary cost — remains open (§12), because this pass was not authorized to spend against a real API key. **This document still does not close M0.** See [README.md](../README.md) and [ROADMAP.md](../DOCS/ROADMAP.md) for the resulting overall M0 status.

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

## 9. Explicitly unresolved (carried forward from v0.1.0, narrowed by §§10–13)

Per [ROADMAP.md's decision-status section](../DOCS/ROADMAP.md#decision-status-after-this-documentation-pass), still unresolved after v0.1.0. This pass resolved the model/provider choice and the PyJWT exemplar (struck through below, see §§10–11); the rest remain open for the reasons given:

- ~~Model/provider/price schedule and cache settings.~~ **Resolved for the PyJWT pilot's rule-generation calls — see §10.** Not resolved for Arms A/B (no admitted repository exists to run a direct-patching loop against) or for the SQLAlchemy/Pydantic pilots (out of this pass's scope, which was specifically "the first PyJWT pilot").
- Numeric replicate counts beyond "a small number, policy TBD" — **resolved for the PyJWT pilot only** (2, see [pilot_config.json](pilot_config.json)); SQLAlchemy/Pydantic remain TBD.
- The V1 repair cap (needs §5's sweep evidence, which needs a real billed run — see §12).
- Exact DSL primitive semantics for two capabilities this pass's research newly surfaced as open questions: (a) whether restricted `replace_call` can unwrap a list argument into positional arguments (needed for the SQLAlchemy pilot task) and wrap a captured argument inside a new call under a renamed keyword (needed for HTTPX, expansion-only); (b) whether the frozen DSL as scoped can target a string literal in an argument/frequency-string position at all (needed only if pandas 3.0's offset-alias rename is ever pursued — it is an expansion candidate, not a pilot task, precisely so this question does not block the pilot). Both are Phase 1 fixture questions, not resolved by this document. The PyJWT evidence packet (§11) surfaces a related, narrower open question: whether restricted `replace_call` can map several named flat kwargs into one nested `options={}` dict argument — flagged in the packet itself as feasible-but-untested, to be judged by the real generation attempt's output, not assumed here.
- Audit sample size/rubric, blinding logistics, and second-reviewer availability.
- Whether the optional RQ4 metadata-matching ablation (and any external-DSL comparator) is feasible — pandas' `.append()` ambiguity (§3, expansion candidate) and Pydantic's `.dict()`/`.json()` collision (§3, pilot) are the two strongest candidate fixtures for it, but feasibility itself is undecided.
- Final numeric migration/repository counts and split proportions (depends on Phase 6 supply screening this pass explicitly did not perform).

---

## 10. Model/provider selection for the PyJWT pilot — **RESOLVED**

**Provider/model: Anthropic, `claude-haiku-4-5-20251001`**, called directly via the Messages API (not the Claude Code session's own auth token — that credential is for this session's own operation, not an independently-logged, separately-billed research measurement). Full justification, rejected alternatives, request parameters, caching policy, and the real dated price schedule ($1/$5 per MTok input/output, $1.25/$0.10 cache write/read, fetched 2026-09-05 from [claude.com/pricing](https://claude.com/pricing)) are recorded in [pilot_config.json](pilot_config.json), not duplicated here to avoid two sources of truth. In one sentence: it is the cheapest current Claude model, reports the exact per-request usage fields the roadmap's economics section requires, and keeps Arms A–D in one pricing/tokenization system.

This resolves model/provider **for the PyJWT pilot's rule-generation calls (Arms C/D) only**. It does not resolve a model/provider for Arms A/B (they need an admitted repository to inspect, which does not exist — Phase 6 has not started) or for the SQLAlchemy/Pydantic pilots, which this pass was not asked to close.

---

## 11. PyJWT pilot development exemplar — **RESOLVED**

**The exemplar is the before/after code pair in [pilot_evidence_packet.md](pilot_evidence_packet.md#frozen-development-exemplar-real-probed-2026-09-05).** It was authored and probed fresh during this pass (not reused from the earlier `pyjwt-1-to-2` feasibility probe, which tested a different, out-of-scope site — the `algorithms=` requirement). The new probe is recorded as `pyjwt-1-to-2-bounded-task` in [feasibility_probes.json](feasibility_probes.json) and its raw output is appended to [probe_logs.txt](probe_logs.txt).

**Why this exemplar and not another:** the registered bounded pilot task (§3) has exactly two in-scope edit sites — the `jwt.ExpiredSignature` exception rename and the `verify_expiration=` → `options={"verify_exp": ...}` restructuring. No development repository is admitted yet (Phase 6 has not started), so the roadmap's normal exemplar source (a real client repository) does not exist. Using anything else — a synthetic example not actually run against both versions, or the older `algorithms=` probe, which the bounded task explicitly excludes — would either fabricate evidence or silently smuggle the excluded site back into the pilot. A minimal, freshly-probed, real before/after pair covering precisely the two in-scope sites (and nothing excluded) is the only option that is simultaneously real, in-scope, and available before curation starts.

**What the fresh probe added beyond the existing scorecard:** [CANDIDATES.md](../DOCS/CANDIDATES.md#1-pyjwt-171--2x) already flagged the options-restructuring site as "expressible... but not yet fixture-tested." The fresh probe found the site is harder than a flat rename in a specific, previously-undocumented way: on 2.x the old flat kwarg is not rejected with an error — it is **silently ignored**, so the break only surfaces as an unexpected `ExpiredSignatureError` later, not a clean `TypeError` at the call site. This is now recorded as the concrete reason the options-restructuring site needs a behavioral oracle, not just an exception-based one, and it is disclosed to the pilot model directly in the evidence packet.

**Scope note:** this resolves the exemplar for the PyJWT pilot only. SQLAlchemy and Pydantic pilot exemplars remain unselected (not this pass's scope).

---

## 12. Real pilot execution status — **BLOCKED (named, single reason)**

**No model call has been made.** The evidence packet (§11), model/provider configuration (§10), and cost projection ([pilot_estimate.json](pilot_estimate.json)) are complete and require no further design work to execute — the pilot is configured, not designed-but-vague. It is blocked on exactly one thing: **this pass was not given a billable API key or explicit authorization to spend against one.** When asked, the option chosen was "mock/estimated pilot only, no real spend" (recorded here as the actual reason, not inferred).

Consequences, stated plainly:

- **Token usage, latency, and retry behavior are not measured.** [pilot_estimate.json](pilot_estimate.json) contains only a projection built from a real, measured evidence-packet size and a real, dated price schedule, plus explicitly-labeled assumptions about output size. It is not a substitute for an observed request.
- **Monetary cost is not measured**, only projected (worst-case under 5 US cents for the full registered 2-replicate PyJWT pilot — see `pilot_estimate.json#cost_projection_usd`).
- **The numeric ceilings in [ceilings.json](ceilings.json) are therefore estimate-derived or policy defaults, not the "from measured evidence" ceilings the closure task asked for.** Each ceiling in that file states explicitly which kind it is.
- **This is the single fact that keeps M0 from closing** under the stronger bar ("measure actual token usage, latency, retries, and monetary cost") than the roadmap's own minimum Phase 0 deliverable, which permits a cost estimate to be "projections... replace with measured development costs at M3–M7." See [README.md](../README.md) and [ROADMAP.md](../DOCS/ROADMAP.md) for the resulting status statement.

**To unblock:** provide a billable Anthropic API key (env var, not typed into chat) and explicit authorization for a spend up to the ceiling in [ceilings.json](ceilings.json) (`pyjwt_pilot_hard_spend_ceiling_usd: 2.00`, against a projected actual cost under $0.05). The evidence packet and config do not need to change to execute this.

---

## 13. Numeric screening/attempt/retry/spend ceilings — **PARTIALLY RESOLVED (estimate-derived, not measured)**

Full values, bases, and explicit measured-vs-provisional labeling are in [ceilings.json](ceilings.json); summarized:

| Ceiling | Value | Basis |
| --- | --- | --- |
| PyJWT pilot hard spend ceiling | $2.00 | ~40x margin over a real-evidence-packet-size-derived, real-priced worst-case projection (~$0.05) |
| PyJWT pilot generation replicates | 2 | Policy decision (smallest count showing any repeatable-vs-fluke signal), registered before any call |
| Repair proposal sweep | 1, 2, 3, 5 | Restated from ROADMAP.md/§5, not new |
| Max transport retries per request | 2, 60s timeout | Policy cap set before any call, per ROADMAP.md's retry-capping requirement |
| Phase 6 screening ceiling (per migration) | 20 repos / 4 person-hours | **Provisional default, explicitly not derived from measured evidence** — Phase 6 has not started |
| V1 repair cap | **not set** | Requires §12's real pilot run (ROADMAP.md M5 gate) |

The honest summary: ceilings that could be computed from a real artifact (the evidence packet) and a real, dated price schedule without spending money are computed and frozen. Ceilings that inherently require an observed model call (the V1 repair cap) or observed curation effort (the Phase 6 screening ceiling) are either left unset or explicitly marked as an unevidenced provisional default — never presented as more certain than they are.

---

## Amendment log

- **0.1.0 (2026-09-05):** Initial registration — candidate research, three feasibility probes, pilot selection and bounded-task scoping, tie-break/expansion ordering policy, and an explicit unresolved-items list.
- **0.2.0 (2026-09-05):** Added §§10–13. Resolved model/provider selection and the PyJWT pilot's development exemplar (backed by a fresh, real, zero-cost probe — `pyjwt-1-to-2-bounded-task` in feasibility_probes.json). Authored the real evidence packet and pilot config ([pilot_evidence_packet.md](pilot_evidence_packet.md), [pilot_config.json](pilot_config.json)) and a price-schedule-based cost projection ([pilot_estimate.json](pilot_estimate.json)). Recorded that the real billed pilot call itself was not authorized this pass (§12) and is now the single named reason M0 remains open under the stronger "measured, not projected" bar. Registered estimate-derived and policy-default numeric ceilings ([ceilings.json](ceilings.json)), each labeled by kind.
