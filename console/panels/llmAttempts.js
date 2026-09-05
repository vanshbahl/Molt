import { fetchJson, escapeHtml, calloutMockSection } from "./_util.js";

export async function render(root) {
  const data = await fetchJson("./mock/llm_attempts.json");

  root.innerHTML = `
    <h1>LLM Generation / Repair Attempts</h1>
    <p class="panel-intro">Will eventually render <code>inference/</code> (Phase 3) and <code>repair/controller.py</code> (Phase 5) attempt lineage: proposal validity, schema errors, parent/child rule hashes, and terminal status.</p>
    ${calloutMockSection(
      "Zero model calls have been made by this project",
      "No inference or repair module exists. Every attempt below is status 'not_run' by construction; this is a layout placeholder only."
    )}
    <table>
      <thead><tr><th>Attempt</th><th>Proposal #</th><th>Status</th><th>Schema valid</th><th>Note</th></tr></thead>
      <tbody>
        ${data.attempts
          .map(
            (a) => `<tr>
              <td>${escapeHtml(a.attempt)}</td>
              <td>${escapeHtml(a.proposal_index)}</td>
              <td><span class="tag">${escapeHtml(a.status)}</span></td>
              <td>${a.schema_valid === null ? "n/a" : escapeHtml(String(a.schema_valid))}</td>
              <td>${escapeHtml(a.note || "")}</td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}
