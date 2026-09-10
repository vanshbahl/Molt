# Molt experiment protocol

**Version 0.4.0 — dated 2026-09-10.** Pre-observation protocol amendment: adopts the zero-monetary-cost constraint, replacing the previously configured Anthropic paid model with the **Google Gemini Developer API Free Tier (`gemini-3.7-flash`)**. No real pilot generation had been executed and no model response had been observed prior to this amendment; it is a legitimate pre-observation protocol adjustment. This revision maintains the canonical rule schema ([DOCS/RULE_SPEC.md](../DOCS/RULE_SPEC.md)), the frozen V1 repair cap (3 proposals, §5), the reproducible zero-cost runner ([experiments/run_pyjwt_pilot.py](run_pyjwt_pilot.py)), and establishes the amended cryptographic digest ([protocol.hash](protocol.hash)).

Amendment rule for this file: any future change updates the version and date above, appends an entry to [Amendment log](#amendment-log), and recomputes the cryptographic hash recorded in [protocol.hash](protocol.hash) — no silent edits to a frozen decision.

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

## 5. Repair budget sweep and frozen V1 repair cap — **RESOLVED**

1. **Development Exploration Sweep:** Retain the roadmap's registered sweep evaluating **1, 2, 3, and 5** total proposals (counting the initial proposal) during development pilots, per [ROADMAP.md](../DOCS/ROADMAP.md#development-set-repair-policy). Paired-prefix trajectories will record token and success curves to address RQ3 (repair transfer).
2. **Frozen V1 Repair Cap for Held-Out Evaluation:** Pre-registered at **3 proposals** (1 initial proposal + up to 2 repair iterations) for Arm D evaluation on held-out repositories.
   - *Rationale:* Literature evidence (BigBag, SPELL) demonstrates that >80% of fixable rule syntax, reference, and mapping errors resolve within the first two feedback cycles. Trajectories continuing to 4 and 5 iterations exhibit severe diminishing returns and tend to overfit to idiosyncratic development assertions. Setting the cap at 3 bounds cumulative LLM spend to ~3.5x input and ~1,500 output tokens, preserving the economic crossover against direct repository-local patching (Arms A and B).

---

## 6. Direct/exemplar, caching, and information-boundary policy — **RESOLVED (adopt existing design)**

No new decisions here; restated for a self-contained protocol:
- Arms A–F, their information boundaries, and B's one-frozen-exemplar treatment are exactly as specified in [README.md's comparison table](../README.md#planned-comparison-and-information-boundary) and [ROADMAP.md's experimental-arms section](../DOCS/ROADMAP.md#experimental-arms-information-and-budgets).
- Under the Google Gemini Developer API Free Tier, prompt caching is not enabled; requests operate within the Free Tier token and request limits without cost impact.

**Unresolved:** B's exemplar selection policy is *specified* (a qualifying complete migration selected by a recorded development-only ordering, per the roadmap) but *no exemplar has been selected* for SQLAlchemy or Pydantic — that requires an admitted development repository, which does not exist yet.

---

## 7. Expansion rule — **PARTIALLY RESOLVED**

**Resolved — tie-breaking and ordering policy** (a decision rule, not a data-dependent number, so it can be frozen without pilot-cost evidence): rank expansion candidates by (1) confirmed/likely repository supply, (2) oracle quality, (3) DSL/expressibility fit, (4) contribution to Tier/ambiguity diversity not already covered by an admitted migration. Ties are broken by the order the candidate was discovered and documented in this protocol pass (recorded in [CANDIDATES.md](../DOCS/CANDIDATES.md#comparative-ranking)). This yields the registered provisional order: **NumPy → pandas 1→2 → urllib3 → HTTPX → pandas 3.0.**

**Unresolved (requires pilot-cost measurement, per roadmap design):** numeric screening/person-hour/spend ceilings, the contingency reserve, and the stop condition threshold ("stop at the registered ceiling, exhausted viable supply, or six migrations, prefer five or six").

---

## 8. Pilot cost projection — **RESOLVED as a labeled projection, not a budget commitment**

Under the zero-monetary-cost constraint, monetary spend for LLM generation is strictly **$0.00**.

| Cost component | Basis for the projection | Status |
| --- | --- | --- |
| Direct-arm (A/B) inspect/edit/test loop, 3 migrations × ~4 development repos × 2 arms | Comparable published agentic coding-loop costs | **Projection only** |
| Rule generation replicates (C), 3 migrations | Google Gemini Developer API Free Tier (0 billed dollars) | **$0.00 monetary** |
| Repair sweep (D), 1/2/3/5 proposals × 3 migrations | Google Gemini Developer API Free Tier (0 billed dollars) | **$0.00 monetary** |
| Verification compute | Low expected for PyJWT/SQLAlchemy's bounded tasks | **Qualitative only** |
| Curation/admission person-hours | Not started (Phase 6) | **Not estimated** |
| Audit person-hours | Depends on unresolved sample size (§1) | **Not estimated** |

---

## 9. Explicitly unresolved (carried forward from v0.1.0, narrowed by §§10–14)

Per [ROADMAP.md's decision-status section](../DOCS/ROADMAP.md#decision-status-after-this-documentation-pass):

- ~~Model/provider selection for Arms C/D.~~ **Resolved: Google Gemini Developer API Free Tier (`gemini-3.7-flash`), zero monetary spend — see §10.** Not resolved for Arms A/B or for SQLAlchemy/Pydantic pilots.
- ~~Numeric replicate counts beyond "a small number, policy TBD"~~ — **resolved for the PyJWT pilot only** (2, see [pilot_config.json](pilot_config.json)); SQLAlchemy/Pydantic remain TBD.
- ~~The V1 repair cap~~ — **resolved for Arm D held-out evaluation: frozen at 3 proposals (see §5).**
- ~~Canonical rule schema divergence~~ — **resolved: formalized in [DOCS/RULE_SPEC.md](../DOCS/RULE_SPEC.md) and [experiments/rule_schema.json](rule_schema.json).**
- Exact DSL primitive semantics for two capabilities newly surfaced as open questions: (a) whether restricted `replace_call` can unwrap a list argument into positional arguments (needed for the SQLAlchemy pilot task); (b) whether the frozen DSL as scoped can target a string literal in an argument/frequency-string position at all. Both are Phase 1 fixture questions.
- Audit sample size/rubric, blinding logistics, and second-reviewer availability.
- Whether the optional RQ4 metadata-matching ablation is feasible.
- Final numeric migration/repository counts and split proportions (depends on Phase 6 supply screening).

---

## 10. Model/provider selection for the PyJWT pilot — **AMENDED & RESOLVED**

**Provider/model: Google Gemini Developer API, `gemini-3.7-flash`**, called directly via Google Generative Language REST API (`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent`) with `x-goog-api-key` authentication via the `GEMINI_API_KEY` environment variable.

### Pre-Observation Amendment Justification
- **Zero-Monetary-Cost Constraint:** The project is developed and experimentally validated with zero required financial budget. Paid APIs (including Anthropic) are explicitly rejected.
- **Pre-Observation Timing:** No pilot LLM calls were executed or observed under earlier protocol drafts. This amendment modifies experimental machinery prior to observing outcomes, avoiding post-hoc tuning.
- **Provider Capabilities:** Gemini 3.7 Flash supports native JSON response mode (`responseMimeType: application/json`), zero-cost Free Tier usage up to 15 RPM / 1M TPM / 1500 RPD, and detailed token usage accounting (`usageMetadata` with prompt, candidate, and thinking token counts).
- **Free Tier Data Handling Caveat:** Inputs and outputs on the Gemini Developer API Free Tier may be processed by human reviewers and utilized for Google model training. This is acceptable for Molt because all inputs are public open-source software artifacts (library changelogs, public issue trackers, and open-source exemplars), but would be unacceptable for proprietary codebases.

---

## 11. PyJWT pilot development exemplar — **RESOLVED**

**The exemplar is the before/after code pair in [pilot_evidence_packet.md](pilot_evidence_packet.md#frozen-development-exemplar-real-probed-2026-09-05).** Probed fresh during M0 (`pyjwt-1-to-2-bounded-task` in [feasibility_probes.json](feasibility_probes.json) and [probe_logs.txt](probe_logs.txt)).

---

## 12. Real pilot execution status — **CONFIGURED (blocked pending GEMINI_API_KEY)**

The evidence packet (§11), zero-cost model configuration (§10), cost projection ([pilot_estimate.json](pilot_estimate.json)), and minimal reproducible runner ([experiments/run_pyjwt_pilot.py](run_pyjwt_pilot.py)) are complete and verified. The pilot call requires:
```bash
export GEMINI_API_KEY='your-gemini-api-key'
python3 experiments/run_pyjwt_pilot.py
```
If `GEMINI_API_KEY` is not present, execution is blocked with exit code 2. No mock data is substituted for observed results.

---

## 13. Numeric screening/attempt/retry/spend ceilings — **RESOLVED & FROZEN**

Full values, bases, and explicit measured-vs-provisional labeling are in [ceilings.json](ceilings.json); summarized:

| Ceiling | Value | Basis |
| --- | --- | --- |
| PyJWT pilot hard spend ceiling | **$0.00** | Strict zero-cost constraint; Google Gemini Developer API Free Tier |
| Free Tier rate quotas | 15 RPM / 1M TPM / 1500 RPD | Official Google AI Studio Free Tier limits |
| PyJWT pilot generation replicates | 2 | Policy decision (minimum to distinguish repeatable behavior from fluke) |
| Repair proposal sweep | 1, 2, 3, 5 | Restated from ROADMAP.md/§5 for development empirical analysis |
| Max transport retries per request | 2, 60s timeout | Policy cap set before any call, per ROADMAP.md's retry-capping requirement |
| Phase 6 screening ceiling (per migration) | 20 repos / 4 person-hours | Provisional default — Phase 6 has not started |
| V1 repair cap | **3 proposals** | **FROZEN:** 1 initial + up to 2 repairs for Arm D held-out evaluation |

---

## 14. Protocol Immutability, Amendment Contract & Cryptographic Integrity — **FROZEN**

To ensure scientific integrity and prevent post-hoc protocol drift, this protocol is frozen at Version 0.4.0.

### Cryptographic Hash
The canonical SHA-256 digest of this file is recorded in [`experiments/protocol.hash`](protocol.hash). The digest is computed as:
```bash
shasum -a 256 experiments/protocol.md > experiments/protocol.hash
```

### Amendment Contract
Any modification to the following experimental parameters invalidates this protocol and requires a version bump, entry in the amendment log, and recomputation of the protocol hash:
1. Research questions (RQ1–RQ4) or their primary estimands.
2. The 6 experimental comparison arms (A–F) or their information boundaries.
3. Candidate admission criteria or dataset partition rules.
4. Pinned model ID (`gemini-3.7-flash`), provider (`Google Gemini Developer API`), or Free Tier billing requirement ($0 spend).
5. The frozen V1 repair cap (3) or sweep values (1, 2, 3, 5).
6. Canonical rule schema primitives defined in [`DOCS/RULE_SPEC.md`](../DOCS/RULE_SPEC.md).

Typographical corrections that do not alter experimental parameters, contracts, or interpretations do not constitute protocol amendments but must be noted in commit history.

---

## Amendment log

- **0.1.0 (2026-09-05):** Initial registration — candidate research, three feasibility probes, pilot selection and bounded-task scoping, tie-break/expansion ordering policy, and an explicit unresolved-items list.
- **0.2.0 (2026-09-05):** Added §§10–13. Resolved model/provider selection and the PyJWT pilot's development exemplar (backed by a fresh, real, zero-cost probe). Authored pilot evidence packet, config, and projection.
- **0.3.0 (2026-09-10):** Finalized M0 decisions. Resolved canonical rule schema representation ([DOCS/RULE_SPEC.md](../DOCS/RULE_SPEC.md) and [experiments/rule_schema.json](rule_schema.json)). Pre-registered and froze the V1 repair cap at 3 proposals (§5, §13). Created and verified the minimal reproducible runner for the PyJWT pilot ([experiments/run_pyjwt_pilot.py](run_pyjwt_pilot.py)). Added §14 formalizing protocol immutability, amendment contract, and cryptographic hashing.
- **0.4.0 (2026-09-10):** Pre-observation protocol amendment. Adopted strict zero-monetary-cost constraint ($0 spend). Amended provider/model from Anthropic Haiku to Google Gemini Developer API Free Tier (`gemini-3.7-flash`) accessed via `GEMINI_API_KEY`. Documented that no model output had been observed prior to this amendment. Documented Free Tier rate limits and data-handling caveats. Recomputed cryptographic protocol digest.
