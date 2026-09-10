# Molt dev console

**Not a product UI.** This is a small, throwaway, developer-only static site for visually inspecting Molt's data as backend modules get built (rules/, transform/, verification/, inference/, repair/, benchmark/). It has no build step, no server-side code, no auth, no database, and no dependency on any Molt Python package existing — it just reads static JSON/text files with `fetch`. Delete or rewrite it at any time without touching `src/`.

## Run it

Static files with relative `fetch()` calls need to be served over HTTP — opening `index.html` directly as a `file://` URL will fail those fetches in most browsers. From the repository root:

```bash
python3 -m http.server 8420
```

Then open `http://localhost:8420/console/`.

## What's real vs mock vs estimate

Every panel is labeled with a badge:

| Badge | Meaning |
| --- | --- |
| 🟢 `real` | Reads a real file produced by actual M0 work: research, a real zero-cost probe, or a frozen configuration decision. |
| 🟣 `estimate / projection, not measured` | Reads a real artifact (e.g. a measured file size, a dated public price schedule) run through a disclosed projection method. **Never** a billed/observed number — see [experiments/pilot_estimate.json](../experiments/pilot_estimate.json). |
| 🟡 `mock / not implemented` | Reads a placeholder file under `console/mock/`. The corresponding Molt module does not exist yet; the panel exists only so its layout is ready when the module lands. |

| Panel | Status | Backed by |
| --- | --- | --- |
| Migration Candidates | 🟢 real | `experiments/candidates.json` (this M0 pass's research) |
| Repo / Test Status | 🟢 real (probes) + 🟡 mock (per-repo status) | `experiments/feasibility_probes.json` + `console/mock/repo_status.json` |
| Rule JSON / Schema | 🟢 real (pilot's requested output shape) + 🟡 mock (illustrative bundle) | `experiments/pilot_evidence_packet.md` + `console/mock/rule_schema.json` — Phase 1 (`rules/`) not built |
| Transformation Diff | 🟢 real (exemplar, hand-diffed) | `experiments/pilot_evidence_packet.md` — Phase 2 (`transform/`) not built, so no engine produced the diff, but the before/after content is the real frozen M0 exemplar |
| Verification Results | 🟢 real (bounded-task site probe) + 🟡 mock (full harness stages) | `experiments/feasibility_probes.json` + `console/mock/verification_results.json` — Phase 4 (`verification/`) not built |
| LLM Gen / Repair | 🟢 real (pilot config) + 🟡 mock (attempt table) | `experiments/pilot_config.json` + `experiments/ceilings.json` + `console/mock/llm_attempts.json` — Phases 3/5 not built, zero model calls made |
| Cost / Tokens | 🟣 estimate (price schedule + cost projection) + 🟡 mock (empty billed ledger) | `experiments/pilot_config.json` + `experiments/pilot_estimate.json` + `console/mock/cost_usage.json` — no billed usage exists |
| Raw Logs / Errors | 🟢 real (probe output, including the fresh bounded-task probe) + 🟡 mock (harness log shape) | `experiments/probe_logs.txt` + `console/mock/logs.json` |

## Adding a real panel later

When a module lands (e.g. `rules/schema.py` in Phase 1), point that panel's `fetch()` at the module's real output instead of `console/mock/*.json`, update its badge from `mock` to `real` in `_util.js`'s call site, and delete the now-unused mock file. Each panel is one small ES module in `console/panels/` with a single `render(root)` export — there is no shared state, router logic, or build config to touch.

## Design constraints (deliberate)

- No framework, no bundler, no `package.json`, no npm install. Vanilla HTML/CSS/JS with native ES modules (`<script type="module">`, dynamic `import()`).
- No write path anywhere — every panel only ever calls `fetch()` on a static file.
- No auth, no database, no long-running process beyond a plain static file server.
- Everything here is disposable. If Molt's real schema/output shapes diverge from what a panel currently renders, rewrite the panel; nothing else in the repository depends on this directory.
