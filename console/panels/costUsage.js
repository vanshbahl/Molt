import { fetchJson, escapeHtml, calloutMockSection } from "./_util.js";

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
  const data = await fetchJson("./mock/cost_usage.json");

  root.innerHTML = `
    <h1>Cost / Token Usage</h1>
    <p class="panel-intro">Will eventually render the per-request ledger ROADMAP.md requires (uncached/cached input tokens, output tokens, reasoning tokens, billed cost, model/provider, price schedule date) plus cumulative/amortized cost curves (Phase 9).</p>
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
