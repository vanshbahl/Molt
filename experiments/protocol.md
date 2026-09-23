# Molt experiment protocol

**Version 0.5.0 — dated 2026-09-24.** This is a pre-observation amendment: no model has been called under any protocol version. It does five things:

- replaces the non-executable v1 rule schema with `molt.rule.v2`;
- relabels the V1 repair cap as a **provisional policy default**, not an empirically selected value;
- registers the numeric expansion, split, audit, stop and direct-exemplar policies;
- adds a free-tier execution gate to the pilot runner;
- records that M0 remains **open** on one external item: the measured pilot run (§12).

Amendment rule for this file: any change updates the version and date above, appends an entry to the [Amendment log](#amendment-log), and recomputes the SHA-256 digest recorded in [protocol.hash](protocol.hash). No silent edits to a registered decision.

**Value labels used below:**

- **EMPIRICAL**: derived from recorded measurements.
- **POLICY**: a registered decision rule, or a value chosen without data.
- **PROVISIONAL**: a policy value that a named later measurement will revise.

---

## 1. Research questions, hypotheses and practical thresholds — **RESOLVED**

RQ1–RQ4 and their falsifiable hypotheses are adopted verbatim from [ROADMAP.md](../DOCS/ROADMAP.md#research-questions-and-falsifiable-hypotheses).

**Practical thresholds (POLICY, new in 0.5.0):**

- No noninferiority or equivalence margin is registered.
- Results are reported as descriptive frontiers with per-migration counts, family-level intervals and paired-bootstrap differences (ROADMAP metrics section).
- No arm is described as "equivalent", "noninferior" or "better at equal correctness" on the basis of overlapping intervals.
- A difference is called a *finding* only when its family-level paired-bootstrap 95% interval excludes zero. All other differences are reported as observed values without that label.

---

## 2. Candidate investigation — **RESOLVED**

Eight candidates were investigated against primary sources (fetched 2026-09-05). Three of them also got real isolated-venv old-pass/new-fail reproductions. Full scorecards: [DOCS/CANDIDATES.md](../DOCS/CANDIDATES.md). Structured probe records: [feasibility_probes.json](feasibility_probes.json).

**Reproducibility (new in 0.5.0).** The probes are now reusable scripts in [probes/](probes/), driven by [probes/run_probes.py](probes/run_probes.py): a fresh venv per pinned version, PyPI only, zero cost. The 2026-09-23 re-run ([probes/results/probe_run_20260923.json](probes/results/probe_run_20260923.json), raw output in `.txt`) reproduced old-pass → new-fail for all four script probes. That covers PyJWT `algorithms=`, the PyJWT bounded-task sites, SQLAlchemy `select([...])` and the Pydantic `BaseSettings` import.

It also corrected one detail. PyJWT 2.10.1 emits a generic "unsupported kwargs" DeprecationWarning for the flat `verify_expiration=` kwarg; the kwarg is not silently ignored. The behaviour is unchanged: no error and no effect.

Discovery queries and search date (2026-09-05), the population boundary, and the attrs → urllib3 replacement are unchanged from 0.1.0. **No repository-level discovery has run yet** (Phase 6).

---

## 3. Pilot migration selection — **RESOLVED (candidates and bounded scope only)**

| Role | Migration | Bounded task |
| --- | --- | --- |
| Tier 1 anchor | PyJWT 1.7.1 → 2.x | Exception-alias renames (`ExpiredSignature`→`ExpiredSignatureError`, `InvalidAudience`, `InvalidIssuer`) + `verify_expiration=`→`options={"verify_exp": …}`. **Excludes** `algorithms=` value selection (declared abstention). |
| Meaningful Tier 2 | SQLAlchemy 1.3/1.4 → 2.0 | `select([a, b])` → `select(a, b)` only. **Not expressible in `molt.rule.v2`** ([RULE_SPEC §6](../DOCS/RULE_SPEC.md)): this is a registered DSL-ceiling data point. It is not grounds to widen the grammar before evidence. |
| Ambiguity / DSL-ceiling | Pydantic 1.10 → 2.x | Genuinely removed imports only (probed: `from pydantic import BaseSettings`). Deprecation-only surface excluded from admission. |

The expansion order is NumPy → pandas 1→2 → urllib3 → HTTPX → pandas 3.0 ([CANDIDATES.md](../DOCS/CANDIDATES.md#comparative-ranking)). Selection used development-facing evidence only.

**Unresolved:**

- Development repository identities and SHAs (Phase 6).
- Whether SQLAlchemy/Pydantic supply meets admission at volume.

---

## 4. Development repository counts — **RESOLVED (planning range)**

3–5 development repositories per pilot migration (POLICY, adopted from the roadmap). The exact count follows §16's split rule once supply is known.

---

## 5. Repair budget sweep and V1 cap — **POLICY RESOLVED; NUMERIC CAP PROVISIONAL**

1. **Sweep (POLICY).** Development pilots evaluate **1, 2, 3 and 5** total proposals, counting the initial one. Budgets are read off paired prefixes of one trajectory per generation replicate. Every malformed, invalid, truncated or refused output consumes a proposal.
2. **Selection rule (POLICY, registered now, applied at M5).** Let `S(b)` be the development verified-success count, summed over development repositories × generation replicates, at budget `b`. Choose the **smallest** `b ∈ {1,2,3,5}` such that `S(b) ≥ max_b' S(b') − max(1, ⌈0.10 × N_dev_runs⌉)`, where all required safety fixtures also pass at `b`. Ties go to the smaller `b`. The request count per success is reported alongside. Under the $0 regime, requests are the cost proxy.
3. **V1 cap = 3 is a PROVISIONAL default, not an empirically selected value.** It exists only so downstream configuration has a placeholder. The M5 sweep selects the real cap by rule 2. The cap is frozen at M7/M8, before any held-out evaluation, and never chosen from held-out outcomes. If the sweep proves infeasible, a dated amendment records that before freeze, and the cap stays 3 with that weaker justification disclosed.
4. **Withdrawn rationale.** v0.3.0/v0.4.0 justified the cap with ">80% of fixable errors resolve within two feedback rounds (BigBag, SPELL)". That figure was not verified against a specific reported result in those papers. It is withdrawn and is not used.

---

## 6. Direct/exemplar, caching and information boundary — **RESOLVED**

- Arms A–F and their information boundaries are as specified in [README.md](../README.md#planned-comparison-and-information-boundary) and [ROADMAP.md](../DOCS/ROADMAP.md#experimental-arms-information-and-budgets).
- **Direct-arm exemplar (Arm B):** see §18.
- **Caching (POLICY):**
  - Molt creates no explicit context cache.
  - The shared evidence packet is always the first user content: a stable prefix. B's exemplar comes next in its stable prefix, before any repository-specific context.
  - Any implicit provider caching is recorded from `usageMetadata.cachedContentTokenCount` when reported. It is not controlled and not assumed.
  - Timestamps and run order are recorded per request.
  - Caching is never disabled or busted to favour an arm.

---

## 7. Expansion rule — **RESOLVED (§15)**

The tie-breaking and ordering policy of 0.1.0 is unchanged. Numeric screening, admission, expansion and stop rules are now in §15. Their provisional numbers are labelled.

---

## 8. Pilot cost projection — **RESOLVED as a labelled projection**

[pilot_estimate.json](pilot_estimate.json) records exact counts of the real request content (packet v0.2.0 + schema) and heuristic token ranges. It contains **no** observed tokens, latency or cost.

Monetary cost is not observable through the Gemini API. The expected charge is $0.00 only on a key whose project has no billing account. Measured values exist only in `measured_runs/` after §12 runs.

| Component | Status |
| --- | --- |
| Arm C initial proposals (PyJWT, 2 replicates) | Token **projection**; expected $0.00 under a confirmed Free Tier |
| Repair sweep (M5) | Not run in M0 |
| Direct arms A/B | Not estimated (needs admitted repositories) |
| Verification compute | Local; measured per engine run (`verification.duration_s`) |
| Curation / audit person-hours | Ceilings in §15/§16 (PROVISIONAL); not yet measured |

---

## 9. Explicitly unresolved (carried forward)

- Model/provider for Arms A/B and for the SQLAlchemy/Pydantic pilots (same $0 constraint applies).
- Replicate counts beyond the PyJWT pilot's 2.
- The numeric V1 repair cap (§5; M5).
- DSL capability questions from 0.1.0:
  - (a) list-to-positional unwrap: **answered for v2: not expressible** (RULE_SPEC §6); any extension needs a schema version bump;
  - (b) string-literal targeting: **not expressible in v2**.
- Whether the optional RQ4 metadata ablation and the external-language ablation (c) are feasible: decided before M8.
- Final migration/repository counts (Phase 6 supply).

---

## 10. Model/provider for the PyJWT pilot — **RESOLVED**

**Google Gemini Developer API, `gemini-3.7-flash`**, called via `generateContent` with `x-goog-api-key` from `GEMINI_API_KEY`. The official pricing page lists the model with a Free Tier (checked 2026-09-24).

- A key inherits its project's billing status, which the API does not expose ([billing docs](https://ai.google.dev/gemini-api/docs/billing)). Hence the operator gate in §12.
- Free Tier inputs and outputs may be used by Google to improve products. That is acceptable only because every input is public open-source material.
- Request parameters are in [pilot_config.json](pilot_config.json):
  - `temperature 0`;
  - `thinkingConfig.thinkingLevel = low`;
  - `maxOutputTokens 8192`, because Gemini 3.x thinking tokens count toward the cap and the earlier 1024 risked truncated output;
  - JSON response mode.

---

## 11. PyJWT pilot development exemplar — **RESOLVED**

The before/after pair in [pilot_evidence_packet.md](pilot_evidence_packet.md) v0.2.0 is grounded in the bounded-task probe. The Molt engine reproduces it byte-for-byte from the manual reference rule (`tests/test_matcher_transformer.py::test_engine_reproduces_frozen_development_exemplar_exactly`).

Packet v0.2.0 changed only the output-format section (targeting `molt.rule.v2`) and corrected the "silently ignored" wording (§2).

---

## 12. Pilot execution status — **BLOCKED (external: operator must confirm Free Tier)**

[run_pyjwt_pilot.py](run_pyjwt_pilot.py) contacts the API only when **all** of these hold:

- no `--dry-run`;
- `GEMINI_API_KEY` is present, from the environment or an explicit `--env-file`; `.env` is never read implicitly;
- `--confirm-free-tier` is given;
- `MOLT_NO_NETWORK` is unset.

The runner then:

- validates each response with `jsonschema` against [rule_schema.json](rule_schema.json), plus Molt's semantic rules;
- never retries permanent 4xx errors;
- records `finishReason` / `MAX_TOKENS` truncation, the full usage metadata (missing fields stay `null`), latency, attempts and prompt hashes;
- writes **one new read-only file per run** to `measured_runs/`.

Cost is recorded as `null` (unknown) unless Free Tier was asserted. With the assertion it is recorded as `0.0` labelled `operator_assertion`.

From this repository, a key's billing status cannot be established. The pilot has therefore **not** been run. The single remaining command is:

```bash
.venv/bin/python experiments/run_pyjwt_pilot.py --env-file .env --confirm-free-tier
```

Run it only after confirming in Google AI Studio that the key's project is on the Free Tier (no billing account linked).

---

## 13. Numeric screening/attempt/retry/spend ceilings — **RESOLVED (labelled)**

Full values are in [ceilings.json](ceilings.json).

| Ceiling | Value | Label |
| --- | --- | --- |
| All model usage, entire project | **$0.00** | POLICY (hard constraint) |
| PyJWT pilot generation replicates | 2 | POLICY |
| Repair sweep | 1, 2, 3, 5 | POLICY |
| V1 repair cap | 3 | **PROVISIONAL** (selected at M5 by §5 rule) |
| Transport retries | 2 (429/5xx/transport only), 60 s timeout | POLICY |
| Free Tier rate figures used for request spacing | 15 RPM / 1500 RPD | PROVISIONAL (unverified) |
| Screening per migration | 20 repositories / 4 person-hours | PROVISIONAL |
| Screening total | 60 person-hours | PROVISIONAL |

---

## 14. Protocol integrity — **REGISTERED AT 0.5.0**

The SHA-256 digest of this file is recorded in [`protocol.hash`](protocol.hash):

```bash
shasum -a 256 experiments/protocol.md > experiments/protocol.hash
```

The following changes require a version bump, an amendment-log entry and a new hash:

1. RQs or their estimands.
2. Arms A–F or their information boundaries.
3. Admission, partition, split, audit or expansion rules.
4. The pinned model/provider or the $0 constraint.
5. The repair sweep, the §5 selection rule, or the frozen V1 cap once selected.
6. `molt.rule.v2` fields, edit kinds or semantics ([RULE_SPEC.md](../DOCS/RULE_SPEC.md)).
7. The evidence packet content.

Typographical corrections are noted in commit history only.

---

## 15. Admission, expansion and stop rules — **RESOLVED (POLICY; numbers PROVISIONAL)**

**Minimum oracle (admission) criteria.** All of these per repository:

- a pinned SHA;
- the unchanged suite passes on the old version in **3/3** consecutive runs, otherwise the repository is excluded as flaky, with a recorded reason;
- an attributable target-version failure in at least one in-scope site class;
- at least one existing test or frozen external probe exercising each in-scope site class present in the repository;
- no required secrets or services.

**Admission floor per migration:** ≥ **8** independent families admitted within the screening ceiling (20 repositories / 4 person-hours), giving ≥ 3 development + ≥ 5 held-out under §16. The target is 10–15. A migration below the floor is reported as feasibility-only and is not part of the main study.

**Add the next migration** in the registered order only if **all** hold:

- (a) it meets the admission floor within its ceiling;
- (b) its projected all-arm, all-replicate model requests fit within **80%** of the Free Tier daily request quota × a **5-day** execution window. The other 20% is the reserve. Money is never a lever;
- (c) it adds a tier or ambiguity role not already covered, or at least one additional required Tier 2 site class;
- (d) its oracle meets the minimum criteria.

**Stop expansion** at the first of:

- 6 migrations;
- two consecutive candidates in the order fail (a) or (d);
- the 60 person-hour total screening ceiling;
- Free Tier capacity exhausted, which means pause, never pay.

If fewer than 3 migrations meet the floor, the result is reported as a feasibility pilot, not V1. Every reduction is recorded **before** held-out outcomes are inspected.

**Run-level stop rules:**

- The M0 pilot stops on the first permanent API error, or after its configured replicates. No run is repeated to obtain a better output, and every run file is kept.
- The M5 repair loop stops at the budget or at a repeated rule hash.
- In held-out evaluation, every assigned run reaches a terminal status, with at most 2 identical infrastructure retries.

---

## 16. Split and audit sampling — **RESOLVED (POLICY)**

**Families.** Forks and mirrors, copied templates, and repositories sharing substantial migration-relevant code are grouped into one family. "Substantial" is PROVISIONAL: ≥ 50% of migration-relevant files byte-identical. The family is the independent unit.

**Split.**

- Per migration, with `N` admitted families: `n_dev = min(5, max(3, ceil(0.3 N)))`, held-out = `N − n_dev`, and held-out must be ≥ 5.
- Families are ordered by `sha256(f"20260924:{migration_id}:{family_id}")` ascending. The first `n_dev` go to development.
- A family already studied for rule design is forced into development. That increases `n_dev` if necessary, and the change is recorded.
- Seed: **20260924**.

**Audit sample (per migration × arm)**, ordered by `sha256(f"20260924:{site_or_repo_id}")`:

- all changed sites if ≤ 20, otherwise the first 20;
- the first 10 unchanged labelled candidate sites (lookalikes and abstentions);
- repository-level diff review of up to 10 repositories counted as successes.

**Rubric labels:**

- correct required edit;
- incorrect required edit;
- unnecessary/unrelated edit;
- missed required site;
- correct abstention;
- unknown.

**Reviewing:**

- Reviewers see diffs with arm labels removed where feasible.
- If a second person is available, they review a 20% subset. Disagreements are adjudicated and recorded. Otherwise the single-reviewer limitation is disclosed.
- An LLM judge is never the sole correctness oracle.
- Audit coverage is reported beside every audited metric.

---

## 17. DSL vs existing languages — **RESOLVED**

See [DOCS/DSL_FEASIBILITY.md](../DOCS/DSL_FEASIBILITY.md). It is a documented desk review of Comby, ast-grep and GritQL, plus executed engine evidence. The decision is to build a bounded LibCST substrate.

The feasibility is demonstrated by the M1 vertical slice:

- the reference rule migrates the synthetic PyJWT fixture from failing to passing under 2.10.1;
- the frozen exemplar is reproduced exactly.

Existing languages remain optional comparators for the RQ4 ablation (c).

---

## 18. Direct-arm exemplar design (Arm B) — **RESOLVED (POLICY)**

- **Count.** Exactly one exemplar per migration, identical for every Arm B repository and replicate. Arm A receives the same packet without it.
- **Selection at M7**, from development repositories only. Candidates are those whose manual reference migration is complete and passes verification.
  - Order them by `sha256(f"20260924:{migration_id}:{family_id}")`.
  - Choose the first that covers ≥ 1 site of every in-scope site class. If none covers all, choose the one covering the most classes, with ties broken by that order.
  - Held-out data is never consulted.
- **Content.** Changed hunks with ±5 lines of context, plus the unified patch, capped at 8,000 characters. Whole hunks are dropped in order to fit, and truncation is recorded.
- **Placement.** It sits in the stable prompt prefix after the shared evidence packet and before any repository-specific context.
- **Recorded.** Source SHA, path list, content SHA-256, and human preparation minutes (part of `S_B`).
- **Interim (PyJWT, until development repositories are admitted).** The probe-grounded exemplar in [pilot_evidence_packet.md](pilot_evidence_packet.md) serves as the frozen exemplar. It is replaced by the rule above at M7, with both hashes recorded.

---

## 19. M0 definition-of-done status (2026-09-24)

| DoD item | Status | Evidence |
| --- | --- | --- |
| Closest-prior-art + RuleFlow reviews | DONE | [RELATED_WORK.md](../DOCS/RELATED_WORK.md) |
| 6–8 candidate scorecards | DONE | [CANDIDATES.md](../DOCS/CANDIDATES.md), [candidates.json](candidates.json) (8) |
| Pilot feasibility evidence, reproducible | DONE (probe-level; no admitted repositories yet) | [probes/](probes/), [probe_run_20260923.json](probes/results/probe_run_20260923.json) |
| Pilot cost estimate | DONE as projection | [pilot_estimate.json](pilot_estimate.json) |
| **Measured pilot generation (2 replicates)** | **BLOCKED**: operator Free Tier confirmation | §12; runner tests in `tests/test_pilot_runner.py` |
| Final RQs/hypotheses + practical-threshold policy | DONE | §1 |
| Direct exemplar design | DONE (policy; interim PyJWT exemplar) | §18 |
| Caching policy | DONE | §6 |
| Repair-budget policy | DONE (sweep + selection rule); cap PROVISIONAL | §5 |
| Canonical executable rule schema | DONE | [RULE_SPEC.md](../DOCS/RULE_SPEC.md), [rule_schema.json](rule_schema.json), `tests/test_rule_schema.py` |
| Numeric expansion/stop, split and audit rules | DONE (numbers labelled PROVISIONAL) | §§15–16, [ceilings.json](ceilings.json) |
| DSL vs existing languages | DONE | §17 |
| Dated protocol + hash | DONE | this file, [protocol.hash](protocol.hash) |

**M0 is not closed** until the measured pilot run exists in `measured_runs/`, its values replace the projection's role in §8, and a dated amendment records the result.

---

## Amendment log

- **0.1.0 (2026-09-05):** Initial registration: candidate research, three feasibility probes, pilot selection and bounded scoping, tie-break/expansion ordering, unresolved-items list.
- **0.2.0 (2026-09-05):** Added §§10–13. Resolved the model/provider and the PyJWT exemplar; authored the evidence packet, config and projection.
- **0.3.0 (2026-09-10):** Formalised the v1 rule schema; set the V1 repair cap at 3; added the runner and §14.
- **0.4.0 (2026-09-10):** Pre-observation amendment to the Gemini Developer API Free Tier (`gemini-3.7-flash`) under the zero-cost constraint.
- **0.5.0 (2026-09-24):** Pre-observation amendment; no model output has been observed under any version.
  - Replaced the v1 schema with the executable `molt.rule.v2`: structured `replace_call`, typed values, closed objects, semantic validation. §§3, 9, 14, RULE_SPEC.
  - Evidence packet v0.2.0: output format retargeted to v2, and the "silently ignored" wording corrected (§2, §11).
  - Relabelled the V1 cap = 3 as PROVISIONAL, registered the M5 selection rule, and withdrew the unverified literature rationale (§5).
  - Added the practical-threshold policy (§1), numeric admission/expansion/stop rules (§15), split and audit policies (§16), the DSL feasibility note (§17) and the Arm B exemplar policy (§18).
  - Runner hardening: jsonschema validation, no retry on permanent 4xx, thinking config with `maxOutputTokens` 8192, immutable per-run files, cost recorded as unknown unless Free Tier is asserted, and the `--confirm-free-tier` gate. `.env` is never read implicitly.
  - Probes made reusable and re-run (§2).
  - M0 status table (§19): M0 remains open, blocked only on the measured pilot run.
