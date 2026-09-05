# Molt development and research roadmap

**Status:** planning only; no milestone is complete. The project contains this document, [README.md](../README.md), [RELATED_WORK.md](RELATED_WORK.md), and [GLOSSARY.md](GLOSSARY.md), with no implementation or benchmark artifacts. All module names, commands to be designed, artifacts, and gates below describe proposed work.

## Goal and implementation strategy

Build the smallest Python research system that measures when reusable LLM-authored migration logic beats repository-local patching in verified correctness, cost, and reliability, and what coverage is lost through deliberate constraints. The unit of reuse is a **versioned migration rule bundle for one specified dependency change**. A bundle can contain several composable primitive operations; it is not a separate patch per repository.

The experiment concerns unseen repositories for known migrations. It does not test generalization to unseen dependency changes. LLM-generated rules, declarative transformations, deterministic reuse, cross-project transfer, and iterative refinement are established ideas. The contribution sought is empirical evidence, including negative findings, for the four questions below.

Start with literature, a feasible migration, and manually authored rules. Build a deterministic engine before adding generation. Prove baseline reproducibility before allowing repair. Freeze the dataset and all method configurations before held-out evaluation. Product work waits until results are credible.

### Research questions and falsifiable hypotheses

| RQ | Proposed hypothesis and evidence that could refute it |
| --- | --- |
| **RQ1 — Reuse and correctness** | Shared rules may match or improve direct/exemplar patching in verified repository success and unrelated edits; lower success, more missed edits, or poorer reliability would limit this claim. Compare A–F per migration, including variability across generation replicates. |
| **RQ2 — Economics conditional on correctness** | Reuse may improve cost per verified success after sufficient deployment volume; realistic caching, fixed costs, verification, and lower success may eliminate any advantage. Report measured frontiers and no-crossover results. |
| **RQ3 — Repair transfer** | Repair on several development repositories may improve held-out success over the identical initial rule; development gains with flat or negative held-out deltas indicate overfitting or limited transfer. |
| **RQ4 — Price of constraint and matching evidence** | The bounded DSL may trade coverage for fewer incorrect/out-of-contract edits and smaller review burden. Measure its ceiling regardless of success. An optional metadata ablation may show fewer unrelated edits, no advantage, or excessive abstention compared with syntax-only matching. |

M0 must freeze estimands, practical effect thresholds where needed, hypotheses, analysis choices, and claim limits before evaluation. These are proposed hypotheses, not observed results or assertions of literature priority. Do not infer DSL causality solely from A–D: representation, search space, and workflow differ. Direct-arm comparisons plus expressibility labels characterize the trade-off; a causal representation comparison would need an additional controlled arm.

### Proposed organization

Create paths only as their phase needs them; do not scaffold empty services or an entire directory tree in advance.

```text
pyproject.toml                Python package, tools, and supported versions
src/molt/
  cli.py                      Thin local orchestration interface
  rules/                      Typed schema, validation, and canonical serialization
  transform/                  Fixed compiler, primitives, metadata, and edit reports
  inference/                  Evidence packets, prompts, model adapter, usage ledger
  verification/               Container execution and structured diagnostics
  repair/                     Bounded development-only rule revision
  benchmark/                  Manifests, partitions, experiment runner, metrics
  baselines/                  Regex, direct LLM, and official/expert adapters
  reporting/                  Tables, plots, and static report generation
tests/
  fixtures/                   Positive, negative, and ambiguous migration examples
  integration/                Engine, harness, and experiment-contract tests
migrations/<migration_id>/    Evidence, development examples, and versioned rules
benchmarks/                   Manifests, split metadata, exclusions, freeze records
containers/                  Reviewed build recipes and runtime policy
experiments/                  Protocol and budget configurations
artifacts/<run_id>/           Local raw outputs; large/sensitive data kept out of Git
reports/                     Sanitized release artifacts
DOCS/                        Methodology, rule specification, related work
```

Prefer one Python package and filesystem JSON/JSONL artifacts. No database, service mesh, job platform, or plugin marketplace is needed. Model adapters should expose only evidence-to-rule generation and usage accounting; a small direct baseline is a separate experiment arm.

A `console/` directory also exists, deliberately outside this research-artifact tree: a small static-HTML developer test harness (no build step, no server-side code) for visually inspecting the JSON/JSONL artifacts above as each phase's modules are built. It is explicitly not part of V1 and not a product UI — see [console/README.md](../console/README.md).

### Execution order and dependencies

Phases are work packages, not permission to postpone experimental design. Phase 0 first records a development-only feasibility protocol, then uses pilot evidence to close M0 and register expansion and budget-selection policies. Paid generation/repair pilots belong to later development phases; no such calls are authorized by this documentation pass. Phase 6 curation starts under that protocol alongside Phases 1–5; candidate discovery is not delayed until the engine is finished. Held-out implementation details remain inaccessible to rule developers.

```text
Phase 0 → Phase 1 → Phase 2 → Phase 3
                   Phase 2 → Phase 4
                   Phases 3 + 4 → Phase 5
Phase 0 → Phase 6 curation; Phase 4 → Phase 6 final admission/freeze
Phases 3 + 4 + 5 → Phase 7
Phases 5 + 6 + 7 → Phase 8 → Phase 9 → optional Phase 10
```

## Experiment contract

The following is the proposed protocol. M0 requires a dated, versioned registration with numeric budgets and selection rules; this roadmap alone is not evidence that registration has occurred.

### Dataset, partitions, and leakage control

- Investigate at least 6–8 migration candidates. Pilot approximately three migrations (Tier 1 anchor, meaningful Tier 2, ambiguity/DSL ceiling), initially about 3–5 development repositories per pilot migration: 9–15 total if feasible. The preferred final target is 4–6 migrations with approximately 10–15 admitted independent repositories **in total per migration**, including development; prefer 5–6 if affordable. A declared three-migration reduced study is acceptable. At M0 register the expansion rule below, exact split/rounding policy, and family-level seeded assignment. No final migration count or identity is frozen by this document.
- Use Tier 1 for name/import/argument changes, Tier 2 for structural call or argument rearrangements, and Tier 3 for behavioral changes requiring broader reasoning. Include at least one migration with necessary Tier 2 edits and report mixed-tier cases explicitly. Include an ambiguity-sensitive case and a simple calibration case. Bound the selected API task before admission; classify every required site inside it, including DSL-unsupported/Tier 3 spillover. Do not exclude those sites or admitted repositories to improve Molt scores. Broader Tier 3 support is deferred, with screening losses disclosed.
- Pre-register discovery queries, search dates, population boundaries, maximum screening effort, inclusion/exclusion reasons, and replacement rules. Record every screened repository. Do not select cases based on whether Molt can already fix them.
- Require a pinned SHA with genuine affected API usage, a reproducible old-version install, a nonempty unchanged test suite that passes, and an attributable failure after the standardized upgrade. Use a frozen external API probe when existing tests do not expose the break. A no-op upgrade that passes without evidence of a required change is not a primary migration case.
- Exclude under recorded rules: unavailable artifacts, unresolved baseline failures, required production secrets/services, irreducible flakiness, no targeted API usage, or licensing/access restrictions that prevent the planned evaluation. Weak coverage is documented; it cannot be repaired by silently replacing the original suite. Pre-register repeated baseline runs and a fixed flake policy.
- Group forks, mirrors, copied templates, and substantial shared migration-relevant code. Prevent family overlap across splits. Record overlap across migrations too; repeated repositories are not independent samples.
- A curation role may screen and containerize held-out repositories using a fixed checklist. It must not send held-out code, probes, failures, or suggestive summaries to rule authors or prompts. This is a data-access role, not a requirement for another agent or a platform. Separate directories/access, curation logs, and immutable manifests provide the minimum audit trail. If one researcher has already studied a repository for rule design, assign it to development.
- Development repositories may guide generation, repair, and candidate selection. No held-out source, diagnostics, patches, or outcomes may change Molt's schema, engine, prompts, rules, thresholds, or budgets. Quarantine accidental exposure; record it and follow the pre-registered replacement policy before evaluation. Exposure after freeze requires a disclosed new experiment version, not silent replacement.
- Include a low-exposure, obscure, or sufficiently recent migration if feasible. Record release dates, public examples/codemods, exposure proxies, model identity, and any disclosed training cutoff. Obscurity and recency do not guarantee absence from training data. If no qualifying migration meets viability criteria, publish the search evidence and limitation before freezing; do not label the dataset contamination-free.

