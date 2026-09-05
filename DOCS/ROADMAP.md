# Molt development and research roadmap

**Status:** planning only; no milestone is complete. The project currently contains this document and [README.md](../README.md), with no implementation or benchmark artifacts. All module names, commands to be designed, artifacts, and gates below describe proposed work.

## Goal and implementation strategy

Build the smallest Python research system that can test whether LLM-generated, constrained migration rules transfer across independent repositories more accurately and cheaply than direct LLM patching. The unit of reuse is a **versioned migration rule bundle for one specified dependency change**. A bundle can contain several composable primitive operations; it is not a separate patch per repository.

The experiment concerns unseen repositories for known migrations. It does not test generalization to unseen dependency changes. Neither reusable codemods nor learning edits from examples is claimed as a new invention.

Start with literature, a feasible migration, and manually authored rules. Build a deterministic engine before adding generation. Prove baseline reproducibility before allowing repair. Freeze the dataset and all method configurations before held-out evaluation. Product work waits until results are credible.

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

### Execution order and dependencies

Phases are work packages, not permission to postpone experimental design. Phase 0 fixes selection and evaluation rules before pilot work. Phase 6 curation starts under that protocol alongside Phases 1–5; candidate discovery is not delayed until the engine is finished. Held-out implementation details remain inaccessible to rule developers.

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

- Select two dependency migrations with exact old/new versions and a bounded API surface. Target 15–30 admitted independent repositories **in total per migration**, including development and held-out repositories. Reserve approximately one third for development and two thirds for held-out evaluation, using a recorded seeded assignment at repository-family level. Freeze exact rounding and stratification at M0.
- Use Tier 1 for name/import/argument changes, Tier 2 for structural call or argument rearrangements, and Tier 3 for behavioral changes requiring broader reasoning. Include at least one migration with necessary Tier 2 edits and report mixed-tier cases explicitly. Do not select only trivial renames or quietly include unsupported Tier 3 tasks.
- Pre-register discovery queries, search dates, population boundaries, maximum screening effort, inclusion/exclusion reasons, and replacement rules. Record every screened repository. Do not select cases based on whether Molt can already fix them.
- Require a pinned SHA with genuine affected API usage, a reproducible old-version install, a nonempty unchanged test suite that passes, and an attributable failure after the standardized upgrade. Use a frozen external API probe when existing tests do not expose the break. A no-op upgrade that passes without evidence of a required change is not a primary migration case.
- Exclude under recorded rules: unavailable artifacts, unresolved baseline failures, required production secrets/services, irreducible flakiness, no targeted API usage, or licensing/access restrictions that prevent the planned evaluation. Weak coverage is documented; it cannot be repaired by silently replacing the original suite. Pre-register repeated baseline runs and a fixed flake policy.
- Group forks, mirrors, copied templates, and substantial shared migration-relevant code. Prevent family overlap across splits. Record overlap across the two migrations too; repeated repositories are not independent samples.
- A curation role may screen and containerize held-out repositories using a fixed checklist. It must not send held-out code, probes, failures, or suggestive summaries to rule authors or prompts. This is a data-access role, not a requirement for another agent or a platform. Separate directories/access, curation logs, and immutable manifests provide the minimum audit trail. If one researcher has already studied a repository for rule design, assign it to development.
- Development repositories may guide generation, repair, and candidate selection. No held-out source, diagnostics, patches, or outcomes may change Molt's schema, engine, prompts, rules, thresholds, or budgets. Quarantine accidental exposure; record it and follow the pre-registered replacement policy before evaluation. Exposure after freeze requires a disclosed new experiment version, not silent replacement.
- Include a low-exposure, obscure, or sufficiently recent migration if feasible. Record release dates, public examples/codemods, exposure proxies, model identity, and any disclosed training cutoff. Obscurity and recency do not guarantee absence from training data. If no qualifying migration meets viability criteria, publish the search evidence and limitation before freezing; do not label the dataset contamination-free.

### Shared environment and correctness contract

Every method starts from the same clean checkout and receives the same standardized target-dependency environment. The harness supplies the dependency-manifest/lockfile delta, records the full resolved dependency closure, and verifies the installed target version. It should hold other dependencies fixed where possible and disclose unavoidable transitive changes. Dependency installation is not part of the transformation DSL.

