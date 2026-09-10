import { escapeHtml, calloutRealSection, calloutMockSection } from "./_util.js";

// Extracts the two fenced ```python blocks following the "**Before" / "**After"
// headers in pilot_evidence_packet.md. Deliberately tiny regex parsing, not a
// markdown library — this panel has no engine and no build step.
function extractExemplar(md) {
  const block = (marker) => {
    const idx = md.indexOf(marker);
    if (idx === -1) return null;
    const fenceStart = md.indexOf("```python", idx);
    const codeStart = md.indexOf("\n", fenceStart) + 1;
    const fenceEnd = md.indexOf("```", codeStart);
    return md.slice(codeStart, fenceEnd).replace(/\n$/, "");
  };
  return { before: block("**Before"), after: block("**After") };
}

// Naive positional line diff: fine for this fixed two-line-change exemplar,
// not a general diff algorithm.
function positionalDiff(beforeSrc, afterSrc) {
  const before = beforeSrc.split("\n");
  const after = afterSrc.split("\n");
  const len = Math.max(before.length, after.length);
  const lines = [];
  for (let i = 0; i < len; i++) {
    const b = before[i];
    const a = after[i];
    if (b === a) {
      lines.push({ type: "ctx", text: b ?? "" });
    } else {
      if (b !== undefined) lines.push({ type: "del", text: b });
      if (a !== undefined) lines.push({ type: "add", text: a });
    }
  }
  return lines;
}

export async function render(root) {
  const res = await fetch("../../experiments/pilot_evidence_packet.md");
  const md = res.ok ? await res.text() : "";
  const { before, after } = extractExemplar(md);

  const diffLines =
    before && after
      ? positionalDiff(before, after)
          .map((l) => {
            const prefix = l.type === "add" ? "+" : l.type === "del" ? "-" : " ";
            const cls = l.type === "add" ? "diff-add" : l.type === "del" ? "diff-del" : "diff-ctx";
            return `<span class="${cls}">${prefix} ${escapeHtml(l.text)}</span>`;
          })
          .join("\n")
      : "(could not load experiments/pilot_evidence_packet.md)";

  root.innerHTML = `
    <h1>Transformation Diff Preview</h1>
    <p class="panel-intro">Will eventually render <code>transform/report.py</code>'s dry-run diff output against a real repository (Phase 2). No engine exists yet.</p>
    ${calloutRealSection(
      "Real frozen exemplar, hand-diffed — not engine output",
      "This diff is computed (a naive line-by-line comparison, not a general diff algorithm) directly from experiments/pilot_evidence_packet.md's frozen development exemplar, which was itself produced by running both PyJWT versions in isolated venvs (see Verification panel). No parser, matcher, or compiler produced this diff — but the before/after content is the real, registered M0 pilot exemplar, not a generic illustration."
    )}
    <h2>PyJWT bounded-task exemplar</h2>
    <pre class="json-view">${diffLines}</pre>

    <h2>Abstentions</h2>
    <p class="panel-intro">A rule can decline to edit a site it cannot safely resolve. This is a real design requirement (see README.md's bounded-rules section). The pilot evidence packet's negative examples (<code>.decode()</code>/<code>.encode()</code> on unrelated receivers, already-migrated code) are the real candidates for this; no engine exists yet to actually decide abstention, so this section stays illustrative.</p>
    ${calloutMockSection(
      "Illustrative only",
      "No matcher/engine exists to actually produce an abstention decision. The negative examples above are real (from the evidence packet); the abstention reasoning below is hand-written."
    )}
    <div class="card"><div class="card-title">raw_bytes.decode("utf-8")</div><div>Not a PyJWT receiver; qualified-name matching must not fire on spelling alone.</div></div>
    <div class="card"><div class="card-title">jwt.decode(token, secret, algorithms=["HS256"], options={"verify_exp": False})</div><div>Already in the target (2.x) form; a correct rule must be idempotent and produce no further edit here.</div></div>
  `;
}
