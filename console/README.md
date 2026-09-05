# Molt dev console

**Not a product UI.** This is a small, throwaway, developer-only static site for visually inspecting Molt's data as backend modules get built (rules/, transform/, verification/, inference/, repair/, benchmark/). It has no build step, no server-side code, no auth, no database, and no dependency on any Molt Python package existing — it just reads static JSON/text files with `fetch`. Delete or rewrite it at any time without touching `src/`.

## Run it

Static files with relative `fetch()` calls need to be served over HTTP — opening `index.html` directly as a `file://` URL will fail those fetches in most browsers. From the repository root:

```bash
python3 -m http.server 8420
```

Then open `http://localhost:8420/console/`.

## What's real vs mock

Every panel is labeled with a badge:

| Badge | Meaning |
| --- | --- |
| 🟢 `real` | Reads a real file produced by actual M0 work: [`experiments/candidates.json`](../experiments/candidates.json), [`experiments/feasibility_probes.json`](../experiments/feasibility_probes.json), [`experiments/probe_logs.txt`](../experiments/probe_logs.txt). |
| 🟡 `mock / not implemented` | Reads a placeholder file under `console/mock/`. The corresponding Molt module does not exist yet; the panel exists only so its layout is ready when the module lands. |

| Panel | Status | Backed by |
| --- | --- | --- |
| Migration Candidates | 🟢 real | `experiments/candidates.json` (this M0 pass's research) |
| Repo / Test Status | 🟢 real (probes) + 🟡 mock (per-repo status) | `experiments/feasibility_probes.json` + `console/mock/repo_status.json` |
| Rule JSON / Schema | 🟡 mock | `console/mock/rule_schema.json` — Phase 1 (`rules/`) not built |
| Transformation Diff | 🟡 mock | `console/mock/diff_preview.json` — Phase 2 (`transform/`) not built |
| Verification Results | 🟡 mock | `console/mock/verification_results.json` — Phase 4 (`verification/`) not built |
| LLM Gen / Repair | 🟡 mock | `console/mock/llm_attempts.json` — Phases 3/5 not built, zero model calls made |
| Cost / Tokens | 🟡 mock (intentionally empty ledger) | `console/mock/cost_usage.json` — no billed usage exists |
| Raw Logs / Errors | 🟢 real (probe output) + 🟡 mock (harness log shape) | `experiments/probe_logs.txt` + `console/mock/logs.json` |

## Adding a real panel later

When a module lands (e.g. `rules/schema.py` in Phase 1), point that panel's `fetch()` at the module's real output instead of `console/mock/*.json`, update its badge from `mock` to `real` in `_util.js`'s call site, and delete the now-unused mock file. Each panel is one small ES module in `console/panels/` with a single `render(root)` export — there is no shared state, router logic, or build config to touch.

## Design constraints (deliberate)

- No framework, no bundler, no `package.json`, no npm install. Vanilla HTML/CSS/JS with native ES modules (`<script type="module">`, dynamic `import()`).
- No write path anywhere — every panel only ever calls `fetch()` on a static file.
- No auth, no database, no long-running process beyond a plain static file server.
- Everything here is disposable. If Molt's real schema/output shapes diverge from what a panel currently renders, rewrite the panel; nothing else in the repository depends on this directory.