### Shared environment and correctness contract

Every method starts from the same clean checkout and receives the same standardized target-dependency environment. The harness supplies the dependency-manifest/lockfile delta, records the full resolved dependency closure, and verifies the installed target version. It should hold other dependencies fixed where possible and disclose unavoidable transitive changes. Dependency installation is not part of the transformation DSL.

Use four separate records per repository: **old-version baseline**, **unmodified target-version failure**, **method patch**, and **target-version verification**. The same test commands, external probes, resource limits, and typecheck policy apply to every arm. Existing tests, test collection settings, verification configuration, and target dependency pins cannot be modified by any method. Reject patches that disable tests, change the target version, add diagnostic suppressions, or write outside allowed production Python source paths. Cases requiring test migration lie outside this initial benchmark and must be visible in screening statistics.

The primary binary outcome is **verified repository success**: a policy-compliant patch that satisfies the migration oracle, parses, installs/builds as applicable, passes the unchanged existing suite and external migration probes, and passes all pre-registered required typechecks. A passing suite alone is insufficient. Repository-level abstention, unresolved required edits, invalid rules, forbidden edits, and method timeouts are non-successes. Correctly declining to edit an unrelated lookalike is a true negative, not a repository failure.

Freeze repository-specific typecheck applicability during admission. Preserve required existing checks. Require Pyright in a predefined applicable cohort with a passing old-version configuration and usable type information. For other repositories, report Pyright diagnostics as exploratory or `not applicable`, never as a pass or an exclusion invented after results. Distinguish newly introduced diagnostics from baseline diagnostics; do not relax settings per method.

External probes and gold patches are evaluation-only and immutable after freeze. During development, separate public diagnostic probes may help repair. A direct LLM may run existing tests and the same class of public diagnostics in its assigned repository; final private probes remain hidden from every method. Human audit supplements these executable outcomes and can overturn an apparent success. Report the executable-contract success count separately from audit-confirmed success in the reviewed cohort; the primary headline must disclose audit-discovered errors and audit coverage. Apply the same audit policy to all arms and report cost per success under both the executable and audited definitions where denominators are justified. Never call unreviewed sites audit-confirmed.

After dataset freeze, keep every assigned instance in the primary denominator. Separate method failures from infrastructure failures and allow only identical retries under a frozen infrastructure policy. Report unresolved infrastructure cases as non-successes in the conservative primary rate and show a clearly labeled evaluable-only sensitivity analysis. Never improve a score through post-outcome exclusions.

### Experimental arms, information, and budgets

| Arm | Frozen input and behavior |
| --- | --- |
| A — Direct LLM | Public migration evidence, dependency delta, verification contract, and assigned repository; repository-local inspect/edit/test loop, no repository-specific development exemplar. |
| B — Direct LLM + exemplar | Exactly A plus one frozen development before/after example and migration patch per migration. No additional repository-specific exemplar or solution archive. |
| C — Molt without repair | Initial generated shared bundle for each replicate; invalid initial output remains a failed rule. |
| D — Molt with repair | Same initial proposal as C, then development-only rule repair under the selected proposal cap. |
| E — Regex/text | Transparent ordered substitutions authored on development evidence, frozen before held-out use. |
| F — Official/expert | Pinned available tool/recipe/configuration; report unavailable comparators explicitly, with no invented failure score. |

The common public evidence packet contains the same migration guide/API contracts and generic examples for every arm. Separately inventory repository-specific development examples: Molt may use the designated development set; B gets exactly one selected exemplar; A gets none. This intentional difference is part of the reuse treatment. Freeze B's selection policy at M0 (for example, a qualifying complete migration selected by a recorded development-only ordering), then its source SHA, allowed context, patch, provenance, and content hash at M7. Disclose preparation and authoring costs, including any LLM use. Do not select the exemplar using held-out performance or silently copy an expert tool into Molt's inputs.

Use the same pinned base model/provider configuration for A–D, with declared task-specific output formats and budgets. Both direct arms start each repository/replicate with fresh source and conversation, under the same model, tools, prompts except the exemplar, and numeric request/token/time budgets. They may inspect **only the assigned held-out repository** and run its existing tests/public diagnostics. They must not access hidden probes, other held-out results or patches, Molt outcomes, later upstream fixes, or unlogged network retrieval. The frozen evidence packet replaces uncontrolled web search. Shared cached prefixes are permitted; accumulated solution memory is not. C/D make no held-out model calls. All methods use clean target-upgrade checkouts and the same edit/verification contract.

### Development-set repair policy

Evaluate **1, 2, 3, and 5 total proposals**, including the initial proposal, during development pilots. M0 registers the sweep, pilot spend ceiling, selection criterion for diminishing returns (including minimum useful improvement/cost threshold), and how ties/early stopping are handled. M3–M5 supply measured generation/verification costs and outcomes; M5 selects the numeric V1 cap, then M7/M8 freezes it before any held-out evaluation. Do not choose a budget using held-out outcomes. If the sweep is infeasible, disclose a development-only protocol amendment and weaker budget justification before freeze.

Use paired prefixes of the same development proposal trajectory where possible, selecting among candidates available at each budget; this avoids confounding budget with unrelated initial generations. Count malformed outputs, refusals, formatting retries, and every model request. Exposed reasoning/output limits, context, elapsed time, and transport retries must also be capped. Charge billed failures. Register independent generation replicate counts against pilot costs; repeated application of one rule is not a generation replicate.

Repair changes rule data only. Reapply every candidate from clean trees to the full development set; never edit the engine, tests, pins, or repository files inside the repair loop. Freeze candidate selection: policy/schema validity, development repository success, fewer audited/fixture unsafe edits, fewer abstentions, then earliest proposal. Required safety fixtures must pass; no eligible rule yields a failed-rule artifact. Save the untouched initial proposal for C even when D later succeeds. Human repairs and manual prototypes are labeled diagnostics, not autonomous results.

Measure paired development and held-out deltas for every replicate/migration, including repositories helped and harmed, overfitting, unchanged results, and rule costs. Direct and rule budgets need not have identical request counts; report practical cost–success sensitivity rather than claiming equal work from equal calls.

### Metrics and analysis plan

