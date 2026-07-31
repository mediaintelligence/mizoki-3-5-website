"""Tests for the Counsel Room demo engine + its Flask/MCP integration."""

import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime
from mizoki_runtime.demo_counsel import (
    ALLOWED_AUTHORITY_CITATIONS,
    UNAUTHORIZED_PRACTICE_WARNING,
    LegalSynthesizer,
    MixtureRouter,
    ScenarioLibrary,
    list_scenarios,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_SCENARIO_IDS = tuple(s["id"] for s in list_scenarios())
FREE_TEXT_QUERY = "can I change my irrevocable trust in connecticut"
XSS_PROBE = "<script>alert('xss')</script><img src=x onerror=alert(1)>"


class ConflictDetectionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.synthesizer = LegalSynthesizer()

    def test_trust_modification_gst_triggers_critical_conflict(self) -> None:
        response = self.synthesizer.synthesize(scenario_id="trust_modification_gst")
        conflict_ids = {c["conflict_id"] for c in response["conflicts"]}
        self.assertIn("gst_grandfather_termination", conflict_ids)
        gst = next(
            c for c in response["conflicts"]
            if c["conflict_id"] == "gst_grandfather_termination"
        )
        self.assertEqual("critical", gst["severity"])
        self.assertEqual(["trust_law", "tax_law"], gst["domains"])
        self.assertIn("45a-499n", gst["summary"])
        self.assertIn("26.2601-1(b)(4)", gst["summary"])
        self.assertIn("GST analysis", gst["recommendation"])

    def test_other_scenarios_have_no_default_conflicts(self) -> None:
        for scenario_id in ("ct_probate_opening", "crummey_annual_gift"):
            response = self.synthesizer.synthesize(scenario_id=scenario_id)
            self.assertEqual([], response["conflicts"], scenario_id)

    def test_keyword_conflicts_fire_only_on_trigger_words(self) -> None:
        response = self.synthesizer.synthesize(
            free_text="mother died leaving a handwritten holographic will to probate"
        )
        conflict_ids = {c["conflict_id"] for c in response["conflicts"]}
        self.assertIn("holographic_will_ct", conflict_ids)


class ComplianceInvariantsTestCase(unittest.TestCase):
    """Every response — all scenarios AND free text — must be flagged."""

    def setUp(self) -> None:
        self.synthesizer = LegalSynthesizer()

    def test_all_scenarios_flagged_for_review_with_warning(self) -> None:
        for scenario_id in ALL_SCENARIO_IDS:
            response = self.synthesizer.synthesize(scenario_id=scenario_id)
            self.assertIs(True, response["flagged_for_review"], scenario_id)
            self.assertTrue(response["unauthorized_practice_warning"], scenario_id)
            self.assertEqual(
                UNAUTHORIZED_PRACTICE_WARNING,
                response["unauthorized_practice_warning"],
                scenario_id,
            )

    def test_free_text_response_flagged_for_review_with_warning(self) -> None:
        response = self.synthesizer.synthesize(free_text=FREE_TEXT_QUERY)
        self.assertIs(True, response["flagged_for_review"])
        self.assertEqual(
            UNAUTHORIZED_PRACTICE_WARNING, response["unauthorized_practice_warning"]
        )

    def test_missing_both_inputs_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.synthesizer.synthesize()

    def test_over_length_free_text_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.synthesizer.synthesize(free_text="x" * 501)


class RoutingTestCase(unittest.TestCase):
    def test_routing_scores_match_spec_for_scenario_1(self) -> None:
        routing = MixtureRouter.route("trust_modification_gst")
        scores = {entry["expert"]: entry["relevance"] for entry in routing}
        self.assertEqual(
            {"ct_law": 0.94, "trust_law": 0.91, "tax_law": 0.88, "estate_law": 0.42},
            scores,
        )

    def test_experts_below_half_marked_not_consulted_but_listed(self) -> None:
        for scenario_id in ALL_SCENARIO_IDS:
            routing = MixtureRouter.route(scenario_id)
            self.assertEqual(4, len(routing), scenario_id)
            for entry in routing:
                if entry["relevance"] < 0.5:
                    self.assertFalse(entry["consulted"], (scenario_id, entry["expert"]))
                self.assertTrue(entry["rationale"], (scenario_id, entry["expert"]))

    def test_free_text_routes_to_trust_modification_gst(self) -> None:
        scenario_id, score = ScenarioLibrary.match_free_text(FREE_TEXT_QUERY)
        self.assertEqual("trust_modification_gst", scenario_id)
        self.assertGreater(score, 0)

        response = LegalSynthesizer().synthesize(free_text=FREE_TEXT_QUERY)
        self.assertEqual("trust_modification_gst", response["scenario"]["id"])
        self.assertEqual("free_text", response["scenario"]["matched_by"])

    def test_match_free_text_never_errors_on_garbage(self) -> None:
        scenario_id, _ = ScenarioLibrary.match_free_text("zzz qqq 12345 %%%")
        self.assertIn(scenario_id, ALL_SCENARIO_IDS)


class AuthorityCorpusTestCase(unittest.TestCase):
    def test_all_authorities_drawn_from_allowed_corpus(self) -> None:
        synthesizer = LegalSynthesizer()
        for scenario_id in ALL_SCENARIO_IDS:
            response = synthesizer.synthesize(scenario_id=scenario_id)
            self.assertTrue(response["expert_analyses"], scenario_id)
            for analysis in response["expert_analyses"]:
                self.assertTrue(analysis["authorities"], analysis["expert"])
                for authority in analysis["authorities"]:
                    self.assertIn(
                        authority["citation"],
                        ALLOWED_AUTHORITY_CITATIONS,
                        (scenario_id, analysis["expert"], authority),
                    )

    def test_irac_elements_are_substantive(self) -> None:
        synthesizer = LegalSynthesizer()
        for scenario_id in ALL_SCENARIO_IDS:
            response = synthesizer.synthesize(scenario_id=scenario_id)
            for analysis in response["expert_analyses"]:
                for element in ("issue", "rule", "application", "conclusion"):
                    self.assertGreater(
                        len(analysis["irac"][element]),
                        80,
                        (scenario_id, analysis["expert"], element),
                    )

    def test_checklists_have_seven_ordered_steps_with_deadlines(self) -> None:
        synthesizer = LegalSynthesizer()
        for scenario_id in ALL_SCENARIO_IDS:
            response = synthesizer.synthesize(scenario_id=scenario_id)
            checklist = response["compliance_checklist"]
            self.assertEqual(7, len(checklist), scenario_id)
            for item in checklist:
                self.assertTrue(item["step"], scenario_id)
                self.assertTrue(item["deadline"], scenario_id)


class FlaskDemoCounselTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_query_by_scenario_id_returns_200(self) -> None:
        response = self.client.post(
            "/api/demo/counsel/query", json={"scenario_id": "trust_modification_gst"}
        )
        self.assertEqual(200, response.status_code)
        body = response.get_json()
        self.assertIs(True, body["flagged_for_review"])
        self.assertEqual(
            "gst_grandfather_termination", body["conflicts"][0]["conflict_id"]
        )

    def test_query_by_free_text_returns_200(self) -> None:
        response = self.client.post(
            "/api/demo/counsel/query", json={"query": FREE_TEXT_QUERY}
        )
        self.assertEqual(200, response.status_code)
        body = response.get_json()
        self.assertEqual("trust_modification_gst", body["scenario"]["id"])
        self.assertIs(True, body["flagged_for_review"])

    def test_missing_both_returns_400(self) -> None:
        response = self.client.post("/api/demo/counsel/query", json={})
        self.assertEqual(400, response.status_code)
        self.assertIn("scenario_id", response.get_json()["error"])

    def test_over_length_free_text_returns_400(self) -> None:
        response = self.client.post(
            "/api/demo/counsel/query", json={"query": "x" * 501}
        )
        self.assertEqual(400, response.status_code)

    def test_unknown_scenario_id_returns_400(self) -> None:
        response = self.client.post(
            "/api/demo/counsel/query", json={"scenario_id": "not_real"}
        )
        self.assertEqual(400, response.status_code)

    def test_xss_probe_is_json_encoded_not_reflected_as_html(self) -> None:
        response = self.client.post(
            "/api/demo/counsel/query", json={"query": XSS_PROBE}
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.content_type.startswith("application/json"))
        body = response.get_json()
        # Echoed verbatim inside a JSON document (safe), never into HTML.
        self.assertEqual(XSS_PROBE, body["query"])
        raw = response.get_data(as_text=True)
        self.assertFalse(raw.lstrip().startswith("<"))  # JSON body, not HTML
        self.assertIn('"query"', raw)  # probe lives inside a JSON string field
        self.assertIs(True, body["flagged_for_review"])
        # And the served demo page itself never embeds request data server-side.
        page = self.client.get("/demo/counsel").get_data(as_text=True)
        self.assertNotIn("alert('xss')", page)

    def test_scenarios_endpoint_lists_all_three(self) -> None:
        response = self.client.get("/api/demo/counsel/scenarios")
        self.assertEqual(200, response.status_code)
        ids = {s["id"] for s in response.get_json()["scenarios"]}
        self.assertEqual(set(ALL_SCENARIO_IDS), ids)

    def test_mcp_tool_callable_via_api(self) -> None:
        tools = self.client.get("/api/mcp/tools").get_json()["tools"]
        names = {tool["name"] for tool in tools}
        self.assertIn("demo.counsel.query", names)
        self.assertIn("demo.counsel.list_scenarios", names)

        response = self.client.post(
            "/api/mcp/call",
            json={
                "name": "demo.counsel.query",
                "arguments": {"scenario_id": "trust_modification_gst"},
            },
        )
        self.assertEqual(200, response.status_code)
        result = response.get_json()["result"]
        self.assertIs(True, result["flagged_for_review"])
        self.assertEqual(
            "gst_grandfather_termination", result["conflicts"][0]["conflict_id"]
        )

        empty_call = self.client.post(
            "/api/mcp/call", json={"name": "demo.counsel.query", "arguments": {}}
        )
        self.assertEqual(400, empty_call.status_code)


if __name__ == "__main__":
    unittest.main()
