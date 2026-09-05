import { fetchJson, escapeHtml, badge, calloutRealSection } from "./_util.js";

export async function render(root) {
  const data = await fetchJson("../../experiments/candidates.json");

  const pilotSet = new Set(data.pilot_recommendation || []);

  root.innerHTML = `
    <h1>Migration Candidates ${badge("real", "real")}</h1>
    <p class="panel-intro">M0 candidate scorecards, generated ${escapeHtml(
      data.generated_at
    )}. Source of truth: <a href="../../DOCS/CANDIDATES.md">DOCS/CANDIDATES.md</a>; this table mirrors <a href="../../experiments/candidates.json">experiments/candidates.json</a> directly — nothing here is invented for the console.</p>
    ${calloutRealSection(
      "Status",
      data.status
    )}
    <h2>Candidates (${data.candidates.length})</h2>
    <table>
      <thead><tr>
        <th>Library</th><th>Role</th><th>Tier mix</th><th>Ambiguity</th><th>Reproduced?</th><th>Cost</th>
      </tr></thead>
      <tbody>
        ${data.candidates
          .map((c) => {
            const isPilot = pilotSet.has(c.id);
            const repro = c.reproducibility && c.reproducibility.probed;
            const reproTag = repro
              ? `<span class="tag tag-pass">probed</span>`
              : `<span class="tag">documented only</span>`;
            return `<tr>
              <td><strong>${escapeHtml(c.library)}</strong>${isPilot ? ' <span class="tag tag-pass">PILOT</span>' : ""}</td>
              <td>${escapeHtml(c.role)}</td>
              <td>${(c.tier_mix || []).map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join(" ")}</td>
              <td>${escapeHtml(c.ambiguity || "")}</td>
              <td>${reproTag}</td>
              <td>${escapeHtml(c.estimated_cost || "")}</td>
            </tr>`;
          })
          .join("")}
      </tbody>
    </table>

    <h2>Recommended pilot (3)</h2>
    <div id="pilot-cards"></div>

    <h2>Rejected leads</h2>
    <div id="rejected-cards"></div>

    <h2>Full scorecards</h2>
    <div id="all-cards"></div>
  `;

  const pilotEl = root.querySelector("#pilot-cards");
  data.candidates
    .filter((c) => pilotSet.has(c.id))
    .forEach((c) => pilotEl.appendChild(card(c, true)));

  const rejEl = root.querySelector("#rejected-cards");
  (data.rejected || []).forEach((r) => {
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `<div class="card-title">${escapeHtml(r.library)} <span class="tag tag-fail">rejected</span></div>
      <div>${escapeHtml(r.reason)}</div>`;
    rejEl.appendChild(el);
  });

  const allEl = root.querySelector("#all-cards");
  data.candidates.forEach((c) => allEl.appendChild(card(c, pilotSet.has(c.id))));
}

function card(c, isPilot) {
  const el = document.createElement("div");
  el.className = "card";
  const repro = c.reproducibility || {};
  const supply = c.repository_supply || {};
  el.innerHTML = `
    <div class="card-title">
      ${escapeHtml(c.library)}
      ${isPilot ? '<span class="tag tag-pass">PILOT</span>' : '<span class="tag">expansion candidate</span>'}
    </div>
    <div class="card-grid">
      <dt>Role</dt><dd>${escapeHtml(c.role)}</dd>
      <dt>Versions</dt><dd>${escapeHtml(c.versions.old)} → ${escapeHtml(c.versions.new)}</dd>
      <dt>Tier mix</dt><dd>${(c.tier_mix || []).join("; ")}</dd>
      <dt>DSL fit</dt><dd>${escapeHtml(c.dsl_expressibility || "")}</dd>
      <dt>Ambiguity</dt><dd>${escapeHtml(c.ambiguity || "")}</dd>
      <dt>Repo supply</dt><dd>${escapeHtml(supply.qualitative || supply.note || "unmeasured")}${
    supply.note && supply.qualitative ? ` — ${escapeHtml(supply.note)}` : ""
  }</dd>
      <dt>Reproducibility</dt><dd>${repro.probed ? `<span class="tag tag-pass">probed</span> ${escapeHtml(repro.result || "")}` : `<span class="tag">documented only</span> ${escapeHtml(repro.note || "")}`}</dd>
      <dt>Oracle quality</dt><dd>${escapeHtml(c.oracle_quality || "")}</dd>
      <dt>Setup difficulty</dt><dd>${escapeHtml(c.setup_difficulty || "")}</dd>
      <dt>Existing codemods</dt><dd>${escapeHtml(c.existing_codemods || "")}</dd>
      <dt>Est. cost</dt><dd>${escapeHtml(c.estimated_cost || "")}</dd>
      <dt>Sources</dt><dd>${(c.sources || [])
        .map((s) => `<a href="${escapeHtml(s)}" target="_blank" rel="noopener">${escapeHtml(s)}</a>`)
        .join("<br>")}</dd>
    </div>
  `;
  return el;
}
