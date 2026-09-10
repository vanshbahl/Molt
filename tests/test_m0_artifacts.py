"""Basic automated checks for the M0 machinery added while closing M0's pilot-closure
blockers (model/provider selection, PyJWT exemplar, evidence packet, cost projection,
ceilings, and their console wiring).

Deliberately dependency-free (stdlib `unittest` only, no pytest/pyproject.toml) because
no Python package exists yet (Phase 1+). Run with:

    python3 -m unittest discover -s tests -v

This does NOT test Molt's (nonexistent) engine, schema, or inference code. It tests that
the structured JSON/markdown artifacts this M0 pass produced are well-formed, internally
consistent with each other, and that the console panels that read them point at files
that actually exist. A green run is not evidence of a correct migration rule or a
measured pilot result -- it only means the bookkeeping is not silently broken.
"""

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"
CONSOLE = REPO_ROOT / "console"


def load_json(relpath):
    return json.loads((REPO_ROOT / relpath).read_text())


class TestExperimentJsonWellFormed(unittest.TestCase):
    """Every experiments/*.json file must at least parse and be a dict."""

    def test_all_experiment_json_files_parse(self):
        json_files = sorted(EXPERIMENTS.glob("*.json"))
        self.assertGreaterEqual(len(json_files), 5, "expected candidates/probes/pilot_config/pilot_estimate/ceilings at minimum")
        for path in json_files:
            with self.subTest(file=path.name):
                data = json.loads(path.read_text())
                self.assertIsInstance(data, dict)


class TestCandidatesConsistency(unittest.TestCase):
    def setUp(self):
        self.data = load_json("experiments/candidates.json")

    def test_pilot_recommendation_ids_exist_in_candidates(self):
        ids = {c["id"] for c in self.data["candidates"]}
        for pilot_id in self.data["pilot_recommendation"]:
            self.assertIn(pilot_id, ids)

    def test_pyjwt_is_a_pilot_candidate(self):
        self.assertIn("pyjwt-1-to-2", self.data["pilot_recommendation"])

    def test_every_candidate_has_required_fields(self):
        required = {"id", "library", "role", "tier_mix", "reproducibility", "sources"}
        for c in self.data["candidates"]:
            with self.subTest(candidate=c.get("id")):
                self.assertTrue(required.issubset(c.keys()), f"missing: {required - c.keys()}")


class TestFeasibilityProbesConsistency(unittest.TestCase):
    def setUp(self):
        self.data = load_json("experiments/feasibility_probes.json")

    def test_bounded_task_probe_present(self):
        ids = {p["candidate_id"] for p in self.data["probes"]}
        self.assertIn(
            "pyjwt-1-to-2-bounded-task",
            ids,
            "the exemplar's grounding probe (exact bounded-task sites) must be recorded",
        )

    def test_every_probe_has_old_pass_and_new_fail_or_mixed(self):
        for p in self.data["probes"]:
            with self.subTest(candidate=p["candidate_id"]):
                self.assertEqual(p["old_result"]["status"], "pass")
                self.assertIn(p["new_result"]["status"], {"fail", "mixed"})

    def test_bounded_task_probe_covers_both_pilot_sites(self):
        probe = next(p for p in self.data["probes"] if p["candidate_id"] == "pyjwt-1-to-2-bounded-task")
        detail = probe["new_result"]["detail"]
        self.assertIn("ExpiredSignature", detail)
        self.assertIn("verify_expiration", detail)


class TestPilotConfigConsistency(unittest.TestCase):
    def setUp(self):
        self.config = load_json("experiments/pilot_config.json")

    def test_model_is_pinned_snapshot_not_alias(self):
        model_id = self.config["model_id"]
        self.assertRegex(model_id, r"^claude-[a-z0-9-]+-\d{8}$", "model id should be a dated snapshot, not an alias like '-latest'")

    def test_repair_sweep_matches_registered_roadmap_values(self):
        self.assertEqual(self.config["repair_proposal_sweep"], [1, 2, 3, 5])

    def test_generation_replicates_is_positive(self):
        self.assertGreaterEqual(self.config["generation_replicates_pyjwt_pilot"], 2)

    def test_price_schedule_values_are_positive_and_ordered(self):
        p = self.config["price_schedule"]
        for key in ("input_usd_per_mtok", "output_usd_per_mtok", "prompt_cache_write_usd_per_mtok", "prompt_cache_read_usd_per_mtok"):
            self.assertGreater(p[key], 0, key)
        # Sanity relationships that should hold for any real Anthropic-style price schedule.
        self.assertGreater(p["output_usd_per_mtok"], p["input_usd_per_mtok"], "output should cost more than input")
        self.assertGreater(p["prompt_cache_write_usd_per_mtok"], p["input_usd_per_mtok"], "cache write should cost more than plain input")
        self.assertLess(p["prompt_cache_read_usd_per_mtok"], p["input_usd_per_mtok"], "cache read should be cheaper than plain input")

    def test_status_is_not_silently_marked_executed(self):
        self.assertIn("not yet executed", self.config["status"])