| Measure | Operational definition |
| --- | --- |
| Repository success | Successful repositories / all frozen assigned repositories, reported per migration and arm; include counts and confidence intervals. |
| Syntax, install/build, typecheck | Separate stage results with applicability denominators and diagnostic deltas. An unrun stage is never a pass. |
| Existing tests | Repository-level all-tests pass fraction plus collected/passed/failed/skipped counts; detect collection loss or newly skipped tests. |
| Migration correctness | External probe outcomes and a stratified manual sample of changed and unchanged affected sites. Passing tests is only an executable proxy. |
| False positives / missed edits | Audit incorrect or unnecessary edits and missed required changes separately. Report incorrect edits / audited edits as an edit-error fraction, not a population false-positive rate without labeled negatives. Include negative-control fixture results and repository incidence. |
| Model use | Every call, input/output and cache/reasoning tokens where reported, model/config identity, failures, and billed cost using a dated price schedule. Missing usage is unavailable, not zero. |
| Runtime / repair | Wall time and CPU/resource observations for generation, application, verification, setup, and total; proposal counts and accepted revisions. |
| Transfer / difficulty | Development versus held-out results, repaired versus identical unrepaired initial rules, and Tier 1/Tier 2/mixed outcomes. |
| Scale economics | Primary: cost per verified success, plus marginal, cumulative, amortized, LLM-only and full cost, and observed/projected break-even. Failures and abstentions contribute cost. |
| Coverage and constraint | Independently labeled required sites expressible in the frozen DSL / all labeled required sites; unsupported-site rate, observed coverage, applicability, and abstention reported separately. |
| Rule validity and burden | Schema-valid proposals / all proposals; incorrect and out-of-contract edit counts/rates, canonical size, operation/capture count, nesting depth, and optional blinded reviewer time. |
| Migration variance | Per-migration counts, success/cost/repair/error outcomes and spread; macro averages with equal migration weight alongside explicitly weighted pooled results. |

Pre-register an audit sample size or deterministic sampling fraction, seed, correctness rubric, and treatment of disagreements. Sample across migrations, arms, reported successes, failures, abstentions, and unchanged candidate sites. Blind reviewers to method labels where practical; record adjudications and use a second reviewer on a subset if available. Do not use an LLM judge as the sole correctness oracle. If audit resources are limited, reduce claim strength and disclose the limitation rather than implying exhaustive correctness.

Use repository families as the independent unit. Report per-migration binomial intervals when independence is defensible, and paired differences via a family-level paired bootstrap with its seed and method recorded. Do not pool all files or calls as independent observations or infer ecosystem-level generality from a small purposively selected migration set. Repository resampling does not measure uncertainty over unseen migrations. Model-generation replicates must use independently generated bundles; applying one bundle to 20 repositories is not 20 rule-generation replicates. M0 must register the replicate-selection policy and affordable minimum; finalize numeric counts from development costs at M7, explicitly limiting conclusions if only one is affordable. Report family-level uncertainty conditional on each frozen bundle and generation variability separately; repositories sharing a bundle are not independent samples of synthesis ability.

### Site labels and optional matching ablation

Create an evaluation inventory of required migration sites and unrelated lookalikes independently of any method's matches. An edit at a required site can still be wrong; label correct required edits, incorrect required edits, missed required edits, and unrelated changes separately. A wrong edit both fails to resolve the requirement and contributes an edit error. Record stable source spans and coupled edits as one logical site under a frozen rubric to avoid inflating counts. Audit changed **and unchanged** sites for all arms.

Report required sites changed correctly / required sites as site recall/coverage, missed or incorrectly resolved required sites / required sites as missed-edit rate, and unrelated sites changed / labeled unrelated candidates as false-positive rate only when that negative denominator is known. Also report unrelated/incorrect edits per audited edit and per-repository incidence, explicitly named. Do not mix these denominators or equate site precision with repository success. Unknown labels stay unknown; sampling estimates need sampling weights/uncertainty, not full-population claims.

For expressibility, reviewers classify required sites against the frozen DSL using a documented rubric and, where feasible, a witness rule or explicit missing capability. Separate formalism-unsupported cases from unresolved semantic evidence, implementation bugs, and generation misses. Report unsupported / required sites, expressible / required sites, and unknown proportions with bounds; successful generation is not the definition of expressibility. No required site disappears because Molt never matched it. Report site and repository abstention separately; a no-match is not necessarily a deliberate abstention. Required-site abstentions remain misses/non-successes. Audit/reviewer time is optional and cannot establish human usability without an actual study.

**Optional but strongly recommended RQ4 ablation:** apply identical frozen primitive operations using (a) `QualifiedNameProvider` + `ScopeProvider` and conservative ambiguity handling, and (b) name/syntax-only matching in the same engine. Keep rule, operations, file scope, scheduling, and oracle fixed; do not independently regenerate rules for the two variants. Where feasible add (c) equivalent Comby/Ast-Grep/GritQL rules; document semantic mismatches and report only the equivalence-controlled subset as such, with omitted cases visible.

Pre-register aliased imports, `from x import y as z`, local shadowing, multiple receivers with the same method name, relative imports, re-exports, star imports, ambiguous receiver types, and identical attributes from unrelated libraries. Use both a frozen adversarial fixture suite and applicable repository sites; do not pool fixtures as independent repositories. Count required sites changed/missed, unrelated sites changed, abstentions, and repository success. Lexical metadata is not full receiver-type, alias, or data-flow analysis. A finding of no useful metadata advantage, or better precision with unacceptable coverage loss, is valid. M0 chooses feasibility criteria; any decision to omit the ablation is recorded before M8, narrowing RQ4 to the mandatory constraint study.

### Economics and prompt caching

For each migration and direct arm separately, retain the descriptive simple model:

```text
C_direct(n) = nL
C_Molt(n)   = R + nD
equality at n = R / (L - D), provided L > D
first strictly cheaper integer n = floor(R / (L - D)) + 1
```

`R` includes all generation and repair proposals, including failures; use separate setup totals for C and D. Pilot tuning/engineering costs are disclosed separately from the deployment model, never erased from the project-cost ledger. `L` includes direct retries and failures; `D` measures deterministic application. Show LLM-only expenditure and compute-priced application separately before combining monetary units. Report a full-cost model as well:

```text
C_direct_full(n) = S_direct + sum(L_i + V_direct_i)
C_Molt_full(n)   = S_Molt + R + V_dev + sum(D_i + V_Molt_i)
```

`S` is method-specific setup, `V_dev` is rule-development verification, and `V_*_i` is per-repository verification cost. For direct arms, non-LLM tool execution/compute is itemized within `V_direct_i` alongside verification; for Molt, application compute is `D_i`, and all development checking is `V_dev`. `S_B` includes exemplar preparation. Setup includes fixed provisioning, evidence preparation, and any priced engineering effort; do not charge variable costs twice. Shared dataset curation is reported separately; human rule/baseline engineering time is disclosed rather than hidden in token prices. This evaluates deployment to `n` additional repositories after rule development; development cost cannot disappear because development repositories were also tested.

Plot observed cumulative costs under predeclared seeded repository orders and show uncertainty. Show marginal increments and cumulative cost divided by repository count as well as cost per verified success. Reordering recorded requests does not reproduce counterfactual cache hits: keep the measured order as the observed curve, label reordered fixed-ledger curves as conditional accounting, and model alternative cache histories explicitly in sensitivity analysis. Never regenerate a rule for each point on the same amortization curve. If cost lines do not cross, say so; extrapolations beyond the observed sample are labeled projections. Compare at the same frozen repository population and report correctness alongside costs. A method with lower success is not established as better by a lower bill.

