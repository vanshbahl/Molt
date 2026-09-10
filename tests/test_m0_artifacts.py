"""Basic automated checks for the M0 machinery.

Deliberately dependency-free (stdlib `unittest` only, no pytest/pyproject.toml) because
no Python package exists yet (Phase 1+). Run with:

    python3 -m unittest discover -s tests -v

This tests that the structured JSON/markdown artifacts, canonical schema, frozen ceilings,
cryptographic protocol hash, and zero-cost Gemini pilot runner are well-formed and internally consistent.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"
CONSOLE = REPO_ROOT / "console"
DOCS = REPO_ROOT / "DOCS"


def load_json(relpath):
    return json.loads((REPO_ROOT / relpath).read_text(encoding="utf-8"))


class TestExperimentJsonWellFormed(unittest.TestCase):
    """Every experiments/*.json file must at least parse and be a dict."""

    def test_all_experiment_json_files_parse(self):
        json_files = sorted(EXPERIMENTS.glob("*.json"))
        self.assertGreaterEqual(
            len(json_files),
            6,
            "expected candidates/probes/pilot_config/pilot_estimate/ceilings/rule_schema at minimum",
        )
        for path in json_files:
            with self.subTest(file=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
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

    def test_provider_is_google(self):
        self.assertIn("Google", self.config["provider"])
        self.assertEqual(self.config["credential_env"], "GEMINI_API_KEY")

    def test_model_is_exact_pinned_gemini_flash(self):
        model_id = self.config["model_id"]
        self.assertEqual(model_id, "gemini-3.7-flash")

    def test_repair_sweep_matches_registered_roadmap_values(self):
        self.assertEqual(self.config["repair_proposal_sweep"], [1, 2, 3, 5])

    def test_generation_replicates_is_positive(self):
        self.assertGreaterEqual(self.config["generation_replicates_pyjwt_pilot"], 2)

    def test_monetary_cost_is_zero_on_free_tier(self):
        p = self.config["price_schedule"]
        self.assertEqual(p["effective_monetary_cost_usd"], 0.0)
        self.assertIn("Free Tier", p["tier"])

    def test_status_is_not_silently_marked_executed(self):
        self.assertIn("not yet executed", self.config["status"])


class TestPilotEstimateConsistency(unittest.TestCase):
    def setUp(self):
        self.estimate = load_json("experiments/pilot_estimate.json")
        self.config = load_json("experiments/pilot_config.json")

    def test_status_is_projection_not_measurement(self):
        self.assertEqual(self.estimate["status"], "projection, not measurement")

    def test_estimate_distinct_from_measurements(self):
        self.assertEqual(self.estimate["status"], "projection, not measurement")
        measured_dir = EXPERIMENTS / "measured_runs"
        if measured_dir.exists():
            for f in measured_dir.glob("*.json"):
                data = json.loads(f.read_text(encoding="utf-8"))
                self.assertIn("status", data)
                self.assertTrue(data["status"].startswith("measured"))

    def test_measured_inputs_are_positive_integers(self):
        m = self.estimate["measured_inputs"]
        for key in ("evidence_packet_chars", "evidence_packet_words", "system_prompt_chars", "system_prompt_words"):
            self.assertIsInstance(m[key], int)
            self.assertGreater(m[key], 0)

    def test_measured_evidence_packet_char_count_matches_real_file(self):
        packet = (EXPERIMENTS / "pilot_evidence_packet.md").read_text(encoding="utf-8")
        parts = packet.split("\n---\n")
        self.assertEqual(
            len(parts),
            3,
            "evidence packet must have exactly the header/body/bookkeeping split this test and pilot_estimate.json both assume",
        )
        body = parts[1].strip("\n")
        self.assertEqual(
            len(body),
            self.estimate["measured_inputs"]["evidence_packet_chars"],
            "pilot_estimate.json's recorded packet size has drifted from the real file -- recompute it",
        )

    def test_historical_anthropic_projections_preserved_as_superseded(self):
        self.assertIn("superseded_historical_anthropic_projection_usd", self.estimate)
        hist = self.estimate["superseded_historical_anthropic_projection_usd"]
        self.assertIn("superseded", hist["status"])
        self.assertEqual(hist["model"], "Claude Haiku 4.5")

    def test_zero_monetary_spend_projection(self):
        proj = self.estimate["cost_projection_usd"]
        self.assertEqual(proj["single_uncached_request_point_estimate"], 0.0)
        self.assertEqual(proj["two_replicate_pilot_worst_case_estimate"], 0.0)


class TestCeilingsConsistency(unittest.TestCase):
    def setUp(self):
        self.ceilings = load_json("experiments/ceilings.json")
        self.estimate = load_json("experiments/pilot_estimate.json")

    def test_spend_ceiling_is_strictly_zero(self):
        ceiling = self.ceilings["spend_ceilings"]["pyjwt_pilot_hard_spend_ceiling_usd"]
        self.assertEqual(ceiling, 0.00, "Under the zero-cost constraint, spend ceiling must be strictly $0.00")

    def test_v1_repair_cap_is_frozen_to_sweep_value(self):
        cap = self.ceilings["attempt_ceilings"]["v1_repair_cap_final_selection"]
        sweep = self.ceilings["attempt_ceilings"]["repair_proposal_sweep"]
        self.assertIsInstance(cap, int, "v1_repair_cap_final_selection must be a frozen integer, not unset")
        self.assertIn(cap, sweep, f"frozen cap {cap} must belong to registered sweep {sweep}")
        self.assertEqual(cap, 3, "V1 repair cap must be frozen at 3 proposals (1 initial + 2 repairs)")
        self.assertIn("v1_repair_cap_rationale", self.ceilings["attempt_ceilings"])
        self.assertGreater(len(self.ceilings["attempt_ceilings"]["v1_repair_cap_rationale"]), 30)

    def test_free_tier_quota_ceilings_present(self):
        self.assertIn("free_tier_quota_ceilings", self.ceilings)
        quotas = self.ceilings["free_tier_quota_ceilings"]
        self.assertEqual(quotas["provider"], "Google Gemini Developer API")
        self.assertEqual(quotas["model"], "gemini-3.7-flash")
        self.assertGreater(quotas["max_requests_per_minute"], 0)


class TestCanonicalRuleSchema(unittest.TestCase):
    def test_rule_schema_json_exists_and_is_valid_json_schema(self):
        schema = load_json("experiments/rule_schema.json")
        self.assertEqual(schema["title"], "MoltRuleBundle")
        self.assertIn("operations", schema["properties"])
        self.assertEqual(schema["type"], "object")

    def test_console_mock_schema_conforms_to_canonical_envelope(self):
        mock_rule = load_json("console/mock/rule_schema.json")
        self.assertIn("bundle_id", mock_rule)
        self.assertIn("bundle_version", mock_rule)
        self.assertIn("applies_to", mock_rule)
        self.assertIn("operations", mock_rule)
        self.assertIsInstance(mock_rule["operations"], list)
        valid_ops = {
            "rename_symbol",
            "change_import",
            "rename_argument",
            "add_argument",
            "remove_argument",
            "replace_call",
            "abstain",
        }
        for op in mock_rule["operations"]:
            self.assertIn(op["op"], valid_ops)

    def test_rule_spec_doc_exists(self):
        doc = (DOCS / "RULE_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("Molt Rule Specification", doc)
        self.assertIn("rename_symbol", doc)
        self.assertIn("replace_call", doc)


class TestConsolePanelsReferenceExistingFiles(unittest.TestCase):
    FETCH_RE = re.compile(r"""fetch(?:Json)?\(\s*["']([^"']+)["']""")

    @staticmethod
    def resolve_from_document(path):
        current = CONSOLE
        remainder = path
        while remainder.startswith("../"):
            remainder = remainder[3:]
            if current != REPO_ROOT:
                current = current.parent
        if remainder.startswith("./"):
            remainder = remainder[2:]
        return (current / remainder).resolve()

    def test_every_fetched_path_exists(self):
        panels_dir = CONSOLE / "panels"
        missing = []
        for js_file in sorted(panels_dir.glob("*.js")):
            content = js_file.read_text(encoding="utf-8")
            for path in self.FETCH_RE.findall(content):
                resolved = self.resolve_from_document(path)
                if not resolved.exists():
                    missing.append(f"{js_file.name} -> {path} (resolved: {resolved})")
        self.assertEqual(missing, [], f"panels reference nonexistent files: {missing}")


class TestProtocolDocConsistency(unittest.TestCase):
    def test_protocol_version_bumped_and_dated(self):
        text = (EXPERIMENTS / "protocol.md").read_text(encoding="utf-8")
        self.assertIn("Version 0.4.0", text)
        self.assertIn("0.4.0 (2026-09-10)", text)

    def test_protocol_names_the_chosen_model(self):
        text = (EXPERIMENTS / "protocol.md").read_text(encoding="utf-8")
        config = load_json("experiments/pilot_config.json")
        self.assertIn(config["model_id"], text)
        self.assertIn("gemini-3.7-flash", text)

    def test_protocol_records_frozen_repair_cap(self):
        text = (EXPERIMENTS / "protocol.md").read_text(encoding="utf-8")
        self.assertIn("3 proposals", text)
        self.assertIn("V1 repair cap", text)

    def test_protocol_cryptographic_hash_matches(self):
        protocol_bytes = (EXPERIMENTS / "protocol.md").read_bytes()
        computed_sha256 = hashlib.sha256(protocol_bytes).hexdigest()
        hash_file_content = (EXPERIMENTS / "protocol.hash").read_text(encoding="utf-8").strip()
        recorded_hash = hash_file_content.split()[0]
        self.assertEqual(
            computed_sha256,
            recorded_hash,
            f"Cryptographic hash mismatch! Computed: {computed_sha256}, Recorded: {recorded_hash}",
        )


class TestPilotRunnerMechanism(unittest.TestCase):
    def test_pilot_runner_script_exists_and_dry_run_passes(self):
        script_path = EXPERIMENTS / "run_pyjwt_pilot.py"
        self.assertTrue(script_path.exists(), "experiments/run_pyjwt_pilot.py must exist")

        res = subprocess.run(
            [sys.executable, str(script_path), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(res.returncode, 0, f"dry-run failed with stderr: {res.stderr}")
        self.assertIn("gemini-3.7-flash", res.stdout)
        self.assertIn("Google Gemini Developer API", res.stdout)

    def test_pilot_runner_blocks_cleanly_without_gemini_api_key(self):
        script_path = EXPERIMENTS / "run_pyjwt_pilot.py"
        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)

        res = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=REPO_ROOT,
        )
        self.assertEqual(res.returncode, 2, "Expected exit code 2 when GEMINI_API_KEY is unset")
        self.assertIn("[BLOCKED]", res.stderr)
        self.assertIn("GEMINI_API_KEY", res.stderr)

    def test_no_anthropic_credential_required(self):
        script_path = EXPERIMENTS / "run_pyjwt_pilot.py"
        code = script_path.read_text(encoding="utf-8")
        self.assertNotIn("ANTHROPIC_API_KEY", code)
        self.assertIn("GEMINI_API_KEY", code)

    def test_pilot_runner_loads_dotenv(self):
        import importlib.util
        import tempfile

        script_path = EXPERIMENTS / "run_pyjwt_pilot.py"
        spec = importlib.util.spec_from_file_location("run_pyjwt_pilot", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with tempfile.TemporaryDirectory() as td:
            tmp_env = Path(td) / ".env"
            tmp_env.write_text("GEMINI_API_KEY=test_sample_key_12345\n", encoding="utf-8")
            saved = os.environ.pop("GEMINI_API_KEY", None)
            try:
                loaded = mod.load_dotenv(tmp_env)
                self.assertTrue(loaded)
                self.assertEqual(os.environ.get("GEMINI_API_KEY"), "test_sample_key_12345")
            finally:
                if saved is not None:
                    os.environ["GEMINI_API_KEY"] = saved
                else:
                    os.environ.pop("GEMINI_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
