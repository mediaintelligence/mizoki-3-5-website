"""Tests for the Capital Desk demo engine + its Flask/MCP integration."""

import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime
from mizoki_runtime.demo_capital import (
    COVENANT_HEADROOM_FLOOR_PCT,
    DEFAULT_SEED,
    SCENARIOS,
    CapitalDeskPipeline,
    CapitalGuardrailSet,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_SCENARIOS = tuple(SCENARIOS)


class CapitalEngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = CapitalDeskPipeline()

    def test_same_seed_produces_identical_run(self) -> None:
        for scenario in ALL_SCENARIOS:
            self.assertEqual(
                self.pipeline.run(scenario, seed=DEFAULT_SEED),
                self.pipeline.run(scenario, seed=DEFAULT_SEED),
                scenario,
            )

    def test_unknown_scenario_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.pipeline.run("not_a_scenario")

    def test_exactly_one_covenant_block_per_scenario(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.pipeline.run(scenario)
            validate = next(s for s in run["stages"] if s["stage"] == "validate")
            blocked = [item for item in validate["items"] if item["blocked"]]
            self.assertEqual(1, len(blocked), scenario)
            self.assertEqual(["covenant_headroom"], blocked[0]["blocked_by"], scenario)

    def test_blocked_action_absent_from_act_stage(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.pipeline.run(scenario)
            validate = next(s for s in run["stages"] if s["stage"] == "validate")
            act = next(s for s in run["stages"] if s["stage"] == "act")
            blocked_ids = {i["action_id"] for i in validate["items"] if i["blocked"]}
            executed_ids = {i["action_id"] for i in act["items"]}
            self.assertTrue(blocked_ids, scenario)
            self.assertFalse(blocked_ids & executed_ids, scenario)

    def test_covenant_rule_math(self) -> None:
        passing = {"type": "capital_shift", "magnitude_pct": 5.0, "confidence": 0.9,
                   "supporting_conversions": 40, "headroom_after_pct": 15.0}
        checks = CapitalGuardrailSet.evaluate(passing)
        covenant = next(c for c in checks if c["rule_id"] == "covenant_headroom")
        self.assertTrue(covenant["passed"])
        failing = dict(passing, headroom_after_pct=COVENANT_HEADROOM_FLOOR_PCT - 0.1)
        checks = CapitalGuardrailSet.evaluate(failing)
        covenant = next(c for c in checks if c["rule_id"] == "covenant_headroom")
        self.assertFalse(covenant["passed"])

    def test_decision_card_shape_matches_signal_pattern(self) -> None:
        run = self.pipeline.run("growth_reallocation")
        card = run["decision_card"]
        for key in ("trace_id", "scenario", "executed_action", "provenance_chain",
                    "funnel", "guardrail_block"):
            self.assertIn(key, card)
        for key in ("events_sensed", "signals_formed", "passed_gate", "validated", "executed"):
            self.assertIn(key, run["funnel"])
        self.assertEqual(run["funnel"], card["funnel"])
        self.assertEqual(["covenant_headroom"], card["guardrail_block"]["blocked_by"])

    def test_causal_truth_is_derived_from_run_data(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.pipeline.run(scenario)
            card = run["decision_card"]
            truth = card["causal_truth"]
            self.assertIsInstance(truth, str, scenario)
            if card["executed_action"] is None:
                # Pure veto: the hold is the decision — no winner sentence.
                self.assertIn("the desk held", truth, scenario)
                self.assertNotIn("ranked #1", truth, scenario)
            else:
                # Winner sentence quotes the executed action's entity and ranking.
                self.assertIn(card["executed_action"]["entity_id"], truth, scenario)
                self.assertIn("ranked #1 by expected value × confidence", truth, scenario)
            # Veto sentence quotes the covenant arithmetic, not an opinion.
            self.assertIn(card["guardrail_block"]["entity_id"], truth, scenario)
            self.assertIn("would breach", truth, scenario)
            self.assertIn("arithmetic against the covenant", truth, scenario)

    def test_dividend_scenario_is_a_pure_veto(self) -> None:
        run = self.pipeline.run("dividend_covenant_veto")
        card = run["decision_card"]
        self.assertIsNone(card["executed_action"])
        self.assertEqual(0, run["funnel"]["executed"])
        self.assertEqual(0, run["funnel"]["validated"])
        self.assertEqual(["covenant_headroom"], card["guardrail_block"]["blocked_by"])
        act = next(s for s in run["stages"] if s["stage"] == "act")
        self.assertEqual([], act["items"])
        self.assertIn("No move earned execution this run — the desk held.",
                      card["causal_truth"])

    def test_streaming_frame_ordering_and_termination(self) -> None:
        for scenario in ALL_SCENARIOS:
            frames = list(self.pipeline.run_streaming(scenario))
            self.assertLess(len(frames), 200, scenario)
            self.assertEqual("done", frames[-1]["type"], scenario)
            stage_names = [f["data"]["stage"] for f in frames if f["type"] == "stage"]
            self.assertEqual(list(CapitalDeskPipeline.STAGES), stage_names, scenario)


class FlaskDemoCapitalTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_run_endpoint_returns_consistent_funnel(self) -> None:
        response = self.client.post(
            "/api/demo/capital/run", json={"scenario": "debt_paydown_vs_buyback"}
        )
        self.assertEqual(200, response.status_code)
        run = response.get_json()
        self.assertEqual(run["funnel"], run["decision_card"]["funnel"])

    def test_run_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.post("/api/demo/capital/run", json={"scenario": "nope"})
        self.assertEqual(400, response.status_code)

    def test_scenarios_endpoint_lists_all_registered(self) -> None:
        ids = {s["id"] for s in
               self.client.get("/api/demo/capital/scenarios").get_json()["scenarios"]}
        self.assertEqual(set(ALL_SCENARIOS), ids)

    def test_sse_endpoint_streams_parseable_frames(self) -> None:
        response = self.client.get(
            "/api/demo/capital/stream?scenario=growth_reallocation&seed=42"
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.content_type.startswith("text/event-stream"))
        self.assertEqual("no-cache", response.headers["Cache-Control"])
        self.assertEqual("no", response.headers["X-Accel-Buffering"])
        body = response.get_data(as_text=True)
        first_frame = body.split("\n\n")[0]
        lines = first_frame.splitlines()
        self.assertEqual("event: raw_event", lines[0])
        payload = json.loads(lines[1].split("data: ", 1)[1])
        self.assertIn("event_id", payload)
        self.assertIn("event: done", body)

    def test_sse_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.get("/api/demo/capital/stream?scenario=bogus")
        self.assertEqual(400, response.status_code)

    def test_page_served_with_absolute_urls(self) -> None:
        response = self.client.get("/demo/capital")
        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn('href="/assets/css/styles.css"', body)
        self.assertNotIn('href="assets/', body)
        self.assertIn("covenant", body.lower())

    def test_mcp_tool_registered_and_callable(self) -> None:
        names = {t["name"] for t in self.client.get("/api/mcp/tools").get_json()["tools"]}
        self.assertIn("demo.capital.run", names)
        self.assertIn("demo.capital.list_scenarios", names)
        response = self.client.post(
            "/api/mcp/call",
            json={"name": "demo.capital.run",
                  "arguments": {"scenario": "working_capital_stress"}},
        )
        self.assertEqual(200, response.status_code)
        result = response.get_json()["result"]
        self.assertEqual(
            result, CapitalDeskPipeline().run("working_capital_stress", seed=DEFAULT_SEED)
        )


if __name__ == "__main__":
    unittest.main()