Use four separate records per repository: **old-version baseline**, **unmodified target-version failure**, **method patch**, and **target-version verification**. The same test commands, external probes, resource limits, and typecheck policy apply to every arm. Existing tests, test collection settings, verification configuration, and target dependency pins cannot be modified by any method. Reject patches that disable tests, change the target version, add diagnostic suppressions, or write outside allowed production Python source paths. Cases requiring test migration lie outside this initial benchmark and must be visible in screening statistics.

The primary binary outcome is **verified repository success**: a policy-compliant patch that satisfies the migration oracle, parses, installs/builds as applicable, passes the unchanged existing suite and external migration probes, and passes all pre-registered required typechecks. A passing suite alone is insufficient. Repository-level abstention, unresolved required edits, invalid rules, forbidden edits, and method timeouts are non-successes. Correctly declining to edit an unrelated lookalike is a true negative, not a repository failure.

Freeze repository-specific typecheck applicability during admission. Preserve required existing checks. Require Pyright in a predefined applicable cohort with a passing old-version configuration and usable type information. For other repositories, report Pyright diagnostics as exploratory or `not applicable`, never as a pass or an exclusion invented after results. Distinguish newly introduced diagnostics from baseline diagnostics; do not relax settings per method.

External probes and gold patches are evaluation-only and immutable after freeze. During development, separate public diagnostic probes may help repair. A direct LLM may run existing tests and the same class of public diagnostics in its assigned repository; final private probes remain hidden from every method. Human audit supplements these executable outcomes and can overturn an apparent success in a separately reported audited measure.

After dataset freeze, keep every assigned instance in the primary denominator. Separate method failures from infrastructure failures and allow only identical retries under a frozen infrastructure policy. Report unresolved infrastructure cases as non-successes in the conservative primary rate and show a clearly labeled evaluable-only sensitivity analysis. Never improve a score through post-outcome exclusions.

### Repair and method budgets

Default Molt budget: **three rule proposals total per migration and generation replicate: one initial proposal plus at most two revisions**. Malformed proposals count. Each proposal is one model request; do not hide formatting retries or extra agents. Transient transport retries are separately capped, recorded, and charged whenever billed. Freeze token, context, time, and transport limits at M0.

Repair is development-only and changes the rule data, never repository files, engine primitives, tests, or dependency pins. Every revision is reapplied from clean starting trees to the full development set. Select the best candidate by a frozen ordering: policy/schema validity, development repository success count, fewer audited/fixture unsafe edits, fewer abstentions, then earliest proposal. Safety fixtures must pass; if none qualify, return an explicit failed-rule artifact. Development gains are a selection signal, not evidence of held-out improvement.

Save the initial proposal for the no-repair ablation. An invalid initial proposal remains a recorded failure for that arm even if a revision becomes valid. Do not hand-edit generated JSON in either LLM arm. Manual rule prototypes are engineering diagnostics, not substitutes for generated rules in reported scores.

The direct baseline generates repository-specific patches using the same pinned model and migration evidence packet (including permitted development examples), plus its assigned repository. It starts with fresh context per repository and cannot reuse a rule or solution learned from other attempts. Give it meaningful source inspection and execution tools; freeze its own numeric per-repository request/token/time limits and retry policy at M0. Compare both under declared practical budgets; identical request counts are not equivalent work, so report cost-versus-success sensitivity rather than asserting budget equality.

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
| Scale economics | Marginal cost per additional repository, cumulative and amortized cost, break-even estimate with uncertainty, and cost per verified success. |

Pre-register an audit sample size or deterministic sampling fraction, seed, correctness rubric, and treatment of disagreements. Sample across migrations, arms, reported successes, failures, abstentions, and unchanged candidate sites. Blind reviewers to method labels where practical; record adjudications and use a second reviewer on a subset if available. Do not use an LLM judge as the sole correctness oracle. If audit resources are limited, reduce claim strength and disclose the limitation rather than implying exhaustive correctness.

