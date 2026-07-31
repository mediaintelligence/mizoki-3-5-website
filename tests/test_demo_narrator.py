"""Tests for the Trace Narrator (deterministic 'Why?' narration)."""

import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime
from mizoki_runtime.demo_narrator import NARRATABLE_DEMOS, narrate


REPO_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_SCENARIOS = {
    "signal": "ecommerce_roas",
    "capital": "growth_reallocation",
    "counsel": "trust_modification_gst",
    "estate": "ct_estate_settlement",
    "risk": "quarterly_close",
    "nexus": "cpm_shock",
}


class NarratorTestCase(unittest.TestCase):
    def test_every_demo_is_narratable_and_deterministic(self) -> None:
        for demo in NARRATABLE_DEMOS:
            scenario = SAMPLE_SCENARIOS[demo]
            first = narrate(demo, scenario, seed=42)
            second = narrate(demo, scenario, seed=42)
            self.assertEqual(first, second, demo)
            self.assertTrue(first["narration"], demo)
            self.assertTrue(first["trace_id"], demo)
            # 4–6 sentence budget: at least 4 sentence terminators.
            self.assertGreaterEqual(first["narration"].count("."), 4, demo)

    def test_signal_narration_mentions_blocked_rule_id(self) -> None:
        narration = narrate("signal", "ecommerce_roas", seed=42)["narration"]
        self.assertIn("budget_swing_cap", narration)
        self.assertIn("campaign_7", narration)

    def test_capital_narration_mentions_covenant_rule(self) -> None:
        narration = narrate("capital", "growth_reallocation", seed=42)["narration"]
        self.assertIn("covenant_headroom", narration)

    def test_risk_narration_mentions_veto_rule_and_token(self) -> None:
        narration = narrate("risk", "campaign_compliance", seed=42)["narration"]
        self.assertIn("aggressive_reallocation_veto", narration)
        self.assertIn("hmac-demo:", narration)

    def test_unknown_demo_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            narrate("nope", "whatever")

    def test_unknown_scenario_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            narrate("signal", "not_a_scenario")


class FlaskNarratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_narrate_endpoint_for_every_demo(self) -> None:
        for demo, scenario in SAMPLE_SCENARIOS.items():
            response = self.client.get(
                f"/api/demo/{demo}/narrate?scenario={scenario}&seed=42"
            )
            self.assertEqual(200, response.status_code, demo)
            body = response.get_json()
            self.assertIn("narration", body, demo)
            self.assertIn("trace_id", body, demo)

    def test_narrate_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.get("/api/demo/signal/narrate?scenario=bogus")
        self.assertEqual(400, response.status_code)

    def test_narrate_endpoint_unknown_demo_404s(self) -> None:
        response = self.client.get("/api/demo/bogus/narrate?scenario=x")
        self.assertEqual(404, response.status_code)

    def test_mcp_narrate_tool(self) -> None:
        names = {t["name"] for t in self.client.get("/api/mcp/tools").get_json()["tools"]}
        self.assertIn("demo.narrate", names)
        response = self.client.post(
            "/api/mcp/call",
            json={"name": "demo.narrate",
                  "arguments": {"demo": "risk", "scenario": "quarterly_close"}},
        )
        self.assertEqual(200, response.status_code)
        result = response.get_json()["result"]
        self.assertEqual(narrate("risk", "quarterly_close", seed=42), result)


if __name__ == "__main__":
    unittest.main()