The primary economic estimand is `C_method(n) / K_method(n)`, where `K` is verified successful repositories among the **same n assigned repositories**. Report success counts/rates beside both LLM-only and full-cost ratios; when `K = 0`, report “no finite cost per verified success,” never zero. Include every failed attempt, retry, unresolved case, and abstention in expenditure; quantify spend on each status. No fallback patching is silently credited to Molt. A combined rule-then-agent workflow would be a separate arm with all costs charged.

The constant-mean equations assume comparable monetary units, a reusable frozen rule, stationary marginal costs, and a fixed deployment population. They ignore success differences, variable verification work, and cache warm-up/expiry. In an illustrative constant-success model, costs per success scale as `(R+nD)/(n*p_Molt)` versus `L/p_direct`; equality of raw bills does not imply equality of these ratios. Use measured cumulative curves and success counts as primary evidence. Pareto comparisons require considering success and error rates, not just the cheapest ratio. Any noninferiority margin must be justified and frozen at M0; otherwise report descriptive frontiers without declaring equivalent correctness.

Use provider prompt caching under realistic available settings. Put shared migration evidence in an identical stable prefix where possible, and B's frozen exemplar in its stable prefix before variable repository context. Do not disable caching, intentionally bust cache keys, or pad prompts to advantage an arm. Freeze provider cache settings/retention where exposed, scheduling/concurrency, and treatment of cold/warm runs; cache-prefix hashing must not include hidden outcomes. Record timestamps and run order because hits can depend on timing and prefix eligibility. Separate measured caching results from modeled cold/warm sensitivity; do not assert every repeated prefix hits.

For every request record **uncached input tokens, cached input tokens, output tokens, reasoning tokens where exposed, actual billed cost, model/provider, and price schedule date**, plus cache-write/retention fees if applicable. Avoid double-counting reasoning tokens already included in billed output. Keep estimated costs labeled and reconcile to billing where available; missing usage/billing is unavailable, not zero. If caching cannot be controlled or measured reliably, disclose this and bound the cost claim. Exact provider policy and prices must be checked at model selection; no provider, price, or cache lifetime is assumed here.

## Phase 0 — Literature, Candidate Feasibility & Experimental Design

**Objective and rationale:** Close M0 with evidence for a feasible, fair study before building the engine. This documentation revision does not close M0 or authorize benchmark execution/model calls.

**Deliverables:**

- Refresh [RELATED_WORK.md](RELATED_WORK.md): BigBag, SPELL, MELT, Allain et al., Cummins, RuleFlow, and Google first; retain earlier synthesis, infrastructure, and evaluation context. Resolve the additional direct-agent leads. Record paper versions, primary-source evidence, unknowns, and scoped distinctions; RuleFlow's economics review is mandatory.
- Development-only feasibility protocol followed by candidate scorecards for **at least 6–8 candidates**, with exact version deltas/API scope, release evidence, Tier 1/2/3 mix, ambiguity opportunity, DSL-ceiling risk, independent client supply, install effort, oracle strength, expert-tool coverage, exposure proxies, and rejection reasons. No preset winner or PyJWT+pandas pair.
- Approximately three pilot migrations representing the anchor, structural, and ambiguity/ceiling roles, with initially 3–5 development clients each if feasible. Record old-pass/target-fail feasibility, admission person-hours and compute, flakiness, test/probe strength, and proposed required-site expressibility. Source-only estimates are labeled estimates; no claim that these repositories are already admitted.
- Pilot cost estimate including both direct arms, independent generation replicates, the 1/2/3/5 repair sweep, expert setup, full verification, curation, audit, and failure reserve. Initial model costs can be projections; replace with measured development costs at M3–M7 before expansion/freeze. Do not treat six arms as six equivalent paid-agent loops.
- A dated `experiments/protocol.md` and budget configuration when this phase is executed: final RQ1–RQ4 hypotheses, estimands, practical thresholds, selection/expansion/split rules, audit sample/rubric, direct/exemplar policy, cache policy, proposal-budget selection policy, model/replicate/time/spend limits, stopping/amendment rules, and self-review or reviewer record.

### Candidate investigations, not selections

**Investigated 2026-09-05 — see [DOCS/CANDIDATES.md](CANDIDATES.md) for the full evidence-backed scorecards** (primary-source citations plus three real old-pass/new-fail reproductions). The table below is retained as the original planning-stage framing; it is superseded by CANDIDATES.md wherever the two differ.

