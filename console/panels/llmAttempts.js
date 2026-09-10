import { fetchJson, escapeHtml, badge, calloutRealSection, calloutMockSection } from "./_util.js";

export async function render(root) {
  const [mock, config, ceilings] = await Promise.all([
    fetchJson("./mock/llm_attempts.json"),
    fetchJson("../../experiments/pilot_config.json"),
    fetchJson("../../experiments/ceilings.json"),
  ]);

  root.innerHTML = `
    <h1>LLM Generation / Repair Attempts</h1>
    <p class="panel-intro">Will eventually render <code>inference/</code> (Phase 3) and <code>repair/controller.py</code> (Phase 5) attempt lineage: proposal validity, schema errors, parent/child rule hashes, and terminal status.</p>

    <h2>Configured PyJWT pilot ${badge("real", "real")}</h2>
    ${calloutRealSection(
      "Real config, zero calls made",
      "This section reads experiments/pilot_config.json and experiments/ceilings.json directly — a real, frozen M0 decision, not mock data. The status line below is the actual reason no attempt has run."
    )}
    <div class="card">
      <div class="card-title">${escapeHtml(config.model_id)} <span class="tag">${escapeHtml(config.provider)}</span> <span class="tag tag-mixed">${escapeHtml(config.status)}</span></div>
      <div class="card-grid">
        <dt>Scope</dt><dd>${escapeHtml(config.scope)}</dd>
        <dt>Generation replicates</dt><dd>${escapeHtml(String(config.generation_replicates_pyjwt_pilot))}</dd>
        <dt>Repair proposal sweep</dt><dd>${(config.repair_proposal_sweep || []).join(", ")} (paired-prefix trajectory)</dd>
        <dt>Max output tokens</dt><dd>${escapeHtml(String(config.request_parameters.max_output_tokens))}</dd>
        <dt>Retry ceiling</dt><dd>${escapeHtml(String(config.retry_and_timeout_policy.max_transport_retries_per_request))} transport retries, ${escapeHtml(String(config.retry_and_timeout_policy.request_timeout_seconds))}s timeout</dd>
        <dt>Spend ceiling</dt><dd>$${escapeHtml(String(ceilings.spend_ceilings.pyjwt_pilot_hard_spend_ceiling_usd))} hard cap (~40x the projected worst case — see Cost/Tokens panel)</dd>
        <dt>Evidence packet</dt><dd><a href="../../experiments/pilot_evidence_packet.md">pilot_evidence_packet.md</a> (real, measured size — see Cost/Tokens panel)</dd>
      </div>
    </div>

    <h2>Attempt table</h2>
    ${calloutMockSection(
      "Zero model calls have been made by this project",
      "Every row below is status 'not_run' by construction: no inference or repair module exists, and the configured pilot above has not been executed (blocked on a billable API key and spend authorization — see protocol.md §12). This table shows the intended attempt-lineage shape only."
    )}
    <table>
      <thead><tr><th>Attempt</th><th>Proposal #</th><th>Status</th><th>Schema valid</th><th>Note</th></tr></thead>
      <tbody>
        ${mock.attempts
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
