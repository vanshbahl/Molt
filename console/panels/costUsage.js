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
    fetchJson("../../experiments/pilot_config.json"),
    fetchJson("../../experiments/pilot_estimate.json"),
  ]);
  const price = config.price_schedule;
  const proj = estimate.cost_projection_usd;

  root.innerHTML = `
    <h1>Cost / Token Usage</h1>
    <p class="panel-intro">Will eventually render the per-request ledger ROADMAP.md requires (uncached/cached input tokens, output tokens, reasoning tokens, billed cost, model/provider, price schedule date) plus cumulative/amortized cost curves (Phase 9).</p>

    <h2>Real, dated price schedule</h2>
    <div class="card">
      <div class="card-title">${escapeHtml(price.model)} <span class="tag">fetched ${escapeHtml(price.fetched_at)}</span></div>
      <div class="card-grid">
        <dt>Input</dt><dd>$${price.input_usd_per_mtok}/MTok</dd>
        <dt>Output</dt><dd>$${price.output_usd_per_mtok}/MTok</dd>
        <dt>Cache write</dt><dd>$${price.prompt_cache_write_usd_per_mtok}/MTok</dd>
        <dt>Cache read</dt><dd>$${price.prompt_cache_read_usd_per_mtok}/MTok</dd>
        <dt>Source</dt><dd><a href="${escapeHtml(price.source)}" target="_blank" rel="noopener">${escapeHtml(price.source)}</a></dd>
      </div>
    </div>

    <h2>PyJWT pilot cost projection</h2>
    ${calloutEstimateSection(
      "Projection from a real measured artifact + the real price schedule above, NOT a billed cost",
      "experiments/pilot_estimate.json: input-token estimate is derived from the real character/word count of experiments/pilot_evidence_packet.md via two disclosed heuristics; output-token size is an explicit assumption, not a measurement. No request has been sent."
    )}
    <table>
      <thead><tr><th>Scenario</th><th>Estimated cost (USD)</th><th>Basis</th></tr></thead>
      <tbody>
        <tr><td>Single uncached request</td><td>~$${proj.single_uncached_request_point_estimate}</td><td>${escapeHtml(proj.single_uncached_request_note)}</td></tr>
        <tr><td>Full 5-request trajectory (1/2/3/5 sweep, cached)</td><td>~$${proj.full_5_request_trajectory_with_caching_point_estimate}</td><td>${escapeHtml(proj.full_5_request_trajectory_note)}</td></tr>
        <tr><td>Full pilot, 2 replicates (point estimate)</td><td>~$${proj.two_replicate_pilot_point_estimate}</td><td>${escapeHtml(proj.interpretation)}</td></tr>
        <tr><td>Full pilot, 2 replicates (worst case)</td><td>~$${proj.two_replicate_pilot_worst_case_estimate}</td><td>${escapeHtml(proj.two_replicate_pilot_worst_case_assumptions)}</td></tr>
      </tbody>
    </table>
    <p class="panel-intro">Not estimated at all (no basis exists without an observed request): ${escapeHtml(Object.keys(estimate.not_estimated_at_all).join(", "))}. See <a href="../../experiments/pilot_estimate.json">pilot_estimate.json</a> for each field's caveat.</p>

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