| Candidate | Scientific role to assess and specific admission risk | Investigation outcome |
| --- | --- | --- |
| [PyJWT 1→2](https://pyjwt.readthedocs.io/en/stable/changelog.html) | Possible Tier 1 anchor, including bounded argument changes; algorithm/security intent cannot be guessed from a missing argument. Return-type behavior may exceed a simple rule. No assumed zero matching advantage. | **Recommended pilot (anchor).** Old-pass/new-fail reproduced; bounded to exception rename + options-dict restructuring, excluding `algorithms=` value selection. |
| [pandas 1→2, bounded API removal](https://pandas.pydata.org/docs/whatsnew/v2.0.0.html) | Assess structural calls and colliding names separately from behavioral/dtype changes. SPELL's pandas→polars case does not decide version-upgrade feasibility. Keep only a justified bounded task; disclose unsupported spillover. | Expansion candidate (second-wave Tier 2). Real ambiguity risk confirmed (`.append()`); not probed this pass. |
| [Pydantic 1→2](https://docs.pydantic.dev/latest/migration/) | Structural validators/configuration and ambiguous methods can test the DSL ceiling. [bump-pydantic](https://github.com/pydantic/bump-pydantic) provides a comparator. Some deprecated APIs still work; require an actual break. Lexical metadata alone may not resolve model receivers. | **Recommended pilot (ambiguity/DSL-ceiling).** Probe confirmed the "some deprecated APIs still work" risk directly: `.dict()`/`Config`/`GenericModel` are warning-only, not breaks; `BaseSettings` import is a genuine break. Task bounded accordingly. |
| [NumPy 1→2](https://numpy.org/doc/2.0/numpy_2_0_migration_guide.html) | Removed APIs and alias/shadowing cases; Ruff NPY201 is an expert lead. Separate source migration from binary ABI and dtype/behavior changes. | Expansion candidate (Tier 1, strong Ruff NPY201 comparator confirmed). Not probed this pass. |
| [HTTPX `app=` removal](https://github.com/encode/httpx/releases/tag/0.28.0) | Explicit transport construction may offer bounded Tier 2 work; test-only usage can fail the production-source admission contract. | Expansion candidate, pending production-source screening — the admission risk named here is real and unresolved. |
| [SQLAlchemy, bounded 1.4→2.0 API change](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html) | Assess a narrow structural surface such as `select` argument form. Database/service setup and transaction behavior may dominate; reject on evidence, not reputation. | **Recommended pilot (meaningful Tier 2).** Old-pass/new-fail reproduced for `select([cols])`→`select(cols)`; confirmed DB-free at construction time, lowering setup difficulty. |
| Recent/low-exposure breaking release, exact library/version to discover | Seek a clear release/API delta, viable clients, and strong oracle. Recency is an exposure proxy, not proof of training absence. An unnamed slot does not count as a completed scorecard. | **Filled: pandas 2.x→3.0** (released 2026-01-21, at/after Claude's disclosed training cutoff). Expansion candidate; supply is the open risk (too recent for many adopted clients). |
| [attrs modernization](https://www.attrs.org/en/stable/names.html), or another discovered candidate | Both API families exist; modernization without a breaking upgrade fails admission. Replace this lead if no genuine target failure is found. | **Rejected on direct evidence** — old and new attrs APIs coexist permanently, no break exists. **Replaced by urllib3 1→2** (expansion candidate; Tier 1 bounded slice, direct-vs-transitive usage is the open admission risk). |

Expert codemod availability is not a veto. Distinguish a scientifically trivial task that adds little experimental contrast from a useful migration with a strong comparator. Selection optimizes diversity, credible failure evidence, and reproducibility, not expected Molt wins. Count distinct bounded migration tasks honestly; do not inflate diversity by splitting one rename family into many nominal migrations.

### Pre-registered expansion rule

At M0 fill numeric screening/person-hour/spend ceilings, minimum oracle criteria, family counts/split proportions, and a contingency reserve using the pilot estimate. Rank candidates by recorded supply, admission burden, oracle quality, diversity, and budget; freeze tie-breaking. Start from the approximately three-migration pilot. Add the next qualifying migration only when its projected **all-arm, all-replicate, verification and audit** cost fits the remaining ceiling/reserve, independent admitted supply can support roughly 10–15 total clients under the split rule, and it improves diversity without weakening admission. Stop at the registered ceiling, exhausted viable supply, or six migrations. Prefer five or six; four is within the target. Choose three as a reduced study if expansion fails, recording the reason before held-out outcomes are inspected.

Complete M7 development cost measurements before closing M6 when they affect affordability; M6 and M7 can progress together, and both precede M8. Expansion may use those development-only updates and held-out curation counts under the access policy; it must not use held-out method outcomes or Molt's held-out applicability. Freeze exact dataset/counts at M6 and method/budgets at M7/M8. If even three migrations cannot meet the contract, report a feasibility pilot or pause; do not call it completed V1. Do not fill quotas with forks or weak oracles. This rule bounds environment maintenance rather than making it the project.

**Definition of done — M0:** Closest-prior-art and RuleFlow reviews, 6–8 completed candidate scorecards, pilot repository feasibility evidence, pilot cost estimate, final RQs/hypotheses, direct exemplar design, caching policy, repair-budget policy, and numeric benchmark expansion/stop rule are linked to a dated protocol/hash. The complete benchmark and V1 repair cap remain pending their designated evidence gates.

**Progress (2026-09-05):** Literature review — done pre-existing. Eight candidate scorecards — **done**, see [CANDIDATES.md](CANDIDATES.md), including three real old-pass/new-fail reproductions (not just documentation). Pilot selection — **done** (PyJWT/SQLAlchemy/Pydantic, each with an explicit bounded task scope). A first, dated protocol slice — **done**, see [experiments/protocol.md](../experiments/protocol.md). **Still open, by design:** numeric screening/spend ceilings, pilot repository identities/SHAs (Phase 6 has not started), model/provider selection, exemplar identity, the V1 repair cap, and a real dollar-figure pilot cost estimate — the protocol explicitly declines to fabricate these without measured evidence. M0 is therefore **not closed**.

**Decisions / dependencies:** No prior gate. Development-only feasibility precedes implementation. Before M0 closes, compare the planned small DSL with existing languages and record why implementing a bounded LibCST substrate is feasible for these RQs. Keep unsupported cases as outcomes; do not expand the grammar indefinitely to make every candidate fit.

**Not yet:** Engine scaffolding, transformations, full benchmark runs, model tuning, or product infrastructure. Later paid development pilots require the registered budget and their phase prerequisites.

**Risks / questions:** Repository admission, direct-agent cost, weak oracles, and Tier 2 expressibility may constrain the study. Resolve these with evidence and reduce scope before outcomes rather than claiming architectural distinctiveness.

## Phase 1 — Typed Migration Rule System

**Objective and rationale:** Define exactly what a model is allowed to express and what evidence authorizes an edit before building a transformer.

**Deliverables:**

- `rules/schema.py`, `rules/validation.py`, and `DOCS/RULE_SPEC.md`: strict versioned Pydantic models, exported JSON Schema, canonical serialization/hash, examples, and structured rejection reasons.
- A discriminated union for `rename_symbol`, `change_import`, `rename_argument`, `add_argument`, `remove_argument`, and restricted `replace_call`; implement only primitives needed by selected migrations first.
- A rule envelope with dependency/version applicability, ordered operation IDs, imported-symbol targets, typed captures, preconditions, explicit postconditions, provenance, and unsupported-case policy.
- Fixtures for valid composition and rejection of unknown fields, arbitrary code, executable predicates, path-specific patches, undefined captures, inconsistent version ranges, conflicts, and excessive rule size/depth.

**Definition of done:** All valid reference rules round-trip canonically; every prohibited example fails before execution. Manual fixtures establish which selected task sites are expressible and which are unsupported; meaningful Tier 2 expressibility is demonstrated without requiring complete coverage of every selected migration. The schema identifies unsupported behavior rather than offering a raw-code escape hatch.

**Decisions / dependencies:** Requires M0. Use typed literals, qualified symbols, and captured CST subtrees as replacement values, not unrestricted Python strings. No `eval`, generated visitor classes, filesystem operations, or shell commands. Set finite capture/operation limits and a stable schema version. `replace_call` maps arguments and captures rather than replacing arbitrary statements.

**Not yet:** LLM integration, repository execution, general-purpose language design, `wrap_expression`, or broader attribute rewriting.

**Risks / questions:** A DSL that cannot express meaningful Tier 2 edits may trivialize the experiment. A DSL that permits arbitrary expressions may merely disguise executable patch generation. Resolve this tradeoff with concrete development fixtures.

## Phase 2 — Deterministic LibCST Transformation Engine

**Objective and rationale:** Prove that manually authored rule data can reliably produce bounded edits; generation cannot compensate for an unsound compiler.

**Deliverables:**

- `transform/compiler.py`, `metadata.py`, `primitives.py`, and `report.py`: lower validated operations to fixed LibCST visitors; emit diffs, matches, changed spans, abstentions, and rejection reasons.
- Alias-aware and scope-aware matching with LibCST matchers, `QualifiedNameProvider`, and `ScopeProvider`; explicit handling of symbol source and multiple candidates.
- Dry-run output and transactional repository application: validate every transformed file before publishing the patch; no partial writes on error. Make source-root discovery and symlink/path boundaries explicit.
- A fixture matrix covering import aliases, dotted imports, local shadowing, conditional imports, relative imports/re-exports, star imports, unrelated same-named calls, receiver ambiguity, positional/keyword arguments, `*args`/`**kwargs`, duplicate keywords, already-migrated code, multiline formatting, comments, encoding/newlines, and interacting operations. Every case has either an exact expected patch or a documented abstention.
- At least one manually authored bundle applied unchanged to three independent development repositories, with before/after diffs and local checks. Container-level reproducibility is a later gate.

**Definition of done — M1:** A manual rule passes the positive, negative, formatting, and ambiguity suite; applying it twice changes nothing on the second pass; repeated fresh runs produce identical patches. Required fixtures show no unrelated edits.

**Definition of done — M2:** That same bundle handles the required migration sites in at least three independent development repositories without repository names, per-file exceptions, or source patch overrides. Record any abstentions and manual correctness review. This establishes engineering reuse, not held-out performance.

**Decisions / dependencies:** Requires Phase 1. Match conservatively: a candidate set that includes unrelated identities does not authorize an edit. Defer unresolved re-exports and dynamic receivers. For ordered operations, recompute metadata after each pass and define conflict rejection; do not match against stale names after import changes. Preserve argument evaluation count and order; removing a side-effecting argument or duplicating/reordering captured calls requires evidence unavailable to the basic DSL and should abstain.

Pyright starts as a verifier. Its documented JSON output contains diagnostics, not complete per-expression binding facts. If a selected migration truly needs type-assisted matching, add a narrow adapter to an existing supported interface, pin it, and test source-position/type mapping; otherwise abstain. Do not assume LibCST's type-inference facilities are a Pyright bridge. [Pyright CLI](https://github.com/microsoft/pyright/blob/main/docs/command-line.md), [LibCST metadata](https://libcst.readthedocs.io/en/latest/metadata.html).

**Not yet:** Generated executable transformers, custom type inference/language server, custom code-property graph, broad semantic rewrites, or automatic commits.

**Risks / questions:** Formatting preservation is not a semantic guarantee. Import collisions, indirect bindings, and evaluation order can make superficially simple edits unsafe. Too much abstention can destroy coverage; measure it rather than guessing.

## Phase 3 — LLM Rule Inference

**Objective and rationale:** Replace manual rule authoring with a constrained generation step while preserving the engine boundary and measuring its actual cost.

**Deliverables:**

- `inference/evidence.py`, `prompts.py`, `client.py`, and `usage.py`: one pinned model configuration initially, evidence assembly, schema-constrained response parsing, raw-response retention, and cost ledger.
- Versioned migration evidence packets: source URLs/content hashes, old/new API contracts, release notes, permitted development before/after examples, negative cases, and the rule schema.
- Tests with recorded responses for malformed JSON, unknown operations, refusals, truncation, unsupported schema versions, and absent usage fields. Separate unit tests from paid live experiments.
- An end-to-end recorded generation attempt that validates, compiles, and applies using only the fixed primitive library.

**Definition of done — M3:** At least one unedited model response expresses a valid, nontrivial migration bundle and passes required development fixtures. All unsuccessful attempts are also retained and charged. Record validity and success rates across the registered pilot attempts; a selected example is not the aggregate result.

**Decisions / dependencies:** Requires M1 and M2. Prefer a constrained provider response mode where available, but always validate locally. A human may curate versioned evidence before freeze, not silently repair the model output. Treat repository/docs content as untrusted data; it cannot change orchestration instructions or tools. No model calls occur during deterministic held-out application.

**Not yet:** Fine-tuning, provider sweeps, retrieval/vector infrastructure, autonomous repository-specific patching in Molt, or repair.

**Risks / questions:** Valid JSON may contain an incorrect rule; limited DSL expressiveness and incomplete evidence must be distinguishable from model inference errors. Record evidence preparation effort.

## Phase 4 — Repository Baseline + Container Verification

**Objective and rationale:** Attribute outcomes to migration behavior rather than broken environments and make the same checks reproducible for all arms.

**Deliverables:**

- `verification/environment.py`, `runner.py`, `diagnostics.py`, and reviewed `containers/` recipes.
- Per-repository manifest fields for URL, commit SHA, license/access status, Python/platform, image digest, old/new dependency closure and hashes, setup commands, test collection expectations, build command, timeouts, required checks, and source edit allowlist.
- Separate old-version and target-version records, structured stage status, installed-version evidence, patch hashes, stdout/stderr artifact references, and resource accounting.
- Small integration cases for install failure, timeout, test failure, invalid syntax, wrong dependency version, changed test collection, forbidden patch paths, and missing artifacts. Failures are classified without rewriting their meaning.

**Definition of done — M4:** At least three development repositories reproduce a passing old baseline, an attributable unmodified target failure, and a successful manual-rule migration in two fresh container runs. All registered commands and required checks run; equal patch/check outcomes and differing runtime measurements are reported separately. Every intentional harness failure yields the expected status and cleanup.

**Decisions / dependencies:** Requires M2 and Phase 0's contract; can progress alongside Phase 3. Use isolated disposable checkouts and unprivileged containers with resource/time limits. Do not mount credentials, the host Docker socket, or unrelated workspace paths. Restrict installation network access to the recorded artifact sources; run verification offline where feasible. Keep cached artifacts immutable and identify cold versus warm setup. Containers reduce exposure but are not a security proof for hostile code.

**Not yet:** Kubernetes, cloud fleets, remote services, production credentials, dependency updates performed by the LLM, or a universal packaging-system abstraction.

**Risks / questions:** Archived wheels, native extensions, architecture differences, transitive dependency drift, and tests needing external services may make candidate supply the bottleneck. Record supported host/container architecture and narrow the benchmark honestly.

## Phase 5 — Bounded Rule Repair

**Objective and rationale:** Test whether development failures improve the shared rule, rather than allowing a system to accumulate one-off repository fixes.

**Deliverables:**

- `repair/controller.py` and `feedback.py`: explicit state machine for proposal, validation, clean application, verification, candidate selection, and terminal status.
- Bounded feedback packets containing current rule, development diagnostics, relevant source snippets, fixture counterexamples, and structured abstention reasons; record truncation policy and token costs.
- Rule lineage with parent/child hashes, all rejected candidates, fixture outcomes, full development outcomes, best-rule selection, and independent initial-rule artifacts.
- Paired no-repair/repaired pilot evaluation from identical initial proposals and development fixtures that detect regression, cycles, and budget exhaustion.

**Definition of done — M5:** The controller enforces each registered pilot cap (1/2/3/5) and the subsequently selected V1 cap, never edits repository files directly, never reads held-out artifacts, and rechecks the full development set from clean trees. A paired pilot quantifies improvement, no change, or harm and marginal returns by proposal budget under the same verification contract; the numeric V1 cap is selected by M0 policy and frozen before held-out evaluation. An improvement claim requires observed positive evidence; a documented null/negative result can close the implementation gate and must remain in the report.

**Decisions / dependencies:** Requires M3 and M4. Only rule data can vary during a repair run. Engine/schema fixes are engineering work outside the loop and require a new development experiment version. Detect repeated rule hashes and stop early. Return the best eligible candidate under the frozen rule, not merely the last response. Invalid/no-safe-rule outcomes remain failures.

**Not yet:** Held-out adaptation, per-repository exceptions, unbounded retries, multi-agent critics, or human correction counted as autonomous success.

**Risks / questions:** Repair can overfit a small development set or trade precision for coverage. M5 measures development behavior; held-out paired evaluation at M8 is required to claim transfer.

## Phase 6 — Benchmark Dataset Construction

**Objective and rationale:** Build an auditable set of actual migration tasks with known baseline health and independent held-out clients.

**Deliverables:**

- `benchmarks/candidates.jsonl`, `exclusions.jsonl`, `repositories.jsonl`, `splits.json`, and migration cards with difficulty/exposure evidence.
- Frozen original tests and independent migration probes; hashes of environment inputs, source SHAs, family assignments, manifests, and setup patches. Gold patches, if used for audit, stay outside method inputs.
- An admission report showing the screening funnel, original failures, eligible population, chosen sample, split seed, family deduplication, test coverage, and reasons for every exclusion.
- A dataset freeze record containing exact IDs, counts, hashes, access rules, and protocol version. Keep large clones/images outside source control; retain retrievable provenance and permitted artifacts.

**Definition of done — M6:** The M0 expansion rule yields the declared final scope: preferably 4–6 migrations and approximately 10–15 total independent admitted repositories each, or a predeclared three-migration reduced study. Counts and development/held-out splits follow the registered feasibility decision, not held-out outcomes. Every admitted repository meets the baseline and target-failure contract, has reproducible environment evidence, and belongs to one family partition. Necessary Tier 2 edits are represented in both development and held-out sets. The exposure objective has explicit evidence or the predeclared contamination-feasibility limitation. No method outcome was used to choose held-out instances.

**Decisions / dependencies:** Curation starts after M0; final admission requires M4. If the population falls short, record the bottleneck and use a pre-evaluation protocol amendment or pause the full V1 claim. Do not fill the target count with forks, no-op cases, or broken baselines. Dataset freeze is separate from the method freeze at Phase 8.

**Not yet:** Hundreds of shallow migrations, non-Python repositories, synthetic repositories presented as independent real clients, or public release of private artifacts.

**Risks / questions:** Old-version viability can bias toward maintained/simple projects. Report the screened population and exclusions so readers can judge that bias. Repository count alone does not establish migration diversity.

## Phase 7 — Baseline Implementations

**Objective and rationale:** Make the comparison strong enough to test the hypothesis instead of rewarding Molt for favorable setup or a weak direct baseline.

**Deliverables:**

| Arm | Proposed implementation and control |
| --- | --- |
| E — Regex/text | `baselines/regex.py`: transparent ordered substitutions developed only on development examples, with frozen patterns and identical file scope. No hidden AST analysis. |
| A — Direct LLM | `baselines/direct_llm.py`: bounded repository-local inspect/edit/test loop, public migration evidence, fresh context per repository, frozen tools/prompts/budgets, caching, and complete patches/usage. |
| B — Direct LLM + exemplar | Same adapter and settings as A, plus exactly one development exemplar/patch frozen per migration; record its selection, provenance, hash, and preparation cost. |
| D — Molt + repair | Frozen generated bundle selected using development results only; per-repository execution has no LLM calls. |
| F — Official/expert codemod | `baselines/expert.py`: pinned tool/version/recipe/configuration and provenance, same target upgrade and checks. If unavailable, record `not available`, not a failed run. Any custom expert comparator is independently authored from development evidence with effort disclosed. |
| C — Molt without repair | The exact same initial bundle for each generation replicate, applied even if later revisions outperform it; invalid initial bundles score as failures. |

- A shared benchmark result schema and adapter interface for patch, stages, status, usage, and provenance.
- Development smoke runs plus contract checks for clean resets, equivalent environments, private-probe isolation, forbidden edits, and honest timeout/usage reporting. Keep the manual rule prototype as a labeled diagnostic reference if useful.

**Definition of done — M7:** All required available arms execute through the same harness on development repositories and export comparable records. The direct baseline demonstrably inspects relevant source and uses allowed diagnostics; tooling faults are resolved before freeze. Missing official/expert availability is evidenced per migration. Every arm's settings and budgets are fixed for the chosen expansion scope, including exemplar hashes, caching/scheduling policy, replicate counts, chosen repair cap, and the pre-outcome decision on optional matching ablation. Development costs update the expansion affordability estimate before dataset/method freeze.

**Decisions / dependencies:** Requires M3, M4, and M5 for the complete comparison; can start adapters earlier. Use the same migration packet, target dependency delta, production-source write scope, and final oracle. Allow differences inherent to the methods, then disclose them. Official codemods cannot be quietly copied into Molt prompts; if exposed as input, that assistance must be a declared condition.

**Not yet:** Many model leaderboards, deliberate under-budgeting of direct patching, hand-fixing one arm's output, or held-out solution memory in either direct arm. B's frozen development exemplar remains explicitly permitted.

**Risks / questions:** Prompt quality, repository context retrieval, and unequal retries can dominate results. Record budget curves/sensitivity within the registered budget; do not tune a baseline after seeing held-out scores.

## Phase 8 — Frozen Held-Out Evaluation

**Objective and rationale:** Measure transfer after all opportunities to adapt rules, tools, and selection criteria have ended.

**Deliverables:**

- A method freeze manifest containing engine/schema commit, initial and repaired rule hashes, evidence/prompt hashes, baseline versions/patterns, exemplar hashes, cache policy, ablation conditions, model IDs/settings, budgets, seeds, and dataset/protocol hashes.
- `benchmark/runner.py` with partition guards, immutable input validation, seeded run order, per-arm clean resets, resumable artifact indexing, and explicit infrastructure retry records.
- Raw patch and verification artifacts for every assigned repository/arm/replicate, including invalid proposals, abstentions, exhausted budgets, and infrastructure failures. Evaluation-only probe output is quarantined from method feedback.

**Definition of done — M8:** Every frozen assigned run reaches a terminal recorded status. Hash checks confirm no post-hoc changes to rules, engine, prompts, dataset, or evaluation conditions. No held-out result influenced Molt rule development. The initial/repaired pairing is intact, and every missing outcome has an explicit classification.

**Decisions / dependencies:** Requires M5, M6, and M7. Revalidate frozen inputs before each resumed run. Use only predeclared identical infrastructure retries; a semantic/harness defect requiring edits invalidates the affected experiment version. Preserve its results and disclose a separately versioned rerun—do not silently rerun only failures. Direct repository-local adaptation is allowed only within its frozen policy and cannot feed Molt.

**Not yet:** Rule repair on held-out failures, post-hoc exclusions, new model selection, altered probes, or presenting a rerun as an untouched first evaluation.

**Risks / questions:** Model service drift and intermittent infrastructure can break reproducibility. Record provider version metadata, request timestamps, cached responses where permitted, and deviations; reproducible artifacts do not guarantee identical future model outputs.

## Phase 9 — Analysis & Research Report

**Objective and rationale:** Turn frozen evidence into an honest answer about accuracy, transfer, and economics, including the limits of the experiment.

**Deliverables:**

- `benchmark/metrics.py` and `reporting/`: deterministic result aggregation, audit joins, confidence intervals, cost models, and reproducible static HTML/tables/plots.
- Per-migration success and stage breakdowns; paired repair effects; tier and exposure breakdowns; audit results; failure taxonomy; development/held-out gaps; raw counts and denominators.
- LLM calls/tokens/cost, generation/application/verification/runtime components, marginal and amortized cost curves, observed or projected break-even counts, and sensitivity to prices, success rates, setup, and repository ordering.
- A report with method, protocol deviations, prior-art discussion, limitations, reproduction instructions, artifact manifest, licenses/attribution review, and sanitized example diffs. No production integration is required.

**Definition of done — M9:** All summary values reconcile to raw records; a clean analysis rerun reproduces tables and figures; the pre-registered audit is complete; figures distinguish measured from projected costs. README status and supported setup instructions match the actual implementation. Release artifacts have been reviewed for secrets and redistribution permissions, and a second person or documented independent rerun checks the reproduction procedure.

**Decisions / dependencies:** Requires M8. Keep audited correctness distinct from test-based success. Report no crossover or no repair benefit plainly. Explain that even 4–6 selected migrations limit power and external validity; a three-migration study needs explicit reduced-scope claims and cannot estimate ecosystem-wide migration variance reliably. Human setup and expert-codemod effort are not free merely because they produce no model tokens.

**Not yet:** Marketing claims of universal safety, production readiness, ecosystem-wide superiority, or a dashboard built instead of an analysis.

**Risks / questions:** Small samples, partial oracles, selection bias, model contamination, and shared repository families can produce misleading confidence. Surface them with their practical effect on conclusions.

## Phase 10 — Optional Post-V1 Productization

**Objective and rationale:** Consider usability work only after the research identifies a repeatable use case and an acceptable correctness/coverage boundary.

**Deliverables:** A separate decision memo, based on M9 evidence, prioritizing at most one next step: broader migration coverage, improved local review/CLI, additional semantic support, or an explicitly requested integration.

**Definition of done:** An explicit go/no-go decision links proposed work to evidence, user need, maintenance burden, and measurable acceptance criteria. This phase is optional and is not part of V1 completion.

**Decisions / dependencies:** Requires M9. Reliable negative findings may justify more research or stopping. Any later repository write/PR automation requires a separately designed review and authorization workflow.

**Not yet by default:** React/SaaS dashboards, authentication, billing, GitHub Apps or automatic production PRs, multi-language engines, custom code-property graphs/language servers, ML confidence models, vector databases, Kubernetes, or a large multi-agent architecture. Completing V1 does not automatically authorize them.

**Risks / questions:** Product infrastructure can conceal weak research evidence. Do not let a polished interface substitute for transformation correctness.

## Milestone gates

**No gate is complete.** M0 has a documentation/literature start; feasibility and registration remain open. M1–M9 are not started. Gate closure requires linked artifacts, not a progress percentage.

| Gate | Required evidence |
| --- | --- |
| M0 — Feasibility and methodology registered | Closest work/RuleFlow review; 6–8 scorecards; pilot feasibility/cost; RQ1–RQ4; exemplar/caching/repair policies; numeric expansion/stop/split/audit rules and protocol hash. **Partial (2026-09-05):** scorecards ([CANDIDATES.md](CANDIDATES.md)) and pilot selection ([experiments/protocol.md](../experiments/protocol.md)) done; numeric ceilings, real cost estimate, and provider/model selection still open. |
| M1 — Manual rule reliable | Strict schema and deterministic, idempotent, conservative fixture results for a manual rule. |
| M2 — Reuse demonstrated | One unchanged manual bundle correctly handles required sites in at least three independent development repositories. |
| M3 — Constrained inference demonstrated | An unedited LLM bundle validates and passes development fixtures; complete attempt and cost records retained. |
| M4 — Verification reproducible | Old-pass/target-fail/migrated-pass reproduced twice in fresh containers for at least three development repositories; harness failures correctly classified. |
| M5 — Repair policy resolved | 1/2/3/5 development budget evidence, selected numeric V1 cap, paired initial/repaired results and costs; no held-out access. |
| M6 — Dataset frozen | Scope determined by M0 expansion rule (preferred 4–6 migrations × roughly 10–15 total clients; declared three-migration reduction allowed); exact SHAs, partitions, oracles, exclusions, and hashes. |
| M7 — Baselines ready | Shared-harness smoke results and frozen configurations for all required available arms, with comparator gaps documented. |
| M8 — Held-out run complete | Every assigned run terminal, immutable inputs verified, complete failure ledger, and no post-hoc rule changes. |
| M9 — Results ready for release | Audited metrics and cost curves reconcile with raw artifacts; clean report reproduction and release review complete. |

M5 deliberately separates **testing repair** from **proving repair helps**. A null finding must not force endless tuning. Likewise M9 does not require Molt to outperform the direct baseline. Methodological completion and a favorable hypothesis result are different outcomes.

## What constitutes V1 complete

V1 is complete when M0–M9 have evidence, and all of the following hold:

- The engineering substrate enforces the frozen grammar and tested deterministic/idempotent application; required-site expressibility and unsupported cases are measured rather than requiring every migration to be expressible.
- LLM rule generation, the development-selected repair cap, and the paired no-repair arm are evaluated without hand-edited output; invalid proposals and null/negative repair transfer remain in results.
- The declared expansion outcome meets its pre-evaluation scope, with independent partitions, a simple anchor, meaningful Tier 2, ambiguity/ceiling evidence, pinned SHAs, passing originals, attributable failures, and exposure documentation. A three-migration reduction is labeled explicitly.
- A–E and available F comparators complete the same frozen verification protocol, including direct patching both without and with the frozen exemplar, realistic caching, and complete failures/abstentions.
- RQ1–RQ4 results report verified repository success, cost per verified success, cumulative cost, development→held-out repair transfer, unrelated/missed edits, abstention/coverage, DSL unsupported-site rate, and migration-to-migration variance with explicit denominators. Optional matching/reviewer studies are completed or their predeclared omission narrows claims. No positive effect is required.
- The static research report explains the limits of the claims, accounts for protocol deviations, and supports a clean reproduction path. No product service is required.

An undeclared feasibility-only pilot is not a completed V1 study; a three-migration evaluation can be V1 only under the registered reduced-scope contract. If viable population, budget, or oracle quality makes this scope infeasible, publish a dated protocol amendment **before held-out method outcomes are inspected** and explicitly name the reduced scope. Never revise a target retroactively to turn an incomplete experiment into a completed one.

## Immediate next work

**Partially complete as of 2026-09-05:** the candidate leads were turned into 8 evidence-backed scorecards ([CANDIDATES.md](CANDIDATES.md)) and an approximately-three-migration development pilot was chosen by a recorded rubric (registered in [experiments/protocol.md](../experiments/protocol.md)). **Still remaining to close M0:** a real (not projected) admission/oracle/direct-baseline cost estimate, which requires either measured Phase 6 curation effort or a small priced pilot — neither has been authorized or performed. Numeric screening/spend ceilings and the final expansion stop rule remain open for the same reason. This must precede committing to the full primitive set or LLM integration.

## Decision status after this documentation pass

**Fixed design commitments:** research framing and proposed RQ1–RQ4; six-arm comparison including the exemplar; known breaking Python upgrades; common dependency delta/oracle; development-only repair and family separation; zero held-out Molt LLM calls; caching-aware correctness-conditioned economics; mandatory constraint/error/coverage reporting; negative results retained; staged feasibility before benchmark freeze. These commitments are not a completed numeric pre-registration.

**Intentionally unresolved:** final count/splits and numeric expansion ceilings; provider/model/prices/cache settings; direct and rule budgets/replicates; chosen 1/2/3/5-derived repair cap; exemplar; exact DSL semantics (including two capability questions this pass's research newly surfaced — list-to-positional unwrapping and string-literal targeting, see [experiments/protocol.md §9](../experiments/protocol.md#9-explicitly-unresolved-carried-forward-not-newly-opened)); audit resources/practical thresholds; whether the metadata/external-language ablations and reviewer study are feasible. **Updated 2026-09-05:** a recommended three-migration pilot with bounded task scopes is now registered (PyJWT, SQLAlchemy, Pydantic — see [CANDIDATES.md](CANDIDATES.md) and [experiments/protocol.md](../experiments/protocol.md)); repository SHAs remain unresolved because Phase 6 curation has not started. Resolve the rest at the specified gates using development/curation evidence only. No implementation or benchmark execution follows automatically from editing these documents.
