import { fetchJson, escapeHtml, calloutMockSection } from "./_util.js";

export async function render(root) {
  const data = await fetchJson("./mock/diff_preview.json");

  const diffLines = data.diff
    .map((l) => {
      const prefix = l.type === "add" ? "+" : l.type === "del" ? "-" : " ";
      const cls = l.type === "add" ? "diff-add" : l.type === "del" ? "diff-del" : "diff-ctx";
      return `<span class="${cls}">${prefix} ${escapeHtml(l.text)}</span>`;
    })
    .join("\n");

  root.innerHTML = `
    <h1>Transformation Diff Preview</h1>
    <p class="panel-intro">Will eventually render <code>transform/report.py</code>'s dry-run diff output against a real repository (Phase 2). No engine exists yet.</p>
    ${calloutMockSection(
      "Hand-typed diff, not engine output",
      "This diff illustrates the PyJWT anchor's real, documented break (see the Migration Candidates / Repo Status panels) but was written by hand — no parser, matcher, or compiler produced it."
    )}
    <h2>${escapeHtml(data.file)}</h2>
    <pre class="json-view">${diffLines}</pre>

    <h2>Abstentions</h2>
    <p class="panel-intro">A rule can decline to edit a site it cannot safely resolve. This is a real design requirement (see README.md's bounded-rules section), illustrated here with mock content.</p>
    ${data.abstentions
      .map(
        (a) => `<div class="card"><div class="card-title">${escapeHtml(a.site)}</div><div>${escapeHtml(a.reason)}</div></div>`
      )
      .join("")}
  `;
}