Use repository families as the independent unit. Report per-migration binomial intervals when independence is defensible, and paired differences via a family-level paired bootstrap with its seed and method recorded. Do not pool all files or calls as independent observations or generalize uncertainty over two migrations to the Python ecosystem. Model-generation replicates must use independently generated bundles; applying one bundle to 20 repositories is not 20 rule-generation replicates. M0 must fix replicate counts against budget and explicitly scope conclusions if only one is affordable.

For each migration, retain the simple model:

```text
C_direct(n) = nL
C_Molt(n)   = R + nD
equality at n = R / (L - D), provided L > D
first strictly cheaper integer n = floor(R / (L - D)) + 1
```

`R` includes all generation and repair proposals, including failures. `L` includes direct retries and failures; `D` measures deterministic application. Show LLM-only expenditure and compute-priced application separately before combining monetary units. Report a full-cost model as well:

```text
C_direct_full(n) = S_direct + sum(L_i + V_direct_i)
C_Molt_full(n)   = S_Molt + R + V_dev + sum(D_i + V_Molt_i)
```

`S` is method-specific setup, `V_dev` is rule-development verification, and `V_*_i` is per-repository verification cost. Shared dataset curation is reported separately; human rule/baseline engineering time is disclosed rather than hidden in token prices. This evaluates deployment to `n` additional repositories after rule development; development cost cannot disappear because development repositories were also tested.

Plot observed cumulative costs under seeded repository orders and show uncertainty. Never regenerate a rule for each point on the same amortization curve. If cost lines do not cross, say so; extrapolations beyond the observed sample are labeled projections. Compare at the same frozen repository population and report correctness alongside costs. A method with lower success is not established as better by a lower bill.

## Phase 0 — Literature Review & Experimental Design

**Objective and rationale:** Establish a defensible contribution, viable migration candidates, and a protocol that cannot be rewritten to favor the implementation.

**Deliverables:**

