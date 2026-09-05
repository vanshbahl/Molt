# Molt glossary

A reading guide for the planned experiment, not a list of implemented capabilities. Each row gives a plain-English meaning and its specific relevance to Molt; examples are illustrative, not migration advice. Synonyms share a row. Start with [README](../README.md) for the thesis, [ROADMAP](ROADMAP.md) for measurement rules, and [RELATED_WORK](RELATED_WORK.md) for source-backed paper comparisons.

## Source-code structure

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **AST — Abstract Syntax Tree** | A tree representing the grammatical structure of code while leaving out many surface details. | Separates a call from text that merely looks like one: `f(x)` is a call node. |
| **CST — Concrete Syntax Tree** | A syntax tree retaining concrete source details such as punctuation and, in LibCST, whitespace/comments. | Supports small migration diffs without discarding formatting. |
| **Parser** | A program that turns source text into a structured representation according to a grammar. | Molt must parse Python before transforming it. |
| **Token (source code)** | A lexical unit recognized while reading a programming language. | `name`, `(`, and `42` are source tokens; these differ from LLM billing tokens. |
| **Syntax** | The rules describing valid arrangements of code. | A patch can parse correctly yet perform the wrong migration. |
| **Semantics** | What code means or does when executed. | Changing argument order can change behavior without breaking syntax. |
| **Source transformation / code rewrite / program transformation** | A change from one program representation to another. | Molt's planned rules specify such changes; correctness needs a migration contract. |
| **Codemod** | A tool or script that automates a recurring source-code edit. | Official codemods are useful comparators, not automatic reasons to reject a migration. |
| **Refactoring** | Restructuring code while preserving its observable behavior under stated assumptions. | An upgrade may also require intentional API/behavior changes, so not every migration is purely refactoring. |
| **Tree traversal** | Visiting the nodes of a tree in some order. | The engine searches Python trees for eligible sites. |
| **Visitor pattern** | Organizing operations around callbacks for different node types. | A fixed visitor can handle calls; the model need not generate a visitor program. |
| **Matcher** | A specification or function that recognizes a desired code shape. | Recognizing `x.old()` alone does not establish which library owns it. |
| **Capture** | The source fragment saved when part of a pattern matches. | Preserve `load()` from `old(load())` when constructing its replacement. |
| **Metavariable** | A placeholder in a transformation pattern rather than a variable in the user's program. | A placeholder such as `$ARG` can capture many different argument expressions. |
| **Source span** | The start and end positions of a piece of source. | Connect an edit, abstention, and audit label to the same original site. |
| **Pretty-printing** | Turning structured code into readable source using formatting rules. | A printer may change layout; Molt needs to distinguish formatting from migration edits. |
| **Format preservation** | Keeping existing layout/comments where edits do not require changes. | Reduces review noise; it does not prove behavioral correctness. |

## Python and LibCST

