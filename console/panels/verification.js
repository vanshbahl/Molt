import { fetchJson, escapeHtml, calloutMockSection } from "./_util.js";

export async function render(root) {
  const data = await fetchJson("./mock/verification_results.json");

  root.innerHTML = `
    <h1>Verification / Test Results</h1>
    <p class="panel-intro">Will eventually render <code>verification/runner.py</code>'s structured stage results (Phase 4) across syntax, install/build, typecheck, existing tests, and external probes, per ROADMAP.md's metrics table.</p>
    ${calloutMockSection(
      "No verification harness exists",
      "Every stage below is 'not_run' or 'not_applicable' by construction — none of this reflects a real check. The stage list itself is real (mirrors ROADMAP.md), only the results are placeholders."
    )}
    <div class="card">
      <div class="card-title">${escapeHtml(data.repo)} — ${escapeHtml(data.migration_id)} <span class="tag">${escapeHtml(
    data.arm
  )}</span></div>
      <table>
        <thead><tr><th>Stage</th><th>Status</th><th>Note</th></tr></thead>
        <tbody>
          ${data.stages
            .map(
              (s) => `<tr><td>${escapeHtml(s.stage)}</td><td><span class="tag">${escapeHtml(s.status)}</span></td><td>${escapeHtml(
                s.note || ""
              )}</td></tr>`
            )
            .join("")}
        </tbody>
      </table>
      <div><strong>Verified repository success:</strong> ${escapeHtml(data.verified_repository_success)}</div>
    </div>
  `;
}