class TestPilotEstimateConsistency(unittest.TestCase):
    def setUp(self):
        self.estimate = load_json("experiments/pilot_estimate.json")
        self.config = load_json("experiments/pilot_config.json")

    def test_status_is_projection_not_measurement(self):
        self.assertEqual(self.estimate["status"], "projection, not measurement")

    def test_measured_inputs_are_positive_integers(self):
        m = self.estimate["measured_inputs"]
        for key in ("evidence_packet_chars", "evidence_packet_words", "system_prompt_chars", "system_prompt_words"):
            self.assertIsInstance(m[key], int)
            self.assertGreater(m[key], 0)

    def test_measured_evidence_packet_char_count_matches_real_file(self):
        packet = (EXPERIMENTS / "pilot_evidence_packet.md").read_text()
        parts = packet.split("\n---\n")
        self.assertEqual(len(parts), 3, "evidence packet must have exactly the header/body/bookkeeping split this test and pilot_estimate.json both assume")
        body = parts[1].strip("\n")
        self.assertEqual(len(body), self.estimate["measured_inputs"]["evidence_packet_chars"], "pilot_estimate.json's recorded packet size has drifted from the real file -- recompute it")

    def test_cost_projection_recomputes_within_tolerance(self):
        price = self.config["price_schedule"]
        input_tok = self.estimate["token_estimation_method"]["estimated_input_tokens_first_request"]["point"]
        output_tok = self.estimate["output_token_assumption"]["estimated_output_tokens_per_request"]["point"]
        recomputed_single = (input_tok * price["input_usd_per_mtok"] + output_tok * price["output_usd_per_mtok"]) / 1_000_000
        recorded_single = self.estimate["cost_projection_usd"]["single_uncached_request_point_estimate"]
        self.assertAlmostEqual(recomputed_single, recorded_single, delta=0.001)

    def test_worst_case_exceeds_point_estimate(self):
        c = self.estimate["cost_projection_usd"]
        self.assertGreater(c["two_replicate_pilot_worst_case_estimate"], c["two_replicate_pilot_point_estimate"])


class TestCeilingsConsistency(unittest.TestCase):
    def setUp(self):
        self.ceilings = load_json("experiments/ceilings.json")
        self.estimate = load_json("experiments/pilot_estimate.json")

    def test_spend_ceiling_exceeds_worst_case_projection(self):
        ceiling = self.ceilings["spend_ceilings"]["pyjwt_pilot_hard_spend_ceiling_usd"]
        worst_case = self.estimate["cost_projection_usd"]["two_replicate_pilot_worst_case_estimate"]
        self.assertGreater(ceiling, worst_case, "the spend ceiling must have real safety margin over the projected worst case")

    def test_v1_repair_cap_is_explicitly_unset_not_guessed(self):
        self.assertTrue(self.ceilings["attempt_ceilings"]["v1_repair_cap_final_selection"].startswith("NOT SET"))

    def test_screening_ceiling_is_labeled_provisional(self):
        basis = self.ceilings["screening_ceilings"]["basis"]
        self.assertIn("PROVISIONAL", basis)


class TestConsolePanelsReferenceExistingFiles(unittest.TestCase):
    """Light static check: every fetch("...") path literal in console/panels/*.js
    must resolve to a real file, catching a stale reference after a mock file is
    renamed or removed (like diff_preview.json was during this pass).

    Browser relative-URL resolution note: fetch() resolves a relative string
    against the *document's* base URL (console/index.html, i.e. the console/
    directory), not against the importing module's own file -- this is why
    panels a directory deep still write "../../experiments/..." to reach the
    repo root: real browsers clamp ".." segments at the URL root, so any
    number of leading ".." beyond console/'s single parent level lands on the
    served root (repo root) exactly once, never above it. This resolver
    reproduces that clamping instead of naively joining segments.
    """

    FETCH_RE = re.compile(r"""fetch(?:Json)?\(\s*["']([^"']+)["']""")

    @staticmethod
    def resolve_from_document(path):
        # Document base = console/ (console/index.html serves the panels).
        current = CONSOLE
        remainder = path
        while remainder.startswith("../"):
            remainder = remainder[3:]
            if current != REPO_ROOT:
                current = current.parent
            # else: already at the served root -- browsers clamp here.
        if remainder.startswith("./"):
            remainder = remainder[2:]
        return (current / remainder).resolve()

    def test_every_fetched_path_exists(self):
        panels_dir = CONSOLE / "panels"
        missing = []
        for js_file in sorted(panels_dir.glob("*.js")):
            content = js_file.read_text()
            for path in self.FETCH_RE.findall(content):
                resolved = self.resolve_from_document(path)
                if not resolved.exists():
                    missing.append(f"{js_file.name} -> {path} (resolved: {resolved})")
        self.assertEqual(missing, [], f"panels reference nonexistent files: {missing}")


class TestProtocolDocConsistency(unittest.TestCase):
    def test_protocol_version_bumped_and_dated(self):
        text = (EXPERIMENTS / "protocol.md").read_text()
        self.assertIn("Version 0.2.0", text)
        self.assertIn("0.2.0 (2026-09-05)", text)

    def test_protocol_names_the_chosen_model(self):
        text = (EXPERIMENTS / "protocol.md").read_text()
        config = load_json("experiments/pilot_config.json")
        self.assertIn(config["model_id"], text)

    def test_readme_and_roadmap_agree_m0_is_not_closed(self):
        readme = (REPO_ROOT / "README.md").read_text()
        roadmap = (REPO_ROOT / "DOCS" / "ROADMAP.md").read_text()
        self.assertIn("not closed", readme.lower())
        self.assertIn("not closed", roadmap.lower())


if __name__ == "__main__":
    unittest.main()
