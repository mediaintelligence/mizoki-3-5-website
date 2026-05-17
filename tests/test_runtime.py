import tempfile
import unittest
from pathlib import Path

from mizoki_runtime import create_runtime


REPO_ROOT = Path(__file__).resolve().parents[1]


class BossRuntimeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_expected_tools_are_registered(self) -> None:
        tool_names = {tool["name"] for tool in self.runtime.list_tools()}
        self.assertEqual(
            {
                "decision.explain_pipeline",
                "decision.recent_traces",
                "gndi.inspect_context",
                "gndi.list_subagents",
                "gndi.recent_loops",
                "gndi.run_decision_loop",
                "gndi.simulate_action",
                "graphrag.query",
                "kg.describe_entity",
                "kg.list_neighbors",
                "skills.learn",
                "skills.learn_from_loop",
                "skills.list",
                "tools.list",
                "tools.register_alias",
            },
            tool_names,
        )

    def test_registered_tools_expose_complete_argument_schema(self) -> None:
        tools = {tool["name"]: tool for tool in self.runtime.list_tools()}
        schema = tools["graphrag.query"]["argument_schema"]
        self.assertEqual("object", schema["type"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(["query"], schema["required"])
        self.assertEqual("integer", schema["properties"]["top_k"]["type"])
        graph_schema = tools["gndi.run_decision_loop"]["argument_schema"]
        self.assertEqual(["intent"], graph_schema["required"])
        self.assertEqual("array", graph_schema["properties"]["constraints"]["type"])

    def test_alias_tool_registration_is_persisted_and_callable(self) -> None:
        registration = self.runtime.call_tool(
            "tools.register_alias",
            {
                "name": "graphrag.quick_query",
                "description": "Fast GraphRAG lookup for concise answers.",
                "target_tool": "graphrag.query",
                "default_arguments": {"top_k": 1},
                "tags": ["graphrag", "fast"],
            },
        )
        self.assertEqual("graphrag.quick_query", registration["result"]["tool"]["name"])

        execution = self.runtime.call_tool("graphrag.quick_query", {"query": "decision control plane"})
        self.assertEqual("graphrag.query", execution["resolved_tool"])
        self.assertEqual(1, execution["arguments"]["top_k"])
        self.assertTrue(execution["result"]["matches"])

    def test_alias_registration_rejects_invalid_default_arguments(self) -> None:
        with self.assertRaises(ValueError):
            self.runtime.call_tool(
                "tools.register_alias",
                {
                    "name": "graphrag.bad_alias",
                    "description": "Broken alias that should be rejected.",
                    "target_tool": "graphrag.query",
                    "default_arguments": {"top_k": "oops"},
                    "tags": ["graphrag"],
                },
            )

    def test_boss_can_learn_skills_and_route_to_preferred_tool(self) -> None:
        learned_skill = self.runtime.learn_skill(
            {
                "name": "dcp explainer",
                "description": "Prefer the pipeline explainer when users ask about the Decision Control Plane.",
                "trigger_phrases": ["decision control plane", "dcp"],
                "preferred_tools": ["decision.explain_pipeline"],
                "examples": ["Explain the decision control plane."],
            }
        )
        self.assertEqual("dcp explainer", learned_skill["name"])

        execution = self.runtime.execute("Explain the decision control plane and how it governs actions.")
        self.assertEqual("decision.explain_pipeline", execution["selection"]["tool_name"])
        self.assertGreaterEqual(execution["selection"]["confidence"], 0.45)
        self.assertEqual("decision.explain_pipeline", execution["execution"]["resolved_tool"])
        self.assertTrue(execution["candidates"])

    def test_boss_can_learn_skill_from_natural_language_request(self) -> None:
        execution = self.runtime.execute("Learn a new skill for decision control plane questions.")
        self.assertEqual("skills.learn", execution["selection"]["tool_name"])
        learned_skill = execution["execution"]["result"]["skill"]
        self.assertIn("decision.explain_pipeline", learned_skill["preferred_tools"])
        self.assertTrue(any("decision control plane" in phrase.lower() for phrase in learned_skill["trigger_phrases"]))

        follow_up = self.runtime.execute("Decision control plane questions")
        self.assertEqual("decision.explain_pipeline", follow_up["selection"]["tool_name"])

    def test_boss_does_not_misroute_plain_explanations_into_skill_learning(self) -> None:
        execution = self.runtime.execute("Explain the plan.")
        self.assertEqual("decision.explain_pipeline", execution["selection"]["tool_name"])
        self.assertEqual("plan", execution["execution"]["arguments"]["stage"])

    def test_pipeline_explanations_do_not_confuse_plane_with_plan(self) -> None:
        execution = self.runtime.execute("Explain the decision control plane.")
        self.assertEqual("decision.explain_pipeline", execution["selection"]["tool_name"])
        self.assertEqual("", execution["execution"]["arguments"]["stage"])

    def test_boss_records_decision_traces(self) -> None:
        self.runtime.execute("List the available tools.")
        traces = self.runtime.recent_traces(limit=3)
        self.assertEqual(1, len(traces))
        self.assertEqual("tools.list", traces[0]["selection"]["tool_name"])

    def test_graph_native_loop_and_subagents_are_available(self) -> None:
        discovery = self.runtime.discover()
        self.assertIn("graph_native", discovery)
        self.assertTrue(discovery["graph_native"]["subagents"])
        self.assertIn("capabilities", discovery)
        self.assertIn("skills.learn_from_loop", discovery["capabilities"]["skill_learning_tools"])

        loop = self.runtime.run_decision_loop(
            "Run the full graph-native decision loop for the decision control plane.",
            goal="Explain how governance should route this request.",
        )
        self.assertEqual("full_loop", loop["context"]["stage_focus"])
        self.assertTrue(loop["act"]["assigned_subagents"])

        recent_loops = self.runtime.recent_graph_loops(limit=2)
        self.assertEqual(1, len(recent_loops))
        self.assertEqual(loop["trace_id"], recent_loops[0]["trace_id"])

    def test_boss_routes_counterfactual_requests_to_graph_native_simulation(self) -> None:
        execution = self.runtime.execute(
            "Simulate a counterfactual for changing the decision control plane and compare the tradeoff."
        )
        self.assertEqual("gndi.simulate_action", execution["selection"]["tool_name"])
        self.assertEqual("gndi.simulate_action", execution["execution"]["resolved_tool"])
        self.assertIn("counterfactual_delta", execution["execution"]["result"])

    def test_loop_trace_can_be_promoted_to_skill(self) -> None:
        loop = self.runtime.run_decision_loop(
            "Run the graph-native decision loop for knowledge graph governance.",
            goal="Produce a reusable routing pattern.",
        )
        learned = self.runtime.call_tool("skills.learn_from_loop", {"trace_id": loop["trace_id"]})
        self.assertEqual("skills.learn_from_loop", learned["resolved_tool"])
        self.assertTrue(learned["result"]["skill"]["preferred_tools"])

    def test_loop_learning_request_prefers_generating_loop_when_none_exist(self) -> None:
        execution = self.runtime.execute("Learn from loop for graph governance.")
        self.assertEqual("gndi.run_decision_loop", execution["selection"]["tool_name"])

    def test_graph_native_context_rejects_invalid_top_k(self) -> None:
        with self.assertRaises(ValueError):
            self.runtime.graph_context("Explain the platform.", top_k=0)


if __name__ == "__main__":
    unittest.main()
