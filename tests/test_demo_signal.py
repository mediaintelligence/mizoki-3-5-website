"""Tests for the Signal Factory demo engine + its Flask/MCP integration."""

import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime
from mizoki_runtime.demo_signal import (
    DEFAULT_SEED,
    REASON_CONFIDENCE,
    REASON_SAMPLE,
    REASON_UPLIFT,
    SCENARIOS,
    ReLUGate,
    Signal,
    SignalFactoryPipeline,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_SCENARIOS = tuple(SCENARIOS)


def _strip_timestamps(payload):
    """Deep-copy with every timestamp-ish key removed, for run comparison."""
    if isinstance(payload, dict):
        return {
            key: _strip_timestamps(value)
            for key, value in payload.items()
            if key not in ("timestamp", "started_at", "received_at")
        }
    if isinstance(payload, list):
        return [_strip_timestamps(item) for item in payload]
    return payload


class PipelineDeterminismTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = SignalFactoryPipeline()

    def test_same_seed_produces_identical_pipeline_run(self) -> None:
        for scenario in ALL_SCENARIOS:
            first = self.pipeline.run(scenario, seed=DEFAULT_SEED)
            second = self.pipeline.run(scenario, seed=DEFAULT_SEED)
            self.assertEqual(
                _strip_timestamps(first), _strip_timestamps(second), scenario
            )
            # The synthetic clock is fixed too, so full deep-equality holds.
            self.assertEqual(first, second, scenario)

    def test_different_seed_changes_synthetic_events(self) -> None:
        run_a = self.pipeline.run("ecommerce_roas", seed=1)
        run_b = self.pipeline.run("ecommerce_roas", seed=2)
        self.assertNotEqual(run_a["stages"][0]["items"], run_b["stages"][0]["items"])

    def test_unknown_scenario_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.pipeline.run("not_a_scenario")


class GateMathTestCase(unittest.TestCase):
    def test_hand_computed_score_matches(self) -> None:
        signal = Signal(
            entity_id="campaign_7",
            metric="roas_delta",
            uplift=0.22,
            confidence=0.86,
            sample_size=48,
        )
        expected = max(0.0, 0.22) * 0.86 * math.log(1 + 48)
        self.assertAlmostEqual(expected, ReLUGate.score(signal), places=6)
        verdict = ReLUGate.evaluate(signal)
        self.assertTrue(verdict["passed"])
        self.assertEqual([], verdict["reasons"])

    def test_negative_uplift_scores_zero(self) -> None:
        signal = Signal("x", "roas_delta", -0.4, 0.9, 100)
        self.assertEqual(0.0, ReLUGate.score(signal))

    def test_uplift_failure_reason_string(self) -> None:
        verdict = ReLUGate.evaluate(Signal("x", "roas_delta", 0.03, 0.9, 40))
        self.assertFalse(verdict["passed"])
        self.assertEqual([REASON_UPLIFT], verdict["reasons"])

    def test_confidence_failure_reason_string(self) -> None:
        verdict = ReLUGate.evaluate(Signal("x", "roas_delta", 0.10, 0.55, 40))
        self.assertFalse(verdict["passed"])
        self.assertEqual([REASON_CONFIDENCE], verdict["reasons"])

    def test_sample_failure_reason_string(self) -> None:
        verdict = ReLUGate.evaluate(Signal("x", "roas_delta", 0.10, 0.90, 8))
        self.assertFalse(verdict["passed"])
        self.assertEqual([REASON_SAMPLE % 8], verdict["reasons"])
        self.assertIn("sample too small (n=8 < 15)", verdict["reason"])


class GuardrailTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = SignalFactoryPipeline()

    def test_exactly_one_guardrail_block_per_scenario(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.pipeline.run(scenario)
            validate = next(s for s in run["stages"] if s["stage"] == "validate")
            blocked = [item for item in validate["items"] if item["blocked"]]
            self.assertEqual(1, len(blocked), scenario)

    def test_blocked_action_absent_from_act_stage(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.pipeline.run(scenario)
            validate = next(s for s in run["stages"] if s["stage"] == "validate")
            act = next(s for s in run["stages"] if s["stage"] == "act")
            blocked_ids = {i["action_id"] for i in validate["items"] if i["blocked"]}
            executed_ids = {i["action_id"] for i in act["items"]}
            self.assertTrue(blocked_ids)
            self.assertFalse(blocked_ids & executed_ids, scenario)

    def test_every_execution_is_dry_run_with_rollback_token(self) -> None:
        run = self.pipeline.run("ecommerce_roas")
        act = next(s for s in run["stages"] if s["stage"] == "act")
        for record in act["items"]:
            self.assertEqual("dry_run", record["mode"])
            self.assertEqual("executed", record["status"])
            self.assertTrue(record["rollback_token"].startswith("hmac-demo:"))

    def test_causal_truth_is_derived_from_run_data(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.pipeline.run(scenario)
            card = run["decision_card"]
            truth = card["causal_truth"]
            self.assertIsInstance(truth, str, scenario)
            self.assertIn(card["executed_action"]["entity_id"], truth, scenario)
            self.assertIn("ranked #1 by expected value × confidence", truth, scenario)
            self.assertIn(card["guardrail_block"]["entity_id"], truth, scenario)
            self.assertIn("vetoed before execution", truth, scenario)
            self.assertIn("arithmetic against a declared constraint", truth, scenario)


class StreamingFramesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = SignalFactoryPipeline()

    def test_frame_ordering(self) -> None:
        frames = list(self.pipeline.run_streaming("ecommerce_roas"))
        types = [frame["type"] for frame in frames]
        expected_order = ["raw_event", "canonical_event", "signal_gate", "stage", "decision_card", "done"]
        # Types appear in blocks, in the expected order.
        collapsed = [types[0]]
        for frame_type in types[1:]:
            if frame_type != collapsed[-1]:
                collapsed.append(frame_type)
        self.assertEqual(expected_order, collapsed)
        self.assertEqual("done", types[-1])
        stage_names = [f["data"]["stage"] for f in frames if f["type"] == "stage"]
        self.assertEqual(list(SignalFactoryPipeline.STAGES), stage_names)

    def test_frame_content_matches_non_streaming_run(self) -> None:
        run = self.pipeline.run("leadgen_cpa")
        frames = list(self.pipeline.run_streaming("leadgen_cpa"))
        stage_frames = [f["data"] for f in frames if f["type"] == "stage"]
        self.assertEqual(run["stages"], stage_frames)
        card = next(f["data"] for f in frames if f["type"] == "decision_card")
        self.assertEqual(run["decision_card"], card)
        raw_count = sum(1 for f in frames if f["type"] == "raw_event")
        self.assertEqual(run["funnel"]["events_sensed"], raw_count)
        gate_count = sum(1 for f in frames if f["type"] == "signal_gate")
        self.assertEqual(run["funnel"]["signals_formed"], gate_count)

    def test_stream_stays_small_and_terminates(self) -> None:
        for scenario in ALL_SCENARIOS:
            frames = list(self.pipeline.run_streaming(scenario))
            self.assertLess(len(frames), 200, scenario)
            total_delay_ms = sum(f["delay_hint_ms"] for f in frames)
            self.assertLessEqual(total_delay_ms, 60_000, scenario)
            self.assertEqual("done", frames[-1]["type"])


class FlaskDemoSignalTestCase(unittest.TestCase):
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
            "/api/demo/signal/run", json={"scenario": "ecommerce_roas"}
        )
        self.assertEqual(200, response.status_code)
        run = response.get_json()
        funnel = run["funnel"]
        sense = next(s for s in run["stages"] if s["stage"] == "sense")
        act = next(s for s in run["stages"] if s["stage"] == "act")
        self.assertEqual(funnel["events_sensed"], sense["counts"]["raw_events"])
        self.assertEqual(funnel["executed"], len(act["items"]))
        self.assertLessEqual(funnel["executed"], funnel["validated"])
        self.assertLessEqual(funnel["validated"], funnel["signals_formed"] + 1)
        self.assertLessEqual(funnel["passed_gate"], funnel["signals_formed"])
        self.assertEqual(funnel, run["decision_card"]["funnel"])

    def test_run_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.post("/api/demo/signal/run", json={"scenario": "nope"})
        self.assertEqual(400, response.status_code)
        self.assertIn("scenario", response.get_json()["error"])

    def test_run_endpoint_rejects_non_integer_seed(self) -> None:
        response = self.client.post(
            "/api/demo/signal/run", json={"scenario": "ecommerce_roas", "seed": "abc"}
        )
        self.assertEqual(400, response.status_code)

    def test_scenarios_endpoint_lists_all_three(self) -> None:
        response = self.client.get("/api/demo/signal/scenarios")
        self.assertEqual(200, response.status_code)
        ids = {s["id"] for s in response.get_json()["scenarios"]}
        self.assertEqual(set(ALL_SCENARIOS), ids)

    def test_sse_endpoint_streams_parseable_frames(self) -> None:
        response = self.client.get(
            "/api/demo/signal/stream?scenario=ecommerce_roas&seed=42"
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.content_type.startswith("text/event-stream"))
        self.assertEqual("no-cache", response.headers["Cache-Control"])
        body = response.get_data(as_text=True)
        first_frame = body.split("\n\n")[0]
        lines = first_frame.splitlines()
        self.assertEqual("event: raw_event", lines[0])
        payload = json.loads(lines[1].split("data: ", 1)[1])
        self.assertIn("event_id", payload)
        self.assertIn("event: done", body)

    def test_sse_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.get("/api/demo/signal/stream?scenario=bogus")
        self.assertEqual(400, response.status_code)

    def test_demo_pages_are_served(self) -> None:
        for path in ("/demo", "/demo/signal", "/demo/counsel"):
            response = self.client.get(path)
            self.assertEqual(200, response.status_code, path)

    def test_mcp_tool_registered_and_callable(self) -> None:
        tools = self.client.get("/api/mcp/tools").get_json()["tools"]
        names = {tool["name"] for tool in tools}
        self.assertIn("demo.signal.run", names)
        self.assertIn("demo.signal.list_scenarios", names)

        response = self.client.post(
            "/api/mcp/call",
            json={"name": "demo.signal.run", "arguments": {"scenario": "ecommerce_roas"}},
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertEqual("demo.signal.run", payload["resolved_tool"])
        self.assertEqual("ecommerce_roas", payload["result"]["scenario"])
        self.assertEqual(
            payload["result"],
            SignalFactoryPipeline().run("ecommerce_roas", seed=DEFAULT_SEED),
        )

    def test_mcp_list_scenarios_tool(self) -> None:
        response = self.client.post(
            "/api/mcp/call", json={"name": "demo.signal.list_scenarios", "arguments": {}}
        )
        self.assertEqual(200, response.status_code)
        ids = {s["id"] for s in response.get_json()["result"]["scenarios"]}
        self.assertEqual(set(ALL_SCENARIOS), ids)


if __name__ == "__main__":
    unittest.main()
