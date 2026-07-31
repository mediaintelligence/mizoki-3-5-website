"""Tests for the Nexus Run engine + its Flask/MCP integration."""

import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime
from mizoki_runtime.demo_counsel import UNAUTHORIZED_PRACTICE_WARNING
from mizoki_runtime.demo_nexus import (
    DEFAULT_SEED,
    DIVISIONS,
    SCENARIOS,
    TAGLINE,
    NexusRunEngine,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_SCENARIOS = tuple(SCENARIOS)


class NexusEngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = NexusRunEngine()

    def test_same_seed_produces_deep_equal_runs(self) -> None:
        for scenario in ALL_SCENARIOS:
            self.assertEqual(
                self.engine.run(scenario, seed=DEFAULT_SEED),
                self.engine.run(scenario, seed=DEFAULT_SEED),
                scenario,
            )

    def test_unknown_scenario_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.run("not_a_scenario")

    def test_shared_trace_id_appears_in_all_five_division_segments(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.engine.run(scenario)
            divisions = run["divisions"]
            self.assertEqual(5, len(divisions), scenario)
            self.assertEqual(set(DIVISIONS), {seg["division"] for seg in divisions})
            for segment in divisions:
                self.assertEqual(
                    run["nexus_trace_id"], segment["nexus_trace_id"],
                    (scenario, segment["division"]),
                )

    def test_cpm_shock_has_exactly_one_capital_block_and_one_risk_veto(self) -> None:
        run = self.engine.run("cpm_shock")
        capital = next(s for s in run["divisions"] if s["division"] == "capital")
        blocked = capital["verdict"]["blocked"]
        self.assertEqual(["covenant_headroom"], blocked["blocked_by"])
        risk = next(s for s in run["divisions"] if s["division"] == "risk")
        veto = risk["verdict"]["veto"]
        self.assertEqual("vetoed", veto["kind"])
        self.assertTrue(veto["rollback_token"].startswith("hmac-demo:"))
        # Exactly one of each across the whole run.
        self.assertEqual(1, run["divisions"].count(capital))
        self.assertEqual(1, risk["funnel"]["vetoed"])

    def test_counsel_and_estate_lanes_carry_flag_and_exact_warning(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.engine.run(scenario)
            for division in ("counsel", "estate"):
                segment = next(s for s in run["divisions"] if s["division"] == division)
                self.assertTrue(segment["flagged_for_review"], (scenario, division))
                self.assertEqual(
                    UNAUTHORIZED_PRACTICE_WARNING,
                    segment["unauthorized_practice_warning"],
                    (scenario, division),
                )

    def test_provenance_hangs_every_division_off_the_trace(self) -> None:
        run = self.engine.run("cpm_shock")
        edges = run["provenance"]["edges"]
        targets = {edge["to"] for edge in edges if edge["from"] == "nexus"}
        self.assertEqual(set(DIVISIONS), targets)
        self.assertEqual(TAGLINE, run["tagline"])

    def test_stream_frame_ordering_terminates_with_done(self) -> None:
        for scenario in ALL_SCENARIOS:
            frames = list(self.engine.run_streaming(scenario))
            self.assertLess(len(frames), 200, scenario)
            types = [frame["type"] for frame in frames]
            self.assertEqual("trigger", types[0], scenario)
            self.assertEqual("done", types[-1], scenario)
            self.assertEqual("provenance", types[-2], scenario)
            self.assertEqual(5, types.count("division_start"), scenario)
            self.assertEqual(5, types.count("division_verdict"), scenario)
            total_delay = sum(frame["delay_hint_ms"] for frame in frames)
            self.assertLessEqual(total_delay, 90_000, scenario)


class FlaskDemoNexusTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_run_endpoint_returns_nexus_trace_id(self) -> None:
        response = self.client.post("/api/demo/nexus/run", json={"scenario": "cpm_shock"})
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.get_json()["nexus_trace_id"].startswith("nex-"))

    def test_run_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.post("/api/demo/nexus/run", json={"scenario": "nope"})
        self.assertEqual(400, response.status_code)

    def test_stream_endpoint_ends_with_done(self) -> None:
        response = self.client.get("/api/demo/nexus/stream?scenario=cpm_shock&seed=42")
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.content_type.startswith("text/event-stream"))
        body = response.get_data(as_text=True)
        frames = [f for f in body.strip().split("\n\n") if f]
        self.assertTrue(frames[0].startswith("event: trigger"))
        self.assertTrue(frames[-1].startswith("event: done"))
        done_payload = json.loads(frames[-1].splitlines()[1].split("data: ", 1)[1])
        self.assertIn("nexus_trace_id", done_payload)

    def test_page_served_with_absolute_urls_and_boardroom(self) -> None:
        response = self.client.get("/demo/nexus")
        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn('href="/assets/css/styles.css"', body)
        self.assertNotIn('href="assets/', body)
        self.assertIn("Boardroom mode", body)

    def test_mcp_tool_registered_and_callable(self) -> None:
        names = {t["name"] for t in self.client.get("/api/mcp/tools").get_json()["tools"]}
        self.assertIn("demo.nexus.run", names)
        self.assertIn("demo.nexus.list_scenarios", names)
        response = self.client.post(
            "/api/mcp/call", json={"name": "demo.nexus.run", "arguments": {}}
        )
        self.assertEqual(200, response.status_code)
        result = response.get_json()["result"]
        self.assertEqual("cpm_shock", result["scenario"])
        self.assertEqual(result, NexusRunEngine().run("cpm_shock", seed=DEFAULT_SEED))


if __name__ == "__main__":
    unittest.main()
