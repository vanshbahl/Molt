# Related work and research positioning

Reviewed **2026-09-05** against primary papers and official tool documentation. This is a targeted review prompted by the adversarial memo, not an exhaustive systematic literature review. Paper findings below are author-reported, not independently reproduced. Linked full texts pin reviewed versions: MELT v2 (July 8, 2024), and v1 for the other six closest papers. Missing reporting is labeled **not reported in the reviewed source**; it is not evidence that an experiment or capability is impossible. Molt has no results.

The proposed contribution is evidence about the conditions under which reuse is worthwhile: verified repository success versus cost, development-only repair transfer, and coverage sacrificed by a constrained representation. Rule generation, reuse, deterministic execution, declarative representations, cross-project application, and feedback-driven refinement are precedents, not Molt contributions. The exact combination of RQs is not asserted to establish literature priority.

## Closest systems

### BigBag

Reyes, Baudry, and Monperrus, *Agentic Generation of AST Transformation Rules for Fixing Breaking Updates*, arXiv:2606.24446. [Primary paper](https://arxiv.org/html/2606.24446v1), §§II–VI, VIII.

- **Problem:** Breaking Java/Maven dependency updates.
- **Representation:** Executable Java transformation programs using Spoon or JavaParser.
- **LLM role:** Coding agents author programs from a broken client and migration/engine documentation.
- **Refinement:** Generate/apply/build feedback from one seed client.
- **Transfer:** Reapply transformations to other clients of the same update; 129 verified transfer targets across 16 updates.
- **Oracle:** Seed repair uses `mvn test`; the transfer table primarily counts `mvn test-compile`, with separate full-test annotations. Compilation success is not verified behavioral migration success.
- **Cost:** Configuration-level campaign expenditure is reported; repository-local direct-LLM comparison and amortized break-even are not reported.
- **Strongest overlap:** Reusable LLM-generated transformations for breaking updates across projects.
- **Remaining distinction:** Molt proposes Python, development-set repair, paired direct/exemplar arms, and correctness-conditioned repository economics. Multi-client seeding is explicitly future work in BigBag.
- **Unknown:** A reproducible numeric agent-iteration cap was not established by this review; do not infer one from its bounded-loop description.

### SPELL

Ramos et al., *Spell: Synthesis of Programmatic Edits using LLMs*, arXiv:2602.01107. [Primary paper](https://arxiv.org/html/2602.01107v1), §§3–6.

- **Problem:** Primarily migration between Python libraries.
- **Representation:** PolyglotPiranha match/replace rules connected by scoped edges.
- **LLM role:** Generate examples/tests/migrations; orchestrate scripts from anti-unified rules.
- **Refinement:** Up to ten synthesis iterations with engine and test feedback.
- **Transfer:** Synthetic-example scripts applied to 18 GitHub projects; researchers inspect each project to select a suitable script. Source dependencies remain because migration is partial. This is not Molt's single preselected bundle protocol.
- **Oracle:** Generated tests during synthesis; existing project test outcomes during transfer.
- **Cost:** A $100 experimental budget; transformation timing was not measured. No direct repository-patching arm or amortized economics is reported.
- **Strongest overlap:** Declarative Python migration synthesis, iterative rule refinement, and real-project reuse.
- **Remaining distinction:** Molt tests same-library breaking upgrades with development repositories, a frozen shared artifact, and direct/exemplar economics.
- **Caution:** Zero retained pandas→polars triples is explained partly by nontransferable generated test harnesses (§5.5); it does not establish infeasibility of pandas version upgrades.

### MELT

Ramos et al., *MELT: Mining Effective Lightweight Transformations from Pull Requests*, ASE 2023, arXiv:2308.14687. [Primary paper](https://arxiv.org/html/2308.14687v2), §§III–VI, especially §V-E/Table V.

- **Problem:** Python API deprecations and migrations inferred from library PRs.
- **Representation:** Comby templates with type guards, supported through Jedi/LSP.
- **LLM role:** Generate additional code examples; rules are inferred algorithmically, not directly authored by the LLM.
- **Refinement:** Filtering and generalization, not a development-repository repair loop.
- **Transfer:** Fifteen rules evaluated across 60 clients of three libraries.
- **Oracle:** Test/warning/failure deltas; pre-existing unrelated failures can obscure outcomes.
- **Cost:** No comparable billed-cost or repository amortization analysis reported.
- **Strongest overlap:** Lightweight reusable Python migration rules and client evaluation.
- **Remaining distinction:** Molt requires old-pass/target-fail admission and compares direct patching and shared-rule repair under a common oracle.
- **Critical evidence:** One pandas rule caused 81 additional test failures across four projects; the authors attribute unrelated API transformations to missing type information. These are **test failures, not 81 independently counted false edits**. This motivates a controlled matching ablation; it does not prove LibCST will resolve the same ambiguity.

### Allain et al.

Allain, Blot, Khelladi, and Acher, *Code Transformation Rule Synthesis using LLMs: Potential and Limits*, arXiv:2609.03592, submitted **September 3, 2026**. [Submission record](https://arxiv.org/abs/2609.03592), [primary paper](https://arxiv.org/html/2609.03592v1), §§4–7.

- **Problem:** Rule synthesis for repair, API misuse, API migration, and language-version migration.
- **Representation:** Comby, GritQL, and Ast-Grep rules.
- **LLM role:** Infer rules from before/after examples, with optional retrieved DSL guidance.
- **Refinement:** No execution-feedback repair loop evaluated; discussed as an improvement.
- **Transfer:** Dataset-pair reuse measured through additional matches, not a frozen bundle repairing independent upgrade repositories.
- **Oracle:** Applicability, textual/AST agreement, and test validation on Defects4J/BugsInPy. Saying the study uses no repositories is inaccurate.
- **Cost:** RQ1 uses token expense; the named NT metric is **generated tokens**. It is not an uncached/cached-input, output, reasoning, and billed-cost ledger. No direct repository-patching arm or repository break-even comparison is reported.
- **Strongest overlap:** LLM rule synthesis, rule-language comparison, reuse, and cost measurement.
- **Remaining distinction:** Molt's proposed success-conditioned deployment economics and development/held-out repair pairing. This very recent paper must remain central when M0 refreshes the review.

### Cummins et al.

Cummins et al., *Don't Transform the Code, Code the Transforms: Towards Precise Code Rewriting using LLMs*, arXiv:2410.08806. [Primary paper](https://arxiv.org/html/2410.08806v1), §§2–4/Table 1.

- **Problem:** Sixteen transformations of small Python programs.
- **Representation:** Executable Python `ast` transformers.
- **LLM role:** Infer a transformation description and implementation from input/output examples.
- **Refinement:** Up to ten description iterations, then up to **50** implementation-feedback iterations; the memo conflates these limits.
- **Transfer:** Public examples, hidden programs, and non-applicable controls; the direct arm also receives examples. These are not dependency-upgrade repositories.
- **Oracle:** Expected transformed-output agreement, with paper-specific precision/recall definitions; no repository migration test oracle.
- **Cost:** Qualitative compute/review arguments, not repository deployment economics.
- **Strongest overlap:** Direct rewriting versus reusable transform synthesis is already an evaluated comparison; reported aggregate precision is 0.95 versus 0.60 and recall 0.99 versus 1.00, respectively.
- **Remaining distinction:** Molt asks whether the trade-off persists under repository tests/probes, cached direct/exemplar baselines, and full-cost accounting. These program-level scores cannot predict Molt's outcomes.

### RuleFlow

Singh et al., *RuleFlow: Generating Reusable Program Optimizations with LLMs*, arXiv:2602.09051v1. [Primary paper](https://arxiv.org/html/2602.09051v1), §§2.3–4 and appendices A–D.

- **Problem:** Pandas performance optimization.
- **Representation:** Dias-derived patterns, replacements, and Python runtime preconditions; compiler-generated guarded rewrites.
- **LLM role/refinement:** Discover optimized snippets, generalize rules, and revise using counterexamples/checkers.
- **Transfer:** Learn from 199 notebooks; evaluate on 102 PandasBench notebooks. Repository-family separation is not established in the text.
- **Oracle:** Random-data output comparisons, adversarial feedback, and manual rule filtering. Appendix D retains some alias/reference-risk rules; execution is not comprehensive equivalence evidence.
- **Economics measured:** Notebook/cell speedups, successful execution counts, rule hit rates, candidate yield, and agent-decomposition validity; runtime-precondition overhead can cause slowdowns.
- **Not measured in the paper, including appendices:** Billed LLM expenditure, token ledger, discovery/verification monetary totals, cumulative monetary cost, amortized dollars per success, or break-even deployment count. Its per-program discovery-yield analysis is not a matched direct-LLM deployment cost arm.
- **Strongest overlap:** Explicit amortization of LLM discovery through reuse.
- **Remaining distinction:** Molt proposes measured upgrade economics conditional on verified success. Amortization itself is prior art; missing monetary reporting is a scoped observation, not a field-wide priority claim.

### Google migration system

Ziftci et al., *Migrating Code At Scale With LLMs At Google*, arXiv:2504.09691. [Primary paper](https://arxiv.org/html/2504.09691v1), §§3–4.

- **Problem:** Industrial identifier-width migrations across C++, Java, and Dart.
- **Representation:** Direct file patches, not a generated shared rule artifact.
- **LLM role:** Edit entire identified files using migration instructions and suggested locations; Kythe assists discovery.
- **Refinement:** Multiple patch attempts, validation, and developer review/further edits; not rule repair.
- **Transfer:** Industrial deployments, not a development/held-out reusable-rule experiment.
- **Oracle:** Automated validation/regression checks and human review; production and test code can be migrated.
- **Cost:** Developer-estimated 50% time reduction, not measured token or full-cost break-even.
- **Strongest overlap:** Evidence that direct LLM patching with useful tooling is a credible baseline.
- **Remaining distinction:** Molt's controlled Python-upgrade experiment freezes tests for every arm. Its direct agents represent a paradigm, not a reproduction of Google's internal model, infrastructure, or workflow. Human-assisted completion must not be labeled autonomous success.

## Earlier transformation-by-example / migration work

| Work | Established idea Molt must account for |
| --- | --- |
| [REFAZER](https://arxiv.org/abs/1608.09000) | Synthesizes reusable syntactic transformations in a DSL from example edits; examples and abstraction predate LLMs. |
| [LASE](https://www.cs.utexas.edu/~mckinley/papers/lase-icse2013.pdf) | Learns systematic edits and contextual application conditions from examples; locating all appropriate edit sites is part of the problem. |
| [Meditor](https://people.cs.vt.edu/~shengzx/papers/ICPC-Technical_Track-59.pdf) | Infers and applies API migration edits, including related changes beyond replacing a method name. |

These systems inform representation and edit generalization. They are historical context, not substitutes for the closest LLM-era comparisons above.

## Transformation infrastructure

| Tool | Relevance and boundary |
| --- | --- |
| [OpenRewrite / Moderne](https://docs.openrewrite.org/) | Recipes, semantic trees, and repository-scale transformation; a reusable execution platform is established infrastructure. |
| [Piranha / PolyglotPiranha](https://github.com/uber/piranha/blob/master/POLYGLOT_README.md) | Rules and scoped propagation built on tree-sitter; relevant to script composition and SPELL. |
| [Comby](https://comby.dev/) | Structural templates/captures; MELT adds type support. Do not equate structural matching with plain regex. |
| [GritQL](https://github.com/biomejs/gritql) | Declarative code matching/rewriting; a possible comparable formalism. |
| [Ast-Grep](https://ast-grep.github.io/) | AST-oriented search/rewrite patterns and rule configuration; possible matching comparator. |
| [Rector](https://github.com/rectorphp/rector) | PHP upgrade/refactoring automation; conceptual context outside Molt's Python scope. |
| [LibCST](https://libcst.readthedocs.io/en/latest/) | Format-preserving Python CST tooling; chosen machinery whose practical matching trade-offs need measurement. |
| [tree-sitter](https://tree-sitter.github.io/tree-sitter/), [Spoon](https://spoon.gforge.inria.fr/), [JavaParser](https://javaparser.org/) | Parsing/analysis infrastructure used by other systems. JavaParser also offers symbol solving; a paper's chosen configuration does not define a tool's entire capability. |

A declarative language is not automatically as restricted as Molt's proposed schema. Compare the admitted grammar, guards, execution capabilities, and actual edits; do not label every external DSL universally non-executable or every schema-valid rule safe.

## Repository-level evaluation context

| Work | Relevance and limit |
| --- | --- |
| [SWE-bench](https://arxiv.org/abs/2310.06770) | Real repository issue-resolution tasks and executable evaluation. It does not by itself isolate a known dependency migration. |
| [SWE-agent](https://arxiv.org/abs/2405.15793) | Repository tools and agent-computer interfaces inform a competent direct patcher. Tool quality must be established before comparison. |
| [BUMP](https://arxiv.org/abs/2401.09906) / [artifact](https://github.com/chains-project/bump) | Reproducible Java/Maven breaking updates: 571 updates from 153 projects in the paper. Admission methodology is relevant; this is not a Python dataset. |
| [PyMigBench](https://sarahnadi.org/assets/pdf/pubs/IslamMSR23.pdf) / [artifact](https://github.com/ualberta-smr/PyMigBench) | Real Python cross-library migration examples. Pin the dataset version; counts and task units differ across releases and derived studies. Pairs are not automatically reproducible old-pass/target-fail upgrade instances. |

Additional direct-migration context: [Using LLMs for Library Migration](https://arxiv.org/abs/2504.13272) evaluates Python cross-library edits and client tests; it must not be conflated with the original PyMigBench publication. [Environment-in-the-Loop](https://arxiv.org/abs/2602.09944) is a relevant agent/environment approach identified for the M0 follow-up review; only its abstract was inspected here, so its detailed budgets, allowed environment edits, and economic treatment remain **unknown**. [PyMigTool](https://arxiv.org/abs/2510.08810) is another discovered end-to-end migration system whose full protocol remains to be reviewed before M0 closure.

## Memo claims: verification and corrections

The central overlap diagnosis is supported. The memo's stronger conclusions require these limits:

| Memo claim | Disposition |
| --- | --- |
| Architecture is “70% already published”; numerical proceed/pivot probabilities; predictions about competitor timing or publication acceptance | Not independently verifiable measurements. Omitted from Molt's claims. |
| Nobody studies amortization, repair transfer, or abstention | Field-wide absence is not established by this targeted review. RuleFlow directly defeats the broad amortization premise; see its scoped economic account above. |
| All transfer studies implement the same held-out discipline | Unsupported. Target-aware script selection, example-pair reuse, notebook transfer, and frozen repository-family partitions are different protocols. |
| Cummins has only ten feedback iterations; Allain uses no repositories | Corrected in the corresponding entries above. |
| Data-only rules guarantee zero out-of-contract edits | Unsupported: compiler bugs, mistaken bindings, and erroneous preconditions can still produce forbidden or incorrect edits. Measure them. |
| LibCST scope metadata will distinguish arbitrary same-named receiver methods | Unsupported: lexical bindings do not establish every runtime receiver type. [Metadata documentation](https://libcst.readthedocs.io/en/latest/metadata.html) motivates conservative ambiguity handling. |
| pandas must be rejected; most breaks are Tier 3; it has the worst training exposure | Not established. Cross-library failure does not settle version-upgrade viability; [pandas 2.0 notes](https://pandas.pydata.org/docs/whatsnew/v2.0.0.html) include explicit API removals as well as behavioral changes. Training-corpus rankings are unknown. |
| attrs modernization is a breaking-upgrade candidate | Needs an actual old-pass/target-fail case: [attrs documents both API families](https://www.attrs.org/en/stable/names.html). Modernization alone is not admission evidence. |
| PyJWT's matching advantage is provably zero; Pydantic has ample reproducible clients; a wider benchmark is roughly cost-neutral; metadata ablation is cheap | Unverified feasibility or outcome predictions. Candidate scorecards and measured pilot effort must resolve them. |
| A post-cutoff migration proves non-contamination | Unsupported. Disclosed cutoffs, release dates, and exposure proxies do not establish training absence. |

Verified comparator leads: [Pydantic's migration guide](https://docs.pydantic.dev/latest/migration/) recommends [bump-pydantic](https://github.com/pydantic/bump-pydantic); [NumPy's 2.0 guide](https://numpy.org/doc/2.0/numpy_2_0_migration_guide.html) identifies Ruff NPY201. Neither tool's coverage nor client success has been tested here. Their existence can strengthen the experiment rather than disqualify a migration.

## M0 literature closure

Refresh the closest-paper versions, resolve the additional direct-agent leads, and record search terms/dates, source versions, and any unresolved details in the registered protocol. This review inspected the seven close papers' relevant method/evaluation sections, RuleFlow's full main text and appendices, and the cited primary infrastructure/benchmark sources. It did not run their artifacts or verify their experimental logs. M0 remains open until literature positioning is combined with candidate scorecards, development-only feasibility, a cost estimate, and a dated experimental contract.