The technical reference is [LibCST's documentation](https://libcst.readthedocs.io/en/latest/), including its [metadata API](https://libcst.readthedocs.io/en/latest/metadata.html). Metadata does not reveal all dynamic Python behavior.

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **LibCST** | A Python library for parsing, inspecting, and modifying concrete syntax trees. | Proposed transformation substrate; the choice itself is not the research result. |
| **CSTNode** | LibCST's base node type for elements in its syntax tree. | Captures and replacements must be structurally valid nodes. |
| **Metadata** | Extra information associated with a source node beyond its immediate syntax. | May help justify a match rather than relying on spelling alone. |
| **MetadataProvider** | A provider interface/category that computes metadata for nodes. | The planned engine asks existing providers for facts instead of inventing a full analyzer. |
| **QualifiedNameProvider** | A LibCST provider reporting possible qualified identities for names. | Multiple candidate identities may require abstention. |
| **ScopeProvider** | A LibCST provider describing scopes, assignments, and accesses. | Helps detect when a local binding hides an imported name. |
| **Qualified name** | A name with context identifying its origin or containment. | `library.parse` conveys more than the spelling `parse`. |
| **Scope** | A region of code with particular rules for looking up names. | A function's local `client` can differ from the module's `client`. |
| **Binding** | An association between a name and an object or declaration. | `import library as lib` establishes a binding for `lib`. |
| **Symbol** | A named program entity considered during analysis. | Molt needs to identify the affected function/class, not every matching word. |
| **Import alias** | An alternate local name assigned by an import. | `from x import y as z` means the relevant use may be spelled `z()`. |
| **Shadowing** | A nearer binding hiding another binding with the same name. | A parameter `np` may hide an imported NumPy alias. |
| **Re-export** | Making an imported object available through another module. | `wrapper.parse` might originate elsewhere; incomplete evidence can cause abstention. |
| **Relative import** | An import interpreted relative to the current package. | `from .helpers import parse` requires package context. |
| **Star import** | An import that brings a set of exported names into a namespace. | `from x import *` can make source identity harder to establish. |
| **Receiver** | The object on which an attribute or method is accessed. | In `obj.json()`, `obj` is the receiver; its type may be unknown. |
| **Attribute access** | Reading or referring to a member through a dot expression. | `obj.name` can trigger dynamic behavior; spelling is weak identity evidence. |
| **Call expression** | An expression invoking a callable with arguments. | `parse(text, strict=True)` is a potential logical migration site. |
| **Positional argument** | An argument assigned by its position in a call. | In `f(x, y)`, swapping the arguments may change semantics. |
| **Keyword argument** | An argument associated with an explicit parameter name. | `f(timeout=5)` may require a bounded keyword rename. |
| **`*args`** | Positional argument packing in a definition or iterable unpacking in a call. | `f(*items)` may hide how many arguments need rearranging. |
| **`**kwargs`** | Keyword packing in a definition or mapping unpacking in a call. | `f(**options)` may already supply a keyword a rule wants to add. |
| **Evaluation order** | The sequence in which parts of an expression are evaluated. | Reordering `f(load(), save())` can alter behavior. |
| **Side effect** | An observable effect beyond returning a value, such as writing a file. | Removing or duplicating an argument expression may remove or repeat its side effects. |

## Dependency migrations

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **Dependency** | Software a project needs to build or run. | Molt studies source changes required when one dependency changes. |
| **Package** | A distributable software unit, or in Python imports, a namespace containing modules. | Distribution names and import names may differ; record both. |
| **Library** | Reusable code providing functionality to other programs. | A library's clients are the repositories being migrated. |
| **API — Application Programming Interface** | The functions, classes, protocols, and behavior exposed for users of software. | Migration scope must identify which API contract changes. |
| **API migration** | Adapting client code to use a changed or replacement API. | Molt focuses on bounded same-library upgrades, while some prior work replaces libraries. |
| **Breaking change** | A change that makes a previously supported use incompatible. | A removed function can break a previously passing client. |
| **Breaking dependency update** | A dependency-version change that breaks a client's supported build or behavior. | Admission requires evidence of this break, not just a version bump. |
| **Deprecation** | Notice that an API is discouraged and may later change or disappear. | A warning alone may not satisfy the registered breaking-upgrade admission rule. |
| **Semantic versioning / SemVer** | A versioning convention that relates major/minor/patch increments to public-API compatibility. | Useful evidence, but projects differ in adherence and pre-1.0 policies. |
| **Major version** | The leading component of a conventional `major.minor.patch` version. | `1`→`2` suggests checking compatibility; the numeral alone does not prove a break. |
| **Version constraint** | A rule specifying acceptable dependency versions. | `>=1,<2` is a range, not a reproducible exact environment. |
| **Dependency pin** | A requirement fixing a dependency to an exact version. | The harness, not generated rules, controls the target pin. |
| **Lockfile** | A recorded dependency solution, often including exact versions and artifact hashes. | Helps recreate old/target environments; platform differences can still matter. |
| **Dependency resolution** | Choosing a mutually compatible set of dependency versions. | An upgrade can force changes beyond the named library. |
| **Dependency closure** | The full set of direct and indirect dependencies needed by a project. | Record the closure to detect hidden environment changes. |
| **Transitive dependency** | A dependency introduced by another dependency. | An indirect package update may explain a failure incorrectly blamed on Molt. |
| **Migration guide** | Maintainer instructions describing how clients should adapt. | Shared public evidence for all experimental arms. |
| **Old version** | The exact dependency version before the studied upgrade. | Its passing baseline establishes that the task starts healthy. |
| **Target version** | The exact dependency version required after the upgrade. | A patch that downgrades it has not solved the task. |
| **Backward compatibility** | Continued support for previously valid uses. | A compatibility shim may avoid a break; the task contract must say whether it meets the intended migration. |

## Molt rule system

Everything in this section describes the proposed design.

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **DSL — Domain-Specific Language** | A language designed for a limited kind of task. | Molt's planned DSL permits a small set of migration operations. |
| **Schema** | A specification of allowed data shapes and constraints. | Rejects unknown operations before any repository edit. |
| **JSON Schema** | A standard vocabulary for describing and validating JSON data. | Can describe the model-facing rule format; cannot prove a migration is correct. |
| **Pydantic** | A Python library for defining and validating typed data models. | Planned rule validation tool; distinct from Pydantic upgrades as benchmark candidates. |
| **Validation** | Checking an artifact against specified requirements. | Schema validation and behavioral verification are different checks. |
| **Serialization** | Encoding an in-memory object into a storable/transmittable form. | A rule bundle can be stored as JSON. |
| **Canonical serialization** | Using one prescribed encoding for equivalent data. | Stable ordering/encoding enables reproducible rule hashes. |
| **Rule** | A specification of when and how to transform source. | A rule must encode reusable conditions, not a repository-name exception. |
| **Rule bundle** | One versioned migration artifact containing ordered/composed rule operations. | The same frozen bundle is reused across repositories. |
| **Primitive** | A fixed operation supported by the trusted engine. | `rename_argument` is a proposed primitive, not generated executable code. |
| **Precondition** | A condition that must hold before an operation is authorized. | A symbol's identity must match the intended API. |
| **Postcondition** | A requirement expected after an operation. | A renamed keyword must not coexist with a conflicting duplicate. |
| **Capture** | A matched source subtree retained for use in a replacement. | Same meaning as above; captures preserve user expressions under fixed semantics. |
| **Replacement** | The structure substituted at a matched site. | Must use allowed literals/captures without silently changing evaluation behavior. |
| **Rule compiler** | The component translating rule data into executable operations of a fixed engine. | It must not execute arbitrary code supplied by the model. |
| **Rule engine** | The software that matches and performs rule operations. | Bugs here can invalidate schema-valid rules' apparent safety. |
| **Rule application** | Running a rule against source to produce edits or reported non-edits. | Held-out application has no LLM feedback loop. |
| **Unsupported case** | A required migration that the frozen representation or implementation cannot handle. | Record whether the cause is the DSL ceiling, missing evidence, or an engine limitation. |
| **Abstention** | An explicit decision to avoid an edit because requirements cannot be established. | Protecting an unrelated site is useful; abstaining at a required site loses coverage. |
| **Deterministic** | Producing the same result from identical inputs under the same configuration. | A wrong rule can be deterministically wrong. |
| **Idempotent** | Having no further effect when applied again after a successful application. | A second migration pass should produce no additional diff. |
| **Transactional edit** | Publishing a set of edits together only if the operation succeeds. | Avoid leaving half-migrated files after an error. |
| **Dry run** | Showing planned effects without committing them to the target source. | Supports review of diffs and abstentions. |

## Program analysis

These terms occur in papers; **Molt does not claim full type inference, alias analysis, control-flow analysis, or data-flow analysis**. Pyright is initially a verifier. Consult [Pyright's project documentation](https://github.com/microsoft/pyright) for the tool itself.

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **Static analysis** | Reasoning about code without running the analyzed program. | Proposed name/scope matching is static and may lack dynamic facts. |
| **Dynamic analysis** | Learning about behavior by executing a program. | Tests and probes expose failures for particular executions. |
| **Type checking** | Checking that operations are consistent with a type system. | A required typecheck is one part of verification, not a full correctness oracle. |
| **Type inference** | Deriving likely or required types without every type being explicitly written. | Papers may use this to recognize receivers; Molt cannot assume it has such facts. |
| **Pyright** | A static Python type checker. | Required only in pre-registered applicable cohorts; diagnostics are not a universal binding API. |
| **Symbol resolution / name resolution** | Determining which declaration or binding a reference denotes. | Helps distinguish an imported API from an unrelated local name. |
| **Control flow** | The possible order of execution through branches, loops, and calls. | Complex control-dependent migrations may exceed the DSL. |
| **Data flow** | How values and definitions move through program operations. | A value's later uses can make a local rewrite unsafe; full analysis is not planned. |
| **Call site** | A source location where a function or method is invoked. | Often a migration site, but one logical edit may span several nodes. |
| **Scope analysis** | Identifying scopes and their bindings/accesses. | Tests the usefulness of lexical evidence in the matching ablation. |
| **Alias analysis** | Determining whether different expressions may refer to the same object. | `a = b` can make mutation visible through both names; scope metadata alone is insufficient. |
| **Soundness** | Never making a false claim under an analysis's stated assumptions. | Claiming every authorized edit is safe requires stronger evidence than passing fixtures. |
| **Completeness** | Finding every case that satisfies the specified property. | Conservative rules can miss valid migration opportunities. |
| **Ambiguity** | Having insufficient evidence to select one interpretation confidently. | A receiver may belong to several possible libraries. |
| **Conservative matching** | Authorizing an edit only when required evidence is established. | Can reduce unrelated edits at the price of abstention; the benefit must be measured. |

## Experimental design

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **Hypothesis** | A claim an experiment could support or contradict. | “Repair helps held-out success” must permit a negative result. |
| **Research question / RQ** | A precise question the study is designed to answer. | RQ2 asks when reuse pays after correctness and verification are counted. |
| **Baseline** | A reference method used to interpret another method's results. | Direct patching must be competent, not deliberately weak. |
| **Experimental arm** | One specified method/configuration in a comparison. | A–F distinguish direct, exemplar, initial/repaired rules, text, and expert tools. |
| **Control** | A reference condition or factor kept unchanged to isolate an effect. | Identical target environments prevent dependency differences from explaining outcomes. |
| **Treatment** | The feature or intervention whose effect is studied. | Giving B an exemplar is the treatment relative to A. |
| **Ablation** | Removing or changing one component while keeping others fixed. | Turn metadata matching off while retaining the same rule semantics. |
| **Benchmark** | A set of tasks plus a protocol for evaluating methods. | Repository clones alone are not Molt's full benchmark. |
| **Dataset** | A collection of recorded observations or task instances. | Manifests, partitions, and provenance define what Molt evaluated. |
| **Development set** | Data allowed to guide method design and tuning. | Rule generation/repair may use these repositories. |
| **Validation set** | A separate tuning set used to choose among candidate configurations. | An optional split within development could test budget choices; it is not the held-out set. |
| **Held-out set / test set** | Data reserved for final evaluation rather than method selection. | Held-out failures must not change Molt's rules. This differs from a repository's unit-test suite. |
| **Repository family** | Repositories sharing substantial origin or relevant code. | Forks/templates stay in one partition and are not independent evidence. |
| **Train/test leakage** | Information from evaluation examples influencing training or method selection. | No neural training is required: tuning a rule on held-out failures still leaks. |
| **Data leakage** | Any prohibited information crossing an experimental boundary. | Giving a direct agent another held-out patch is leakage. |
| **Contamination** | Evaluation material or close equivalents appearing in a model's earlier learning/exposure. | Release dates reduce uncertainty only partially; they cannot prove absence. |
| **Memorization** | Reproducing previously encountered content rather than solving from the supplied evidence. | A known public codemod may explain apparent synthesis ability. |
| **Pre-registration** | Recording hypotheses and decisions before inspecting the outcomes they govern. | Prevents selecting migrations/budgets after seeing which favor Molt. |
| **Protocol** | The written rules for selecting, running, and analyzing the experiment. | Specifies retries, costs, oracles, exclusions, and amendments. |
| **Freeze** | Locking a version of inputs/settings so evaluation cannot silently change them. | Store rule, prompt, exemplar, and dataset hashes. |
| **Seed / random seed** | A recorded initialization value controlling a pseudorandom process. | Recreates split/order choices; an API seed may not guarantee identical model output. |
| **Replicate** | A repeated experimental unit generated under the same declared condition. | New rule generations assess variability; repeated use of one rule does not. |
| **Independent variable** | A factor intentionally varied or used to define comparison groups. | Arm, proposal budget, and metadata setting are examples. |
| **Dependent variable** | An outcome measured in response to the experimental condition. | Verified repository success and cost per success are outcomes. |
| **Confounder** | Another factor that could explain an apparent treatment effect. | Weaker tests in one arm would confound its success advantage. |
| **Oracle / correctness oracle** | A mechanism providing evidence about whether an outcome meets its specification. | Tests, frozen probes, policy checks, and audit combine; none proves all possible behavior. |
| **External probe** | An evaluation check maintained outside the repository's original tests. | Detects a migration error poorly covered by existing tests; private probes stay hidden. |
| **Fixture** | A small prepared example with known expected behavior. | Can specify an exact edit or an expected abstention. |
| **Adversarial fixture** | A deliberately difficult example targeting a likely mistake. | A local `json()` method can catch an overbroad library-method rename. |
| **Gold patch / ground truth** | A trusted reference change or label used for evaluation. | Alternative patches can also be correct; exact textual equality is not always necessary. |
| **Audit** | A documented human examination using a defined correctness rubric. | Must include changed and unchanged sites across successes and failures. |
| **Blinded review** | Reviewing without information, such as method labels, that may bias judgment. | Reviewers can assess edits before learning whether Molt produced them. |

## Outcomes and errors

Use the roadmap's frozen **site** definition. A site is one logical migration obligation or labeled unrelated lookalike, not necessarily one line. Repository-level success asks whether the whole assigned repository meets its verification contract; site-level precision/recall ask which edits were correct or missed. A repository with nine correct edits and one unresolved required edit can still fail.

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **True positive (TP)** | A positive prediction/action that is correct for a labeled positive case. | In a migration-action count, a required site is changed correctly. |
| **False positive (FP)** | A positive prediction/action on a case labeled negative. | Editing an unrelated lookalike is an FP; wrong edits at required sites also need separate error labels. |
| **True negative (TN)** | Correctly leaving a labeled negative case negative. | Leaving an unrelated method untouched is useful behavior. |
| **False negative (FN)** | Failing to identify or resolve a labeled positive case under the chosen task definition. | A required migration left unresolved is a miss, including abstention. |
| **Precision** | The fraction of positive predictions/actions that are correct. | For audited edit precision use correct migration edits / all audited edits; retain wrong required-site edits in the denominator. |
| **Recall** | The fraction of required positive cases successfully found/resolved. | Use correctly resolved required sites / all labeled required sites. |
| **Success rate** | Successful units divided by all assigned units. | Repository success uses repositories, not test counts or edit counts. |
| **Coverage** | The proportion of a declared target population that a method handles. | State whether this means required sites correctly resolved or whole repositories completed. |
| **Applicability** | Whether a method's matching/preconditions permit an operation on a case. | A rule can apply yet produce a wrong edit; applicability is not success. |
| **False-edit rate** | The frequency of unnecessary or incorrect edits under an explicit denominator. | Report unrelated edits, wrong required edits, and edit-error fractions separately; do not invent a negative population. |
| **Missed-edit rate** | Required sites not correctly resolved divided by required sites. | Includes incorrectly edited requirements, not only untouched ones. |
| **Abstention rate** | Explicitly declined cases divided by a declared candidate population. | Report site and repository rates separately; no-match is not automatically abstention. |
| **Unsupported-site rate** | Required sites inexpressible in the frozen DSL divided by all labeled required sites. | Separate the formalism ceiling from missing metadata, engine bugs, and model failures. |
| **Over-generalization** | Making a rule apply beyond the cases where it is valid. | Renaming every `.dict()` call may affect unrelated objects. |
| **Under-generalization** | Making a rule too specific to cover valid cases. | A hard-coded development variable name can miss an alias elsewhere. |
| **Regression** | Breaking behavior or checks that previously worked. | Repair can fix one development client and harm another. |
| **Failure taxonomy** | A defined classification of failure causes. | Distinguish invalid rule, unsupported construct, wrong edit, timeout, and infrastructure failure. |
| **Infrastructure failure** | A failure of the environment or harness rather than the method's migration reasoning. | An unavailable wheel is different from a wrong patch, but cannot silently vanish from frozen results. |
| **Method failure** | A failure attributable to the evaluated method under its allowed budget. | Invalid output, unresolved migration, forbidden edits, and method timeouts are examples. |

For simple binary **site detection**, precision is `TP/(TP+FP)` and recall is `TP/(TP+FN)`. Correct transformation is a richer task: selecting the right site but applying the wrong replacement is not a correct edit. Molt therefore labels site selection and edit correctness separately; it must not squeeze every wrong rewrite into an incompatible binary table. Undefined ratios, including no audited edits, are `not defined`, not perfect precision.

## Practical statistics

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **Sample** | The cases actually observed from a larger set of possible cases. | Admitted clients form a selected sample, not all Python projects. |
| **Sample size** | The number of relevant observational units. | State both migration count and independent repository-family count. |
| **Population** | The broader set about which a claim is intended. | Eligibility rules limit the population Molt's evidence can address. |
| **Independence** | One observation not sharing the dependence relevant to another observation's outcome. | Forks and applications of one generated rule share information; account for clustering. |
| **Confidence interval** | An interval produced by a procedure designed to cover the true parameter at a stated long-run rate. | Wide intervals warn that a small observed advantage is uncertain. |
| **Variance** | A measure of how much outcomes differ around their average. | Report differences across migrations and generation replicates. |
| **Bootstrap** | Estimating uncertainty by repeatedly resampling observed units with replacement. | Resample families, not individual calls as though independent. |
| **Paired comparison** | Comparing methods on the same cases. | Each admitted repository receives every required arm from a clean state. |
| **Paired bootstrap** | Resampling case pairs together so method comparisons retain their shared cases. | Preserve initial/repaired and A/B outcomes when resampling families. |
| **Statistical power** | The chance a study detects an effect of a given size under specified assumptions. | Few migrations can miss real differences; a null result is not proof of equality. |
| **Effect size** | The magnitude of a measured difference. | A five-percentage-point success gain is more informative than significance alone. |
| **Sensitivity analysis** | Repeating an analysis under plausible alternative assumptions. | Check whether price, ordering, infrastructure handling, or success definitions change the cost conclusion. |
| **Denominator** | The quantity by which a count is divided. | `8/10 repositories` and `80/100 sites` answer different questions despite both being 80%. |

## LLM terminology

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **LLM — Large Language Model** | A model trained to generate and interpret sequences of language/code tokens. | Authors rules or repository patches; its output must be verified. |
| **Prompt** | The instructions and information supplied to a model. | Freeze evidence and prompt versions before evaluation. |
| **System prompt** | A high-priority instruction message configuring a model interaction. | Agent policies must not be overridden by instructions embedded in repository data. |
| **Context window** | The amount of tokenized material a model can consider in one interaction. | Truncation can hide migration evidence; record context policy. |
| **Token (LLM)** | A model-specific unit of encoded text or other input/output. | Billing tokens do not correspond one-to-one with words, lines, or Python tokens. |
| **Input token** | A token supplied to the model. | Count migration evidence and repository context, including repeated inputs. |
| **Output token** | A token generated by the model. | Count failed proposals and retries as well as accepted artifacts. |
| **Reasoning token** | A provider-reported token used for internal reasoning computation. | Record when exposed; it may already be included in billed output totals. |
| **Temperature** | A sampling setting that affects output randomness. | Record it; zero does not guarantee a reproducible hosted service. |
| **Structured output** | Model output constrained to a declared format such as a JSON schema. | Helps format validity, not semantic correctness. |
| **Tool use** | A model requesting operations outside text generation. | Direct agents need source inspection and allowed tests. |
| **Agent** | A controller that uses model decisions and feedback across multiple actions. | Its tools, loops, and stopping limits are part of the method. |
| **Coding agent** | An agent equipped to inspect, edit, and check software. | A competent direct baseline does more than receive one isolated file prompt. |
| **Inference** | Running a trained model to produce an output. | Distinguish model inference from static type inference. |
| **Model configuration** | The model identity and settings governing requests. | Pin version, sampling, reasoning, tools, and limits for meaningful comparisons. |
| **Model drift** | Changes in hosted model behavior or infrastructure over time. | Request timestamps/version metadata help disclose reproducibility limits. |
| **Training cutoff** | A disclosed date describing some boundary of training data collection. | It does not certify that later migration evidence was never encountered. |
| **Prompt caching** | Reusing provider-side computation for repeated eligible prompt content. | Shared migration evidence can reduce direct-arm input cost; do not artificially disable it. |
| **Cache hit** | A request reusing eligible cached material. | Identical prefixes enable possible hits but do not prove one occurred. |
| **Retry** | Another attempt after an error, failure, or unusable response. | Separate transport retries from new semantic attempts and charge billed work. |
| **Generation replicate** | A separately generated rule or patch attempt under the registered experimental configuration. | Measures output variability; applying one frozen rule many times is reuse, not replication. |

Caching and token accounting depend on the selected provider; M0/M7 must verify the then-current policy and price schedule. This glossary does not prescribe a cache lifetime, model, or current price.

## Economics

| Term | Plain-English meaning | Why it matters to Molt / tiny example |
| --- | --- | --- |
| **Marginal cost** | The extra cost of handling one more unit. | Measure the next repository's application/patching and verification bill. |
| **Fixed cost** | Cost paid regardless of how many later units are handled. | Rule generation is fixed for a frozen migration bundle. |
| **Variable cost** | Cost that changes as more units are handled. | Each repository still needs application and verification. |
| **Amortized cost** | Total cost spread across the units served. | The generation bill per repository shrinks as reuse grows. |
| **Cumulative cost** | All cost incurred up to a given deployment count. | Include failures and abstentions in the curve, not only successes. |
| **Break-even point** | The scale where two specified total-cost measures become equal. | A raw-bill crossing does not establish equivalent correctness. |
| **Cost per success** | Total cost divided by the number of successes under a stated definition. | Define success first; test-only and audited success differ. |
| **Cost per verified success** | Total cost divided by repositories satisfying the declared verification contract. | Primary economic outcome, accompanied by success rate and audit coverage. |
| **Setup cost** | Work required to prepare a method/environment before repeated use. | Include exemplar preparation, evidence curation, and tool configuration. |
| **Verification cost** | Resources spent checking whether outputs meet the contract. | Rule development and failed attempts also consume test/probe resources. |
| **LLM cost** | The monetary charge for model usage. | Use actual billing where available and label price-based estimates. |
| **Compute cost** | The cost of CPU/GPU, memory, storage, and related execution resources. | Deterministic transformations and containers are not free merely because they use no model tokens. |
| **Human effort** | Person-time spent preparing, reviewing, diagnosing, or repairing work. | Report hours separately and price them only under explicit assumptions. |
| **Sensitivity analysis (economics)** | Checking how conclusions change with plausible cost assumptions. | Vary prices, cache behavior, verification expense, success rates, and deployment order. |

For one migration and **n additional repositories after development**:

```text
C_direct(n) = nL
C_Molt(n)   = R + nD
```

`L` is average direct patching cost per repository including retries. `R` is total rule-generation/repair cost, including failed proposals. `D` is average deterministic application cost. Direct patching repeatedly pays `L`; Molt pays `R` once and then `D` repeatedly. These costs must use the same monetary units. If `L > D`, the simple curves meet at `R/(L-D)`; if `L <= D`, reuse has no eventual raw-cost advantage under this model. Equality can occur between integer repository counts.

Illustration only: if `L = $4`, `R = $20`, and `D = $1`, ten repositories cost $40 directly and $30 with Molt. But if direct patching verifies eight successes while Molt verifies only three, the costs per verified success are **$5 and $10**, respectively. The cheaper total bill bought much less successful work. If there are zero successes, there is no finite cost per verified success.

The [full-cost model](ROADMAP.md#economics-and-prompt-caching) adds setup, development verification, per-repository checking, and other tool compute. Observed caching, difficult repositories, retries, and abstentions make costs nonconstant. Never discard those expenses, pretend development was free, or count a manually rescued failure as autonomous success. Report both LLM-only and full-cost views, plus human effort and common dataset curation.

## Transformation tools and prior-art vocabulary

These entries identify categories and the idea Molt needs; [RELATED_WORK](RELATED_WORK.md) contains the primary sources and detailed limits.

| Term | Plain-English meaning | Why it matters to Molt |
| --- | --- | --- |
| **Comby** | A structural search-and-replace tool using templates. | Structural patterns are an established alternative to plain text replacement. |
| **GritQL** | A language for querying and rewriting code patterns. | A possible comparator to a custom bounded DSL. |
| **Ast-Grep** | A tool for structural code search and rewriting. | Can help compare syntax-oriented matching under equivalent semantics. |
| **tree-sitter** | A parser framework supporting incremental syntax trees. | Underlies several related tools; parsing is not complete semantic analysis. |
| **PolyglotPiranha** | A rule-based transformation framework with scoped rule propagation. | SPELL's substrate demonstrates reusable declarative migration machinery. |
| **Spoon** | A Java source analysis/transformation framework. | One engine used by BigBag; engine configurations can affect generation outcomes. |
| **JavaParser** | A Java parser/transformation ecosystem with optional symbol-solving support. | Do not equate its entire capability with a paper's syntax-only configuration. |
| **OpenRewrite** | An automated refactoring ecosystem based on reusable recipes. | Repository-scale codemods already exist; Moderne supports broader operational use. |
| **Rector** | A PHP upgrade and refactoring tool. | Conceptual migration infrastructure outside Molt's language scope. |
| **REFAZER** | A research system for learning transformations from examples. | Example-driven rule synthesis predates LLMs. |
| **LASE** | A research system for learning and applying systematic edits. | Edit contexts matter when deciding where a learned change belongs. |
| **Meditor** | A research system for inferring API migration edits. | Migrations may require related changes beyond API-name substitution. |
| **MELT** | A Python API-migration rule-mining system. | Type evidence and incorrect generalization are central precedents. |
| **SPELL** | An LLM-assisted Python migration-script synthesis system. | Declarative synthesis and refinement are prior art. |
| **BigBag** | An agent-generated AST-transformation system for Java dependency upgrades. | Reusable rules already transfer between clients of breaking updates. |
| **RuleFlow** | A system converting discovered optimizations into reusable compiler rules. | Amortization is already a motivation; distinguish it from measured deployment economics. |
| **BUMP** | A benchmark of reproducible Java breaking dependency updates. | Offers admission/reproduction ideas, not ready-made Python tasks. |
| **PyMigBench** | A benchmark of Python library migrations. | Real edit examples need additional work to become Molt's admitted version-upgrade repositories. |
| **SWE-bench** | A benchmark of real repository issue-resolution tasks. | Executable repository evaluation is established but can have incomplete oracles. |
| **SWE-agent** | A repository-editing agent system and interface research project. | Guides the design of a credible tool-using direct baseline. |
