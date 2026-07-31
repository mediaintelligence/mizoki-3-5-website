"""Tests for the Risk Sentinel demo engine + its Flask/MCP integration."""

import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime
from mizoki_runtime.demo_risk import DEFAULT_SEED, SCENARIOS, RiskSentinelEngine


REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_SCENARIOS = tuple(SCENARIOS)


class RiskEngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RiskSentinelEngine()

    def test_same_seed_produces_identical_run(self) -> None:
        for scenario in ALL_SCENARIOS:
            self.assertEqual(
                self.engine.run(scenario, seed=DEFAULT_SEED),
                self.engine.run(scenario, seed=DEFAULT_SEED),
                scenario,
            )

    def test_unknown_scenario_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.run("not_a_scenario")

    def test_event_count_between_12_and_16(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.engine.run(scenario)
            self.assertTrue(12 <= len(run["events"]) <= 16, scenario)

    def test_every_event_lands_on_the_5x5_matrix(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.engine.run(scenario)
            for event in run["events"]:
                self.assertTrue(1 <= event["severity"] <= 5, scenario)
                self.assertTrue(1 <= event["likelihood"] <= 5, scenario)
                self.assertEqual(
                    f"s{event['severity']}l{event['likelihood']}", event["cell_id"]
                )
            self.assertEqual(25, len(run["matrix"]["cells"]))
            self.assertEqual(
                len(run["events"]),
                sum(cell["count"] for cell in run["matrix"]["cells"]),
                scenario,
            )

    def test_exactly_two_escalations_one_vetoed_with_rollback_token(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.engine.run(scenario)
            escalations = run["escalations"]
            self.assertEqual(2, len(escalations), scenario)
            kinds = sorted(e["kind"] for e in escalations)
            self.assertEqual(["auto_mitigated", "vetoed"], kinds, scenario)
            veto = next(e for e in escalations if e["kind"] == "vetoed")
            self.assertTrue(veto["rollback_token"].startswith("hmac-demo:"), scenario)
            self.assertTrue(veto["rule_id"], scenario)
            self.assertTrue(len(veto["evidence_chain"]) >= 3, scenario)
            auto = next(e for e in escalations if e["kind"] == "auto_mitigated")
            self.assertTrue(auto["mitigation"], scenario)

    def test_escalation_events_are_flagged_on_the_feed(self) -> None:
        run = self.engine.run("vendor_breach_drill")
        flags = [e["escalation"] for e in run["events"] if e["escalation"]]
        self.assertEqual(sorted(["auto_mitigated", "vetoed"]), sorted(flags))


class FlaskDemoRiskTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_run_endpoint_round_trips(self) -> None:
        response = self.client.post(
            "/api/demo/risk/run", json={"scenario": "quarterly_close"}
        )
        self.assertEqual(200, response.status_code)
        run = response.get_json()
        self.assertEqual(2, run["funnel"]["escalated"])

    def test_run_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.post("/api/demo/risk/run", json={"scenario": "nope"})
        self.assertEqual(400, response.status_code)

    def test_scenarios_endpoint_lists_all_three(self) -> None:
        ids = {s["id"] for s in
               self.client.get("/api/demo/risk/scenarios").get_json()["scenarios"]}
        self.assertEqual(set(ALL_SCENARIOS), ids)

    def test_page_served_with_absolute_urls(self) -> None:
        response = self.client.get("/demo/risk")
        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn('href="/assets/css/styles.css"', body)
        self.assertNotIn('href="assets/', body)

    def test_mcp_tool_registered_and_callable(self) -> None:
        names = {t["name"] for t in self.client.get("/api/mcp/tools").get_json()["tools"]}
        self.assertIn("demo.risk.run", names)
        self.assertIn("demo.risk.list_scenarios", names)
        response = self.client.post(
            "/api/mcp/call",
            json={"name": "demo.risk.run", "arguments": {"scenario": "campaign_compliance"}},
        )
        self.assertEqual(200, response.status_code)
        result = response.get_json()["result"]
        self.assertEqual(
            result, RiskSentinelEngine().run("campaign_compliance", seed=DEFAULT_SEED)
        )


if __name__ == "__main__":
    unittest.main()
