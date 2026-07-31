"""Tests for the Estate Room demo engine + its Flask/MCP integration."""

import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime
from mizoki_runtime.demo_counsel import (
    ALLOWED_AUTHORITY_CITATIONS,
    UNAUTHORIZED_PRACTICE_WARNING,
)
from mizoki_runtime.demo_estate import (
    DEFAULT_SEED,
    SCENARIOS,
    STATUTORY_CLOCK_IDS,
    EstateRoomEngine,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_SCENARIOS = tuple(SCENARIOS)


def _collect_citations(payload):
    """Every {'citation': ...} anywhere in the run."""
    found = set()
    if isinstance(payload, dict):
        if "citation" in payload:
            found.add(payload["citation"])
        for value in payload.values():
            found |= _collect_citations(value)
    elif isinstance(payload, list):
        for item in payload:
            found |= _collect_citations(item)
    return found


class EstateEngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = EstateRoomEngine()

    def test_same_seed_produces_identical_run(self) -> None:
        for scenario in ALL_SCENARIOS:
            self.assertEqual(
                self.engine.run(scenario, seed=DEFAULT_SEED),
                self.engine.run(scenario, seed=DEFAULT_SEED),
                scenario,
            )

    def test_different_seed_changes_valuations(self) -> None:
        run_a = self.engine.run("basis_step_up", seed=1)
        run_b = self.engine.run("basis_step_up", seed=2)
        self.assertNotEqual(run_a["assets"], run_b["assets"])

    def test_unknown_scenario_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.run("not_a_scenario")

    def test_bad_seed_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.run("ct_estate_settlement", seed="abc")

    def test_every_run_carries_flag_and_exact_warning(self) -> None:
        for scenario in ALL_SCENARIOS:
            run = self.engine.run(scenario)
            self.assertTrue(run["flagged_for_review"], scenario)
            self.assertEqual(
                UNAUTHORIZED_PRACTICE_WARNING,
                run["unauthorized_practice_warning"],
                scenario,
            )

    def test_authorities_subset_of_shared_corpus(self) -> None:
        for scenario in ALL_SCENARIOS:
            citations = _collect_citations(self.engine.run(scenario))
            self.assertTrue(citations, scenario)
            self.assertTrue(
                citations <= set(ALLOWED_AUTHORITY_CITATIONS),
                f"{scenario}: {citations - set(ALLOWED_AUTHORITY_CITATIONS)}",
            )

    def test_settlement_timeline_contains_all_five_statutory_clocks(self) -> None:
        run = self.engine.run("ct_estate_settlement")
        clock_ids = {clock["clock_id"] for clock in run["timeline"]}
        self.assertEqual(set(STATUTORY_CLOCK_IDS), clock_ids)
        by_id = {clock["clock_id"]: clock for clock in run["timeline"]}
        self.assertEqual(30, by_id["filing_30"]["day"])
        self.assertEqual(60, by_id["inventory_60"]["day"])
        self.assertEqual(150, by_id["creditor_150"]["day"])
        self.assertEqual(150, by_id["elective_150"]["day"])
        self.assertEqual(183, by_id["ct706_183"]["day"])
        self.assertEqual("CGS § 45a-436", by_id["elective_150"]["authority"]["citation"])
        self.assertEqual("CGS § 12-391", by_id["ct706_183"]["authority"]["citation"])

    def test_dynasty_graph_spans_three_generations(self) -> None:
        run = self.engine.run("gst_dynasty_review")
        generations = {node["generation"] for node in run["graph"]["nodes"]}
        self.assertEqual({1, 2, 3}, generations)
        self.assertTrue(run["grandfather_flag"]["grandfathered"])

    def test_basis_step_up_totals_are_consistent(self) -> None:
        run = self.engine.run("basis_step_up")
        for asset in run["assets"]:
            self.assertEqual(asset["date_of_death_value"], asset["stepped_basis"])
            self.assertEqual(
                asset["date_of_death_value"] - asset["cost_basis"],
                asset["unrealized_gain_eliminated"],
            )
        self.assertEqual(
            sum(a["unrealized_gain_eliminated"] for a in run["assets"]),
            run["totals"]["unrealized_gain_eliminated"],
        )


class FlaskDemoEstateTestCase(unittest.TestCase):
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
            "/api/demo/estate/run", json={"scenario": "ct_estate_settlement"}
        )
        self.assertEqual(200, response.status_code)
        run = response.get_json()
        self.assertTrue(run["flagged_for_review"])
        self.assertEqual(5, len(run["timeline"]))

    def test_run_endpoint_rejects_unknown_scenario(self) -> None:
        response = self.client.post("/api/demo/estate/run", json={"scenario": "nope"})
        self.assertEqual(400, response.status_code)

    def test_run_endpoint_rejects_non_integer_seed(self) -> None:
        response = self.client.post(
            "/api/demo/estate/run", json={"scenario": "basis_step_up", "seed": "x"}
        )
        self.assertEqual(400, response.status_code)

    def test_scenarios_endpoint_lists_all_three(self) -> None:
        response = self.client.get("/api/demo/estate/scenarios")
        ids = {s["id"] for s in response.get_json()["scenarios"]}
        self.assertEqual(set(ALL_SCENARIOS), ids)

    def test_page_served_with_absolute_urls(self) -> None:
        response = self.client.get("/demo/estate")
        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn('href="/assets/css/styles.css"', body)
        self.assertNotIn('href="assets/', body)

    def test_mcp_tool_registered_and_callable(self) -> None:
        names = {t["name"] for t in self.client.get("/api/mcp/tools").get_json()["tools"]}
        self.assertIn("demo.estate.run", names)
        self.assertIn("demo.estate.list_scenarios", names)
        response = self.client.post(
            "/api/mcp/call",
            json={"name": "demo.estate.run", "arguments": {"scenario": "gst_dynasty_review"}},
        )
        self.assertEqual(200, response.status_code)
        result = response.get_json()["result"]
        self.assertEqual("gst_dynasty_review", result["scenario"])
        self.assertEqual(
            result, EstateRoomEngine().run("gst_dynasty_review", seed=DEFAULT_SEED)
        )


if __name__ == "__main__":
    unittest.main()
