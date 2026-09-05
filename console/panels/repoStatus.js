import { fetchJson, escapeHtml, calloutRealSection, calloutMockSection } from "./_util.js";

export async function render(root) {
  const [probes, mockRepos] = await Promise.all([
    fetchJson("../../experiments/feasibility_probes.json"),
    fetchJson("./mock/repo_status.json"),
  ]);

  root.innerHTML = `
    <h1>Repository / Test Status</h1>
    <p class="panel-intro">Two different levels of reality live on this one panel — read the section badges before trusting a row.</p>

    <h2>M0 feasibility probes</h2>
    ${calloutRealSection(
      "One-script reproductions, not repository admission",
      probes.caveat
    )}
    <table>
      <thead><tr><th>Candidate</th><th>Old version</th><th>New version</th><th>Old result</th><th>New result</th><th>Conclusion</th></tr></thead>
      <tbody>
        ${probes.probes
          .map(
            (p) => `<tr>
              <td>${escapeHtml(p.library)}</td>
              <td>${escapeHtml(p.old_version)}</td>
              <td>${escapeHtml(p.new_version)}</td>
              <td><span class="tag tag-pass">${escapeHtml(p.old_result.status)}</span> ${escapeHtml(p.old_result.detail)}</td>
              <td><span class="tag ${tagClass(p.new_result.status)}">${escapeHtml(p.new_result.status)}</span> ${escapeHtml(
                p.new_result.detail
              )}</td>
              <td>${escapeHtml(p.conclusion)}</td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
    <p class="panel-intro">Not yet probed (documented only): ${escapeHtml((probes.not_probed_documented_only || []).join("; "))}</p>

    <h2>Per-repository verification status</h2>
    ${calloutMockSection(
      "No repository is admitted and no verification harness exists",
      "This shows the shape of what Phase 4/6 (verification/, benchmarks/repositories.jsonl) will eventually populate: per-repo old-baseline / target-failure / patch / re-verify status across arms. Every row below is invented placeholder data, not a real repository."
    )}
    <table>
      <thead><tr><th>Repo (mock)</th><th>Migration</th><th>Old-version baseline</th><th>Target-version failure</th><th>Patch applied</th><th>Re-verified</th></tr></thead>
      <tbody>
        ${mockRepos
          .map(
            (r) => `<tr>
              <td>${escapeHtml(r.repo)}</td>
              <td>${escapeHtml(r.migration)}</td>
              <td>${statusTag(r.old_baseline)}</td>
              <td>${statusTag(r.target_failure)}</td>
              <td>${statusTag(r.patch_applied)}</td>
              <td>${statusTag(r.reverified)}</td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function tagClass(status) {
  if (status === "fail") return "tag-fail";
  if (status === "mixed") return "tag-mixed";
  return "tag-pass";
}

function statusTag(v) {
  if (v === "pass") return '<span class="tag tag-pass">pass</span>';
  if (v === "fail") return '<span class="tag tag-fail">fail</span>';
  if (v === "pending") return '<span class="tag">pending</span>';
  return `<span class="tag">${escapeHtml(String(v))}</span>`;
}
