import { fetchJson, escapeHtml, calloutMockSection, calloutEstimateSection } from "./_util.js";

const COLUMNS = [
  "request_id",
  "model/provider",
  "uncached input tokens",
  "cached input tokens",
  "output tokens",
  "reasoning tokens",
  "billed cost",
  "price schedule date",
];

export async function render(root) {
  const [data, config, estimate] = await Promise.all([
    fetchJson("./mock/cost_usage.json"),
    fetchJson("./data/pilot_config.json"),
    fetchJson("./data/pilot_estimate.json"),
  ]);
  const price = config.price_schedule;
  const m = estimate.measured_inputs;
  const tok = estimate.token_estimation_method.estimated_input_tokens_per_request;
  const out = estimate.output_token_assumption.estimated_visible_output_tokens_per_request;

  root.innerHTML = `
    <h1>Cost / Token Usage</h1>
    <p class="panel-intro">Will eventually render the per-request ledger ROADMAP.md requires plus cumulative/amortized curves (Phase 9). Measured pilot runs land in experiments/measured_runs/ (none yet).</p>

    <h2>Configured price schedule</h2>
    <div class="card">
      <div class="card-title">${escapeHtml(price.model)} <span class="tag">${escapeHtml(price.tier)}</span> <span class="tag">checked ${escapeHtml(price.fetched_at)}</span></div>
      <div class="card-grid">
        <dt>Input / output</dt><dd>$${price.input_usd_per_mtok} / $${price.output_usd_per_mtok} per MTok (Free Tier)</dd>
        <dt>Applies when</dt><dd>${escapeHtml(price.note)}</dd>
        <dt>Source</dt><dd><a href="${escapeHtml(price.source)}" target="_blank" rel="noopener">${escapeHtml(price.source)}</a></dd>
      </div>
    </div>

    <h2>PyJWT pilot token projection</h2>
    ${calloutEstimateSection(
      "Projection from exact request-content counts, NOT observed usage",
      estimate.$comment
    )}
    <table>
      <thead><tr><th>Quantity</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Request content (packet + schema), chars</td><td>${m.user_content_chars}</td></tr>
        <tr><td>Estimated input tokens / request (low · point · high)</td><td>${tok.low} · ${tok.point} · ${tok.high}</td></tr>
        <tr><td>Assumed visible output tokens / request</td><td>${out.low} · ${out.point} · ${out.high} (thinking tokens unknown)</td></tr>
        <tr><td>Requests</td><td>${escapeHtml(String(estimate.requests.initial_proposals_per_run))} initial proposals; repair: ${escapeHtml(estimate.requests.repair_requests)}</td></tr>
        <tr><td>Monetary cost</td><td>${escapeHtml(estimate.monetary_cost.interpretation)}</td></tr>
      </tbody>
    </table>
    <p class="panel-intro">Not estimated at all: ${escapeHtml(Object.keys(estimate.not_estimated_at_all).join(", "))}.</p>

    <h2>Billed usage ledger</h2>
    ${calloutMockSection(
      "Ledger is empty by design, not populated with invented numbers",
      data.note
    )}
    <table>
      <thead><tr>${COLUMNS.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead>
      <tbody>
        ${
          data.ledger.length
            ? data.ledger.map((row) => `<tr>${COLUMNS.map((c) => `<td>${escapeHtml(row[c] ?? "")}</td>`).join("")}</tr>`).join("")
            : `<tr><td colspan="${COLUMNS.length}" style="text-align:center;color:var(--text-dim)">No requests recorded — zero LLM calls made by this project so far.</td></tr>`
        }
      </tbody>
    </table>
  `;
}
