import { fetchJson, escapeHtml, badge, calloutRealSection, calloutMockSection } from "./_util.js";

export async function render(root) {
  const [data, probes] = await Promise.all([
    fetchJson("./mock/verification_results.json"),
    fetchJson("../../experiments/feasibility_probes.json"),
  ]);
  const boundedProbe = probes.probes.find((p) => p.candidate_id === "pyjwt-1-to-2-bounded-task");

  root.innerHTML = `
    <h1>Verification / Test Results</h1>
    <p class="panel-intro">Will eventually render <code>verification/runner.py</code>'s structured stage results (Phase 4) across syntax, install/build, typecheck, existing tests, and external probes, per ROADMAP.md's metrics table.</p>

    <h2>PyJWT bounded-task site verification ${badge("real", "real")}</h2>
    ${calloutRealSection(
      "Real old-pass/new-fail evidence for the exact two sites the pilot targets",
      "This is a single-script reproduction (see Repo/Test Status panel for the earlier, differently-scoped probe), not the Phase 4 harness above and not repository-level admission — it establishes that the pilot's frozen exemplar is grounded in a real, observed break, not a guess."
    )}
    ${
      boundedProbe
        ? `<div class="card">
            <div class="card-title">${escapeHtml(boundedProbe.library)} ${escapeHtml(boundedProbe.old_version)} → ${escapeHtml(boundedProbe.new_version)}</div>
            <div class="card-grid">
              <dt>Sites probed</dt><dd>${escapeHtml(boundedProbe.api_under_test)}</dd>
              <dt>Old (pass)</dt><dd><span class="tag tag-pass">${escapeHtml(boundedProbe.old_result.status)}</span> ${escapeHtml(boundedProbe.old_result.detail)}</dd>
              <dt>New (fail)</dt><dd><span class="tag tag-fail">${escapeHtml(boundedProbe.new_result.status)}</span> ${escapeHtml(boundedProbe.new_result.detail)}</dd>
              <dt>Conclusion</dt><dd>${escapeHtml(boundedProbe.conclusion)}</dd>
            </div>
          </div>`
        : `<p class="panel-intro">Probe record not found.</p>`
    }

    <h2>Full harness stage results (Phase 4, not built)</h2>
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
