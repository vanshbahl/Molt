import { fetchJson, escapeHtml, badge, calloutRealSection } from "./_util.js";

// Renders a molt.engine_result.v1 document (DOCS/ENGINE.md). The committed
// sample is produced by experiments/engine_runs/generate.py.
function renderDiff(diff) {
  if (!diff) return "(no changes)";
  return diff
    .split("\n")
    .map((line) => {
      const cls = line.startsWith("+++") || line.startsWith("---") || line.startsWith("@@")
        ? "diff-ctx"
        : line.startsWith("+") ? "diff-add" : line.startsWith("-") ? "diff-del" : "diff-ctx";
      return `<span class="${cls}">${escapeHtml(line)}</span>`;
    })
    .join("\n");
}

export async function render(root) {
  const r = await fetchJson("./data/engine_result.json");
  const v = r.verification || {};
  const s = r.summary;

  root.innerHTML = `
    <h1>Transformation Diff Preview</h1>
    ${calloutRealSection(
      "Real engine output (molt.engine_result.v1)",
      `Produced by the Molt engine ${r.engine_version} applying ${r.rule.bundle_id} ${r.rule.bundle_version} to ${r.repo.path} in dry-run mode. Regenerate with experiments/engine_runs/generate.py.`
    )}
    <div class="card">
      <div class="card-title">Result ${badge(r.status === "PASS" ? "real" : "partial", r.status)} <span class="tag">${escapeHtml(r.reason)}</span></div>
      <div class="card-grid">
        <dt>Matched / changed / abstained</dt><dd>${s.matched} / ${s.changed} / ${s.abstained}</dd>
        <dt>Files scanned / with candidates / changed</dt><dd>${r.repo.files_scanned} / ${r.repo.files_with_candidates} / ${r.repo.files_changed}</dd>
        <dt>Verification</dt><dd><code>${escapeHtml((v.command || []).join(" ") || "(none)")}</code> → <span class="tag">${escapeHtml(v.status || "not_run")}</span></dd>
        <dt>Rule sha256</dt><dd><code>${escapeHtml(r.rule.sha256 || "")}</code></dd>
      </div>
    </div>

    <h2>Unified diff</h2>
    <pre class="json-view">${renderDiff(r.diff)}</pre>

    <h2>Sites</h2>
    <table>
      <thead><tr><th>File:line</th><th>Operation</th><th>Decision</th><th>Reason</th></tr></thead>
      <tbody>
        ${r.sites
          .map(
            (site) => `<tr><td>${escapeHtml(site.file)}:${site.line}</td><td>${escapeHtml(site.op_id)}</td><td><span class="tag ${
              site.decision === "changed" ? "tag-pass" : "tag-mixed"
            }">${escapeHtml(site.decision)}</span></td><td>${escapeHtml(site.reason)}</td></tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}
