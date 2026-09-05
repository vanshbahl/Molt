# M0 candidate migration scorecards

**Status: investigation, not selection.** These are the 6–8 candidate scorecards required to close [M0](ROADMAP.md#phase-0--literature-candidate-feasibility--experimental-design). Research performed **2026-09-05**: official changelogs/migration guides were fetched directly (cited per candidate), and three candidates were additionally checked with a real, isolated-venv old-pass/new-fail reproduction (recorded in [experiments/feasibility_probes.json](../experiments/feasibility_probes.json)). No candidate here is an admitted repository or a chosen migration; admission requires the Phase 6 curation checklist. Nothing here authorizes engine implementation or model calls.

**Discovery method:** the roadmap's eight named leads (PyJWT, pandas, Pydantic, NumPy, HTTPX, SQLAlchemy, a recent/low-exposure release, attrs) were each checked against a primary source. **attrs failed admission on first evidence** (see below) and is replaced by **urllib3 1→2**, which the roadmap explicitly permits ("attrs modernization, **or another discovered candidate**"). Search queries used: see the per-candidate "Sources" line and the web searches logged in this session for codemod/tool discovery (bump-pydantic, Ruff NPY201, sqlalchemy2-stubs, PyJWT codemods, urllib3 migration guide, recent 2026 breaking releases). No candidate was screened out because Molt could or couldn't already fix it.

Tier definitions are the roadmap's: **Tier 1** name/import/argument changes, **Tier 2** structural call/argument rearrangements, **Tier 3** behavioral changes requiring broader reasoning. The planned primitives are `rename_symbol`, `change_import`, `rename_argument`, `add_argument`, `remove_argument`, restricted `replace_call`.

---

## 1. PyJWT 1.7.1 → 2.x

| Field | Evidence |
| --- | --- |
| **Exact break** | `jwt.decode()` now raises unless `algorithms=[...]` is passed explicitly (previously optional, auto-detected). `jwt.encode()` return type changed `bytes`→`str`. Exceptions `ExpiredSignature`/`InvalidAudience`/`InvalidIssuer` removed in favor of the `*Error`-suffixed names. Flat `verify_expiration`/`verify`/`require_*` decode kwargs replaced by a nested `options={...}` dict. Source: [PyJWT changelog](https://pyjwt.readthedocs.io/en/stable/changelog.html). |
| **Tier mix** | Mostly **Tier 1**: exception rename (`rename_symbol`), `bytes`→`str` return (no call-site edit for typical use). The `algorithms=` requirement and the flat-kwarg→`options={}` restructuring are **Tier 2** (argument rearrangement into a nested structure) and are excluded from the anchor's bounded scope below. |
| **DSL expressibility** | Exception rename: fully expressible (`rename_symbol` + `change_import`). `options={}` restructuring: expressible with restricted `replace_call` mapping named kwargs into one dict argument — feasible but not yet fixture-tested. `algorithms=` value: **not safely inferable** — the correct algorithm is a security decision the DSL cannot guess from a missing argument (also flagged in [ROADMAP.md](ROADMAP.md#candidate-investigations-not-selections)). |
| **Ambiguity** | Low for the exception rename (globally unique names, unlikely to collide). Moderate for `.decode(...)`/`.encode(...)` call sites: these are common method names on unrelated objects (e.g. bytes/JSON codecs), so identity must be established via import-qualified name, not spelling. |
| **Repository supply** | Not independently counted in M0 (PyPI download-stat APIs returned 429/required an API key during this pass — see [feasibility_probes.json](../experiments/feasibility_probes.json)). PyJWT is a foundational auth dependency reused by many web frameworks; qualitative prevalence is high. Exact independent-repository counts are **unresolved**, deferred to Phase 6 curation. |
| **Old-pass → new-fail reproducibility** | **Probed and confirmed** (2026-09-05, PyJWT 1.7.1 → 2.10.1): old call succeeds; identical call raises `DecodeError` on 2.x. See [feasibility_probes.json](../experiments/feasibility_probes.json). |
| **Oracle quality** | Strong for the bounded scope: the `DecodeError`/`AttributeError` (for old exception names) is a direct, unambiguous exception; no external probe needed beyond the repository's own decode call sites. |
| **Setup difficulty** | Low. Pure-Python(ish) dependency (`cryptography` backend has wheels for common platforms); no external service, no DB. |
| **Existing codemods** | None found. No official or community PyJWT 1→2 codemod was located in this search. |
| **Estimated experiment cost** | Low. Small, well-isolated API surface; cheap to install and verify; cheap to generate a rule for (few operations). Good candidate for a low-cost anchor across all six arms. |
| **Admission risk** | The genuinely useful bounded task is narrower than "migrate PyJWT" — must explicitly scope to the exception rename + options-dict restructuring, and treat `algorithms=` value selection as excluded/abstained. |

---

## 2. pandas 1.x → 2.0 (bounded to explicit removals)

| Field | Evidence |
| --- | --- |
| **Exact break** | Confirmed removed (not merely deprecated) in 2.0.0: `Series/DataFrame.iteritems()`, `.append()`, `.pad()`→`.ffill()`, `.backfill()`→`.bfill()`, `Int64Index`/`UInt64Index`/`Float64Index` classes, `DataFrame.lookup()`, `pandas.io.json.json_normalize` (moved), `date_parser` kwarg in `read_csv`. Full list: [pandas 2.0.0 whatsnew](https://pandas.pydata.org/docs/whatsnew/v2.0.0.html). |
| **Tier mix** | **Tier 1/2 mix as required by the roadmap.** Tier 1: `.pad()`→`.ffill()`, `.backfill()`→`.bfill()`, `Int64Index`→`Index(..., dtype=...)` import/rename. Tier 2: `.append()`→`concat()` requires restructuring a method call into a module-level function call with the receiver becoming an argument — a genuine call-shape change, not a rename. Tier 3 (explicitly out of the bounded task): Copy-on-Write semantics, dtype-inference changes, tz default changes. |
| **DSL expressibility** | Renames: fully expressible. `.append()`→`pd.concat([self, other])`: at the edge of `replace_call` — requires turning the receiver into a list element, which the roadmap's `replace_call` primitive ("maps arguments and captures rather than replacing arbitrary statements") may or may not cover; **flagged as an open Phase 1 fixture question**, not resolved here. |
| **Ambiguity** | Real risk: `.append()` is one of the most overloaded method names in Python (`list.append`, `set.add`-adjacent naming, custom classes). Receiver-type evidence is essential; a syntax-only rule would very plausibly rewrite unrelated `.append()` calls. This makes pandas a strong candidate for the RQ4 metadata-matching ablation, not just the main study. |
| **Repository supply** | Not independently counted in M0. pandas is one of the most-used data libraries; qualitative prevalence is very high, but old-version (pandas <2.0) still-maintained clients with passing test suites may be harder to find as the ecosystem moves forward — this is a real admission risk to check in Phase 6, not assumed here. |
| **Old-pass → new-fail reproducibility** | **Not probed in M0** (documented only, via official whatsnew page). The `.append()`/`.iteritems()` removals are `AttributeError`s at call time — expected to be trivially reproducible, but this is an estimate, not an observation. |
| **Oracle quality** | Strong: removed methods raise `AttributeError` immediately; existing test suites that exercise the removed call sites will fail without needing an external probe. Silent behavior changes (Tier 3, excluded) would need probes instead. |
| **Setup difficulty** | Low-moderate. pandas has occasional native/ compiled-extension install friction on older pins depending on Python version compatibility; generally manageable. |
| **Existing codemods** | None official for the 1.x→2.0 removed-method surface specifically (distinct from the pandas→polars case in SPELL, which is a different, cross-library problem — see [RELATED_WORK.md](RELATED_WORK.md#spell)). |
| **Estimated experiment cost** | Moderate. More operations than PyJWT; the `.append()` ambiguity risk means audit/fixture cost is higher than a pure rename case. |
| **Admission risk** | Must bound the task explicitly to the listed removed methods/classes and disclose Tier 3 spillover; do not claim to "migrate pandas 1→2" broadly. |

---

## 3. Pydantic 1.10 → 2.x (bounded to genuinely-removed surface)

| Field | Evidence |
| --- | --- |
| **Exact break** | **Probed finding, not just documentation**: most of the commonly-cited v1→v2 surface (`.dict()`, `.json()`, inner `Config` class, `pydantic.generics.GenericModel`) is a **soft-deprecation compatibility shim** in 2.9.2 — it still executes correctly and only emits a `UserWarning`. It does **not** satisfy the roadmap's "attributable failure after upgrade" admission bar by itself. The genuinely broken surface found in this pass: `from pydantic import BaseSettings` raises `PydanticImportError` (moved to `pydantic-settings`). Migration guide (secondary, for scope reference only since it lists the full recommended-not-required surface): [Pydantic migration guide](https://docs.pydantic.dev/latest/migration/). Comparator tool: [bump-pydantic](https://github.com/pydantic/bump-pydantic) (10 rules BP001–BP010; **archived 2026-05-27**, "Pydantic V1 has long been EOL"). |
| **Tier mix** | Mostly **Tier 1** for the genuinely-broken imports (`BaseSettings`, and by the same pattern likely `Color`/`PaymentCardNumber` moved to `pydantic-extra-types` — not independently probed). The *popular* `.dict()`/`Config`/validator surface, while real migration guidance, is **out of scope for admission** unless a repository's own test suite asserts on the deprecation warning (e.g. `filterwarnings("error")`) — a case-by-case fact to check per candidate repository, not assumed. |
| **DSL expressibility** | Import rename: fully expressible (`change_import`). This is a narrow, clean Tier 1 task once correctly bounded — but it is a much smaller task than the "Pydantic migration" most engineers picture, which is exactly the finding worth reporting. |
| **Ambiguity** | **High**, and this is the primary reason to keep Pydantic in the study: `.dict()`/`.json()` collide with builtin `dict`/JSON-module method names on unrelated objects; a naive rule targeting the popular (but non-admitting) surface would risk over-generalization on non-BaseModel receivers. This directly tests the DSL/matching ceiling described in [RELATED_WORK.md's MELT entry](RELATED_WORK.md#melt) (81 additional test failures from a similarly-shaped pandas rule). |
| **Repository supply** | Not independently counted. Pydantic is extremely widely used (FastAPI and much of the modern Python web stack depend on it), so a *pool* of old-version clients is plausible, but clients specifically depending on the now-fully-removed surface (vs. the still-working shimmed surface) may be a much smaller subset — an open admission risk. |
| **Old-pass → new-fail reproducibility** | **Probed and confirmed** for the `BaseSettings` import (2026-09-05, Pydantic 1.10.14 → 2.9.2): import succeeds on 1.x, raises `PydanticImportError` on 2.x. The `.dict()`/`Config`/`GenericModel` paths were also probed and found to **not** break (see caveat above). |
| **Oracle quality** | Strong for the bounded import-rename task (`ImportError`/`PydanticImportError` is unambiguous). Weak/nonexistent for the popular surface unless a repository's suite treats warnings as errors — must check per repository, not assume. |
| **Setup difficulty** | Low-moderate; Pydantic 2.x has a Rust-backed core (`pydantic-core`) with prebuilt wheels for common platforms, generally low friction. |
| **Existing codemods** | `bump-pydantic` exists but is archived/unmaintained; useful as a frozen comparator (Arm F) with its unmaintained status disclosed, not as a live baseline. |
| **Estimated experiment cost** | Moderate-high if the popular (ambiguous) surface is included for the DSL-ceiling role; low if bounded strictly to genuinely-removed imports. **Recommend running the bounded-import task as the measured pilot scope, and using the popular/ambiguous surface as the documented DSL-ceiling discussion**, not as a second admitted task in the same pilot — this keeps the admission-rule violation risk (deprecation-only "breaks") out of the frozen denominator. |
| **Admission risk** | The single largest scoping risk in this candidate list: a naive Pydantic task built from the migration guide alone would likely include many non-admitting (deprecation-only) sites. This is registered here explicitly so it cannot be silently smoothed over later. |

---

## 4. NumPy 1.x → 2.0 (bounded to removed aliases/functions)

| Field | Evidence |
| --- | --- |
| **Exact break** | ~100 removed main-namespace members: type aliases (`np.float_`, `np.complex_`, `np.string_`, `np.unicode_`), constants (`np.NaN`, `np.Inf`, `np.NINF`/`np.PINF`), functions (`np.alltrue`, `np.sometrue`, `np.cumproduct`, `np.product`, `np.round_`, `np.asfarray`, `np.cast`, `np.mat`, and ~30 more). Source: [NumPy 2.0 migration guide](https://numpy.org/doc/2.0/numpy_2_0_migration_guide.html). |
| **Tier mix** | Overwhelmingly **Tier 1**: each is a 1:1 name/import substitution with a documented exact replacement (`np.NaN`→`np.nan`, `np.product()`→`np.prod()`, etc.). The `copy=` keyword behavior change and NEP 50 scalar-precision promotion are **Tier 3**, explicitly excluded from this bounded task. |
| **DSL expressibility** | Very high — this is close to the cleanest possible `rename_symbol`/`change_import` task in the candidate list: one-to-one substitutions, no argument restructuring, no receiver ambiguity (all under the `np.`/`numpy.` qualified namespace). |
| **Ambiguity** | Low. `np.NaN`, `np.float_`, etc. are qualified attribute accesses on the `numpy` module; alias/shadowing risk exists only if a project defines its own `NaN`-like name, which scope-aware matching should catch. |
| **Repository supply** | Not independently counted. NumPy is a near-universal dependency for scientific/data Python; supply is very likely high, but as with pandas, still-maintained old-version (NumPy <2.0) test clients may thin out over time — check in Phase 6, not assumed. |
| **Old-pass → new-fail reproducibility** | **Not probed in M0** (documented only). Expected trivially reproducible (`AttributeError: module 'numpy' has no attribute 'NaN'`), but not independently observed this pass. |
| **Oracle quality** | Strong: each removed name raises `AttributeError` immediately at import/use; a repository's own test collection will typically surface this without an external probe. |
| **Setup difficulty** | Low-moderate; NumPy has prebuilt wheels for common platforms, but native/compiled-extension client code (Cython, C extensions using the NumPy C-API) could raise setup difficulty — screen for pure-Python-API clients first. |
| **Existing codemods** | **Yes — official**: `ruff check --select NPY201` (Ruff ≥0.4.8) automatically migrates this exact surface. This is a strong Arm F (official/expert) comparator. |
| **Estimated experiment cost** | Low for the bounded rename task; the existence of a mature official codemod (Ruff NPY201) also makes this the cheapest candidate to validate Molt's rule against a real comparator. |
| **Admission risk** | Low, provided the task stays bounded to the removed-alias list and excludes `copy=`/NEP 50 behavioral changes. Its similarity to PyJWT's Tier-1 slice raises a diversity question — see the pilot recommendation below. |

---

## 5. HTTPX: `app=` shortcut removal (0.28.0)

| Field | Evidence |
| --- | --- |
| **Exact break** | `httpx.Client(app=...)` / `AsyncClient(app=...)` raises because the `app=` shortcut was removed in **0.28.0** (deprecated in 0.27.0, per the project's own changelog: "The deprecated `app` argument has now been removed" — [CHANGELOG.md](https://raw.githubusercontent.com/encode/httpx/master/CHANGELOG.md)). The `proxies=` argument was removed in the same release. Replacement: `transport=httpx.ASGITransport(app=app)` (async) or `httpx.WSGITransport(app=app)` (sync). |
| **Tier mix** | **Tier 2**: this is a call-shape change — a keyword argument on `Client(...)` must become a constructor call wrapped into a new `transport=` keyword, not a simple rename. `proxies=` removal (no direct replacement keyword; must restructure to `mounts=`) is a separate, somewhat harder Tier 2/3 case. |
| **DSL expressibility** | The `app=` case is plausibly within `replace_call`'s reach if it can wrap a captured argument inside a new call (`ASGITransport(app=<captured>)`) assigned to a renamed keyword — this exercises a genuinely different capability than PyJWT/NumPy's flat renames and should be treated as a Phase 1 fixture question, not assumed solved. |
| **Ambiguity** | Low-moderate: `Client`/`AsyncClient` are httpx-specific qualified names, but `app=` as a keyword is generic enough (many frameworks use `app=`) that syntax-only matching could misfire; qualified-name matching on the receiver class should resolve most of this. |
| **Repository supply** | **Admission risk explicitly flagged in the roadmap**: `app=` is primarily used to wire a test client to an ASGI/WSGI app in **test code**, which risks failing the roadmap's production-source admission contract ("Reject patches that... write outside allowed production Python source paths" and "test-only usage can fail the production-source admission contract"). This needs a real screening pass before admission; not resolved here. |
| **Old-pass → new-fail reproducibility** | **Not probed in M0.** Would require constructing a minimal ASGI/WSGI app fixture; deferred, not performed this pass (see `not_probed_documented_only` in [feasibility_probes.json](../experiments/feasibility_probes.json)). |
| **Oracle quality** | Likely strong if the break is in production code path (immediate `TypeError` on unexpected kwarg), weak/inapplicable if confined to test fixtures that themselves need migrating (out of scope per the roadmap's test-migration exclusion). |
| **Setup difficulty** | Low technically (pure-Python, async-capable), but admission screening (finding a repo where `app=` is used in *production* source, not just its own test suite) may be the harder part. |
| **Existing codemods** | None found. |
| **Estimated experiment cost** | Low-moderate if a qualifying production-source repository is found; screening cost could be nontrivial given the test-code admission risk above. |
| **Admission risk** | Real and specific: likely to reject a meaningful fraction of candidate repositories on the production-source rule. Treat as an **expansion candidate**, not a pilot, until a production-source instance is confirmed. |

---

## 6. SQLAlchemy 1.4/1.3 → 2.0 (bounded to `select()` list-argument form)

| Field | Evidence |
| --- | --- |
| **Exact break** | `select([col1, col2])` (list-argument form) raises; SQLAlchemy 2.0 requires positional arguments: `select(col1, col2)`. Source: [SQLAlchemy 2.0 migration guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html); confirmed by direct reproduction. The migration guide also documents `Query.get()`→`Session.get()`, `engine.execute()`/connectionless execution removal, and DML constructor keyword removal, all excluded from this bounded task (Tier 2/3, broader ORM restructuring). |
| **Tier mix** | **Tier 2** — the specific bounded task is a clean structural call-shape rewrite: unwrap a single list argument into positional arguments at a specific, qualified call site (`sqlalchemy.select`). This is exactly the "meaningful Tier 2" role the roadmap asks the pilot set to cover. |
| **DSL expressibility** | Good match for restricted `replace_call`: capture each element of the list argument and re-emit as positional arguments to the same callable. A single, well-defined operation shape, unlike the ORM-wide `Query`→`select()`/`Session.execute()` restructuring (out of scope — that is closer to Tier 3 given the semantic changes to result rows, `.scalars()`, `.unique()`). |
| **Ambiguity** | Moderate: `select` is a common name (e.g. `select` in `typing`, HTML forms, other ORMs); qualified-name matching on `sqlalchemy.select`/`sa.select` should resolve most cases, but aliasing (`from sqlalchemy import select as sel`) and local shadowing must be handled — a good adversarial-fixture source. |
| **Repository supply** | Not independently counted. SQLAlchemy is one of the most-used Python ORMs/SQL toolkits; supply is plausibly high among data/web-backend repositories. |
| **Old-pass → new-fail reproducibility** | **Probed and confirmed** (2026-09-05, SQLAlchemy 1.3.24 → 2.0.35): `select([t.c.x, t.c.y])` compiles fine on 1.3.24; raises `sqlalchemy.exc.ArgumentError` on 2.0.35 with a message that literally suggests the fix ("Did you mean to say select(Column(...), ...)"). |
| **Oracle quality** | Strong for this specific site class: the break is a **query-construction-time** `ArgumentError`, reproducible without a live database connection or fixture data — a repository's test suite need only import/build the query to hit it, and additionally SQLite is available for repositories whose tests execute the query. This meaningfully **lowers setup difficulty** relative to the broader SQLAlchemy ORM-behavior surface. |
| **Setup difficulty** | Low for the bounded `select()` task (no external DB service required for construction-time verification; SQLite suffices for repositories that also execute queries in tests). Higher if a candidate repository's tests need a real Postgres/MySQL service — screen for this per repository. |
| **Existing codemods** | No official automated codemod; the migration guide's own "Codemods" section (per search results) is documentation-driven guidance, not a runnable, general-purpose tool. `sqlalchemy2-stubs` is a typing-only artifact, not a code transformer. This makes SQLAlchemy a case with **no strong Arm F comparator** for the bounded task — disclose as "not available," not a failed run. |
| **Estimated experiment cost** | Moderate. Richer operation shape than a flat rename (list-to-positional unwrapping), but the DB-free oracle for the bounded site keeps verification cost down. |
| **Admission risk** | Low for the bounded `select()` scope specifically; the temptation to expand into the full 1.4→2.0 ORM surface (which is largely Tier 3) must be resisted for this experiment. |

---

## 7. urllib3 1.x → 2.0

| Field | Evidence |
| --- | --- |
| **Exact break** | Removed: `strict` parameter (`HTTPResponse`), `urllib3.contrib.ntlmpool`, `urllib3.contrib.securetransport`, the `urllib3[secure]` extra. Renamed: `VerifiedHTTPSConnection`→`HTTPSConnection` (import path also changed — no longer importable from `connectionpool`). Deprecated-toward-removal: `ssl_version`→`ssl_minimum_version`. Behavioral (Tier 3, excluded): minimum TLS version raised to 1.2, request-body encoding ISO-8859-1→UTF-8, default cipher list removed in favor of system ciphers, hostname verification now `subjectAltName`-only. Source: [urllib3 v2 migration guide](https://urllib3.readthedocs.io/en/stable/v2-migration-guide.html). |
| **Tier mix** | **Tier 1** for the parameter/module removals and the class rename; **Tier 3** for the TLS/encoding/cipher behavioral changes (excluded from the bounded task). |
| **DSL expressibility** | High for the bounded Tier 1 slice: `remove_argument`(`strict`), `change_import`(`VerifiedHTTPSConnection`→`HTTPSConnection`, correcting the import path), `rename_argument`(`ssl_version`→`ssl_minimum_version`). No structural call-shape change needed. |
| **Ambiguity** | Low-moderate: `strict=` and `ssl_version=` are somewhat generic keyword names that could appear on unrelated classes; qualified receiver-type evidence (is this actually a `urllib3.HTTPConnectionPool`/`HTTPResponse`?) matters, but urllib3's own class names are distinctive enough to reduce collision risk relative to, say, `.append()`. |
| **Repository supply** | Not independently counted. urllib3 is a near-ubiquitous transitive dependency (via `requests` and others), but *direct, production-source* use of the specific removed parameters (rather than transitive/vendored use through `requests`) may be a much smaller population — an open admission risk parallel to the HTTPX one. |
| **Old-pass → new-fail reproducibility** | **Not probed in M0** (documented only). Expected straightforward to reproduce (`TypeError: unexpected keyword argument` or `ImportError`), but not independently observed this pass. |
| **Oracle quality** | Likely strong for the bounded Tier 1 slice (immediate `TypeError`/`ImportError`); the excluded Tier 3 TLS/encoding changes would need behavioral probes (e.g. an actual TLS handshake or cipher negotiation), which is a materially higher-setup oracle not attempted here. |
| **Setup difficulty** | Low; pure-Python with C-accelerated SSL bindings via the standard library, no external service required for the bounded parameter-removal task. |
| **Existing codemods** | None found. |
| **Estimated experiment cost** | Low for the bounded Tier 1 slice. |
| **Admission risk** | Chief risk is finding repositories with *direct* (not merely transitive) urllib3 API usage of the specific removed surface — screen explicitly in Phase 6 rather than assuming prevalence from urllib3's overall popularity. |

---

## 8. pandas 2.x → 3.0 (recent/low-exposure slot)

| Field | Evidence |
| --- | --- |
| **Exact break** | Released **2026-01-21** — this is at or after Claude's disclosed January 2026 training cutoff, making it the strongest low-exposure candidate in this list (an exposure proxy, not proof of training absence, per the roadmap's own caution). Confirmed removals: offset alias renames enforced (`M`→`ME`, `Q`→`QE`, `Y`→`YE`, etc. — old aliases now raise), `copy=` keyword removed from ~20 methods (`truncate`, `astype`, `reindex`, `rename`, `merge`, etc.), `Index.sort()` always raised, `verify_integrity` removed from `set_index()`, `arg=` removed from `Series.map()` (use `func=`), `SettingWithCopyWarning` removed. Source: [pandas 3.0.0 whatsnew](https://pandas.pydata.org/docs/whatsnew/v3.0.0.html). |
| **Tier mix** | Clean **Tier 1** slice available: the offset-alias renames (`M`→`ME` etc.) are pure string-literal/name substitutions — arguably the single cleanest `rename_symbol`-style task in this entire list, since the "identifier" being renamed is a string passed to a constructor/`resample()`/`freq=` argument, not a Python symbol (a genuinely different DSL exercise: text-literal renaming inside typed argument positions). **Tier 2**: `copy=` keyword removal across ~20 methods (`remove_argument`, repeated across many call sites — good reuse-of-one-operation-many-sites test). **Tier 3** (excluded): Copy-on-Write default, string dtype default, datetime/timedelta resolution inference, `zoneinfo` default. |
| **DSL expressibility** | The offset-alias rename is expressible but is a **new capability relative to the other candidates**: it requires recognizing a string literal in an argument/frequency-string position as the rename target, not a Python identifier — flag as a Phase 1 fixture question (does the frozen DSL as scoped in the README cover string-literal targets, or only symbols/imports/arguments?). The `copy=` removal across many methods is a straightforward repeated `remove_argument`. |
| **Ambiguity** | Low for the qualified offset classes (`pd.offsets.MonthEnd`, `freq="M"` in pandas-specific contexts) but genuine risk that a bare string `"M"` appears in many non-pandas contexts (dict keys, unrelated config) — this is actually a **different kind of ambiguity** than receiver-type ambiguity: it is string-literal-in-context ambiguity, valuable as a second, distinct ambiguity case if pursued. |
| **Repository supply** | **Low**, by construction — this is a released-January-2026 major version; few production repositories will have upgraded yet, and "old-pass" (pandas <3.0, still widely deployed) supply is presumably large but "genuinely attempted the 3.0 upgrade already" supply is thin. This is the central admission risk: recency buys low exposure at the cost of client-repository availability. |
| **Old-pass → new-fail reproducibility** | **Not probed in M0** (documented only, via official whatsnew page dated 2026-01-21). |
| **Oracle quality** | Strong for the enforced-alias and removed-`copy=`-kwarg sites (immediate `ValueError`/`TypeError`); weak/inapplicable for the Tier 3 CoW/dtype defaults (excluded). |
| **Setup difficulty** | Same as pandas 2.0 (see above), plus a possibly narrower set of compatible transitive-dependency versions given how recent 3.0 is — worth checking NumPy/PyArrow minimum-version compatibility (pandas 3.0 requires NumPy ≥1.26, PyArrow ≥13 per its own whatsnew) before assuming easy setup. |
| **Existing codemods** | None found (too recent). |
| **Estimated experiment cost** | Low for the bounded Tier 1/2 slice; the real cost driver is **repository discovery**, not verification or generation. |
| **Admission risk** | The most exposure-favorable and the most supply-constrained candidate simultaneously — exactly the tension the roadmap's exposure section anticipates ("If no qualifying migration meets viability criteria, publish the search evidence and limitation before freezing"). Treat as a **stretch/expansion candidate** pending a real supply check, not a guaranteed pilot slot. |

---

## Rejected lead: attrs modernization

**Rejected on first evidence, per the roadmap's own replacement rule** ("Replace this lead if no genuine target failure is found"). Fetched [attrs naming docs](https://www.attrs.org/en/stable/names.html) directly: "The traditional, or *OG*, APIs `attr.s()` / `attr.ib()`... will stay **forever**." The old and new APIs coexist with no deprecation warning and no functional break. This is modernization, not a breaking upgrade, and fails the roadmap's admission contract outright (no old-pass/target-fail pair exists). **Replaced by urllib3 1→2** above, which the roadmap explicitly permits as a substitute discovered candidate.

---

## Comparative ranking

| Candidate | Tier mix | DSL fit | Ambiguity | Supply (qualitative) | Reproduced? | Oracle | Setup | Codemod comparator | Cost (qual.) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PyJWT 1→2 (bounded) | 1 (+2 excluded) | High | Low-mod | High (unmeasured) | **Yes** | Strong | Low | None | Low |
| pandas 1→2 (bounded) | 1/2 mixed | High/edge-case | High (`.append()`) | Very high (unmeasured) | No | Strong | Low-mod | None (for this surface) | Moderate |
| Pydantic 1→2 (bounded) | 1 (narrow) | High for bounded scope | **High** | High (unmeasured) | **Yes** | Strong (bounded) / weak (popular surface) | Low-mod | bump-pydantic (archived) | Moderate-high |
| NumPy 1→2 (bounded) | 1 | Very high | Low | Very high (unmeasured) | No | Strong | Low-mod | **Ruff NPY201 (official)** | Low |
| HTTPX `app=` | 2 | Medium (new capability) | Low-mod | Uncertain (test-code risk) | No | Uncertain | Low (tech) / high (screening) | None | Low-mod |
| SQLAlchemy `select()` (bounded) | 2 | High | Moderate | High (unmeasured) | **Yes** | Strong | Low (DB-free) | None | Moderate |
| urllib3 1→2 (bounded) | 1 | High | Low-mod | Uncertain (direct-use risk) | No | Strong (est.) | Low | None | Low |
| pandas 3.0 (bounded) | 1/2 mixed | High + new capability (string literals) | Low/novel | **Low** (too recent) | No | Strong (est.) | Low-mod | None | Low + discovery cost |

---

## Recommended pilot (~3 migrations)

1. **Anchor (Tier 1, simple): PyJWT 1→2, bounded to the exception rename + options-dict restructuring.** The only candidate with a fully reproduced old-pass→new-fail break, a strong unambiguous oracle, low setup cost, and a genuinely small operation count. NumPy's bounded slice is comparably clean but would duplicate PyJWT's role without adding diversity; keep NumPy in the registered expansion pool instead (and its Ruff NPY201 comparator makes it a good **second-wave** addition once budget allows).
2. **Meaningful Tier 2: SQLAlchemy `select()` list-to-positional rewrite.** Reproduced, DB-free oracle (a real setup-difficulty win over most Tier 2 candidates), a genuine structural call-shape change exercising `replace_call` beyond flat renames, and real (if moderate) ambiguity from aliasing/shadowing — satisfies the roadmap's "meaningful Tier 2 structure" role without pulling in SQLAlchemy's much harder ORM-wide Tier 3 surface.
3. **Ambiguity/DSL-ceiling case: Pydantic 1→2, bounded to genuinely-removed imports, with the popular-but-shimmed surface documented as the DSL-ceiling discussion.** This is the most scientifically interesting candidate precisely because of what the probe found: naive scoping from the migration guide would silently violate the admission contract (deprecation warnings are not failures), and the `.dict()`/`.json()` name-collision risk is a direct, testable instance of the matching-ambiguity question RQ4 asks about. Its bounded-import task is cheap and strongly oracled; its documented ceiling is where the DSL-limits story gets told.

**Why not HTTPX, urllib3, or pandas 3.0 as pilot slots:** all three carry a live, unresolved *supply* risk (HTTPX: test-code-only usage; urllib3: direct-vs-transitive usage; pandas 3.0: too recent for adopted clients) that a 3–5 development-repository pilot cannot absorb without first checking real repository availability. They are strong **expansion-phase candidates** (register them in the Phase 0 expansion pool below) rather than pilot picks, consistent with "Selection optimizes diversity, credible failure evidence, and reproducibility, not expected Molt wins." pandas 1→2 is a strong second-wave Tier 2 candidate once the `.append()` ambiguity fixture cost is budgeted; it was not chosen as the pilot's Tier 2 slot only because SQLAlchemy's DB-free oracle and confirmed reproduction gave it a feasibility edge for a first pilot under M0's evidence bar.

**Registered expansion order (post-pilot, pending M6 numeric ceilings — see [experiments/protocol.md](../experiments/protocol.md)):** NumPy (bounded) → pandas 1→2 (bounded) → urllib3 (bounded) → HTTPX (pending production-source screening) → pandas 3.0 (pending supply screening). This order is provisional and explicitly **not** a numeric commitment; exact ceilings, family counts, and stopping rules remain open per the protocol.