- `DOCS/RELATED_WORK.md`: a primary-source comparison of REFAZER, LASE/systematic editing, Meditor, OpenRewrite/Moderne, GritQL, Piranha, Comby, Rector, and SWE-bench/SWE-agent. Start with the [linked sources in the README](../README.md#research-positioning), then search specifically for LLM-authored codemods and rule repair. Record search date, evidence, overlaps, and unresolved novelty questions.
- `experiments/protocol.md` and a machine-readable budget configuration: hypotheses, outcome definitions, selection policy, leakage rules, audit sampling, statistical plan, model/replicate budgets, stop rules, and amendment procedure.
- Candidate scorecards with exact version deltas, release documentation, API exposure, Tier 2 opportunity, expected repository supply, install feasibility, contamination risk, and official/expert codemod availability. Shortlist more than two before final selection.
- A small development-only feasibility screen and a recorded choice of two migrations. No particular dependency is selected by this roadmap.

**Definition of done — M0:** A dated protocol and hash exist; numeric budgets and screening limits are filled in; two candidates have evidence of viable client populations and old/new-version behavior on pilot repositories; all required prior art has been compared. Record reviewers or explicitly identify a self-review. Distinguish a preliminary feasibility estimate from the final dataset count.

**Decisions / dependencies:** No earlier phase. Freeze selection methodology now; freeze exact admitted SHAs at M6. If a candidate later proves infeasible, follow the registered replacement rule before viewing held-out method outcomes. Compare the small DSL with an existing transformation language; proceed with the LibCST plan only with a written scope/implementation rationale.

**Not yet:** Engine implementation, model tuning, large-scale crawling, full benchmark runs, or claims of being the first.

**Risks / questions:** Is there a Tier 2 migration with enough independently testable clients? Does an established tool already answer most of the contribution? If novelty narrows, refine the experiment rather than invent a superiority claim.

## Phase 1 — Typed Migration Rule System

**Objective and rationale:** Define exactly what a model is allowed to express and what evidence authorizes an edit before building a transformer.

**Deliverables:**

- `rules/schema.py`, `rules/validation.py`, and `DOCS/RULE_SPEC.md`: strict versioned Pydantic models, exported JSON Schema, canonical serialization/hash, examples, and structured rejection reasons.
- A discriminated union for `rename_symbol`, `change_import`, `rename_argument`, `add_argument`, `remove_argument`, and restricted `replace_call`; implement only primitives needed by selected migrations first.
- A rule envelope with dependency/version applicability, ordered operation IDs, imported-symbol targets, typed captures, preconditions, explicit postconditions, provenance, and unsupported-case policy.
- Fixtures for valid composition and rejection of unknown fields, arbitrary code, executable predicates, path-specific patches, undefined captures, inconsistent version ranges, conflicts, and excessive rule size/depth.

**Definition of done:** All valid reference rules round-trip canonically; every prohibited example fails before execution. Manual rules can express both selected migration designs or a documented design revision is made using development evidence only. The schema identifies unsupported behavior rather than offering a raw-code escape hatch.

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

**Definition of done — M5:** The controller enforces three total proposals, never edits repository files directly, never reads held-out artifacts, and rechecks the full development set from clean trees. A paired pilot quantifies improvement, no change, or harm under the same verification contract. An improvement claim requires observed positive evidence; a documented null/negative result can close the implementation gate and must remain in the report.

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

**Definition of done — M6:** Two migrations each have 15–30 viable independent repositories, approximately one third development and two thirds held-out under M0's rounding rule. Every admitted repository meets the baseline and target-failure contract, has reproducible environment evidence, and belongs to one family partition. Necessary Tier 2 edits are represented in both development and held-out sets. The exposure objective has explicit evidence or the predeclared contamination-feasibility limitation. No method outcome was used to choose held-out instances.

**Decisions / dependencies:** Curation starts after M0; final admission requires M4. If the population falls short, record the bottleneck and use a pre-evaluation protocol amendment or pause the full V1 claim. Do not fill the target count with forks, no-op cases, or broken baselines. Dataset freeze is separate from the method freeze at Phase 8.

**Not yet:** Hundreds of shallow migrations, non-Python repositories, synthetic repositories presented as independent real clients, or public release of private artifacts.

**Risks / questions:** Old-version viability can bias toward maintained/simple projects. Report the screened population and exclusions so readers can judge that bias. Repository count alone does not establish migration diversity.

## Phase 7 — Baseline Implementations

**Objective and rationale:** Make the comparison strong enough to test the hypothesis instead of rewarding Molt for favorable setup or a weak direct baseline.

**Deliverables:**

| Arm | Proposed implementation and control |
| --- | --- |
| Regex/text | `baselines/regex.py`: transparent ordered substitutions developed only on development examples, with frozen patterns and identical file scope. No hidden AST analysis. |
| Direct LLM | `baselines/direct_llm.py`: bounded repository-local inspect/edit/test loop, shared model/evidence, fresh context per repository, frozen tools/prompts/budgets, and complete patches/usage. |
| Molt + repair | Frozen generated bundle selected using development results only; per-repository execution has no LLM calls. |
| Official/expert codemod | `baselines/expert.py`: pinned tool/version/recipe/configuration and provenance, same target upgrade and checks. If unavailable, record `not available`, not a failed run. Any custom expert comparator is independently authored from development evidence with effort disclosed. |
| Molt without repair | The exact same initial bundle for each generation replicate, applied even if later revisions outperform it; invalid initial bundles score as failures. |

- A shared benchmark result schema and adapter interface for patch, stages, status, usage, and provenance.
- Development smoke runs plus contract checks for clean resets, equivalent environments, private-probe isolation, forbidden edits, and honest timeout/usage reporting. Keep the manual rule prototype as a labeled diagnostic reference if useful.

**Definition of done — M7:** All required available arms execute through the same harness on development repositories and export comparable records. The direct baseline demonstrably inspects relevant source and uses allowed diagnostics; tooling faults are resolved before freeze. Missing official/expert availability is evidenced per migration. Every arm's settings and budgets are fixed.

**Decisions / dependencies:** Requires M3, M4, and M5 for the complete comparison; can start adapters earlier. Use the same migration packet, target dependency delta, production-source write scope, and final oracle. Allow differences inherent to the methods, then disclose them. Official codemods cannot be quietly copied into Molt prompts; if exposed as input, that assistance must be a declared condition.

**Not yet:** Many model leaderboards, deliberate under-budgeting of direct patching, hand-fixing one arm's output, or cross-repository solution memory in the direct arm.

**Risks / questions:** Prompt quality, repository context retrieval, and unequal retries can dominate results. Record budget curves/sensitivity within the registered budget; do not tune a baseline after seeing held-out scores.

## Phase 8 — Frozen Held-Out Evaluation

**Objective and rationale:** Measure transfer after all opportunities to adapt rules, tools, and selection criteria have ended.

**Deliverables:**

- A method freeze manifest containing engine/schema commit, initial and repaired rule hashes, evidence/prompt hashes, baseline versions/patterns, model IDs/settings, budgets, seeds, and dataset/protocol hashes.
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

**Decisions / dependencies:** Requires M8. Keep audited correctness distinct from test-based success. Report no crossover or no repair benefit plainly. Explain that two migrations and a small held-out set limit statistical power and external validity. Human setup and expert-codemod effort are not free merely because they produce no model tokens.

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

All gates begin **not started**. Gate closure requires linked artifacts, not a progress percentage.

| Gate | Required evidence |
| --- | --- |
| M0 — Methodology frozen | Dated protocol/hash, numeric budgets, candidate feasibility, selection/split/audit plan, and prior-art comparison. |
| M1 — Manual rule reliable | Strict schema and deterministic, idempotent, conservative fixture results for a manual rule. |
| M2 — Reuse demonstrated | One unchanged manual bundle correctly handles required sites in at least three independent development repositories. |
| M3 — Constrained inference demonstrated | An unedited LLM bundle validates and passes development fixtures; complete attempt and cost records retained. |
| M4 — Verification reproducible | Old-pass/target-fail/migrated-pass reproduced twice in fresh containers for at least three development repositories; harness failures correctly classified. |
| M5 — Repair effect measured | Bounded rule-only controller and paired development evidence of improvement, no effect, or harm; no held-out access. |
| M6 — Dataset frozen | Two migrations, each with 15–30 viable independent repositories; exact SHAs, partitions, oracles, environments, exclusions, and hashes. |
| M7 — Baselines ready | Shared-harness smoke results and frozen configurations for all required available arms, with comparator gaps documented. |
| M8 — Held-out run complete | Every assigned run terminal, immutable inputs verified, complete failure ledger, and no post-hoc rule changes. |
| M9 — Results ready for release | Audited metrics and cost curves reconcile with raw artifacts; clean report reproduction and release review complete. |

M5 deliberately separates **testing repair** from **proving repair helps**. A null finding must not force endless tuning. Likewise M9 does not require Molt to outperform the direct baseline. Methodological completion and a favorable hypothesis result are different outcomes.

## What constitutes V1 complete

V1 is complete when M0–M9 have evidence, and all of the following hold:

- A small typed data-only DSL and deterministic LibCST engine support the selected Tier 1–2 migrations with tested safety/abstention behavior.
- LLM rule generation, the three-proposal development repair bound, and the paired no-repair arm work end to end without hand-edited model output.
- Two migrations meet the registered 15–30 viable independent-repository target each, with development/held-out separation, Tier 2 coverage, pinned SHAs, passing originals, attributable upgrade failures, and honest exposure documentation.
- All required available baselines have completed the same frozen verification protocol on the held-out population, including recorded failures, abstentions, and exclusions.
- Correctness audits, stage outcomes, costs, runtime, repair effects, uncertainty, amortization, and observed or absent break-even behavior are reported from reproducible artifacts.
- The static research report explains the limits of the claims, accounts for protocol deviations, and supports a clean reproduction path. No product service is required.

A smaller pilot is useful but is not the full V1 benchmark. If viable population, budget, or oracle quality makes this scope infeasible, publish a dated protocol amendment **before held-out method outcomes are inspected** and explicitly name the reduced scope. Never revise a target retroactively to turn an incomplete experiment into a completed one.

## Immediate next work

Begin Phase 0: verify related work beyond the starting references, write candidate scorecards, and inspect development-only installation feasibility. The highest-risk unknown is whether two bounded, nontrivial migrations yield enough independent, reproducibly testable clients. Resolve that before committing to the full primitive set or LLM integration.
