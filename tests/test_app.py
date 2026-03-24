import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime


REPO_ROOT = Path(__file__).resolve().parents[1]


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_root_static_assets_are_served(self) -> None:
        response = self.client.get("/app.js")
        self.assertEqual(200, response.status_code)
        self.assertIn(b"Application JavaScript", response.data)
        response.close()

    def test_mcp_tools_endpoint_returns_registered_tools(self) -> None:
        response = self.client.get("/api/mcp/tools")
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertIn("tools", payload)
        self.assertTrue(any(tool["name"] == "graphrag.query" for tool in payload["tools"]))

    def test_boss_execute_endpoint_selects_tool_and_returns_context(self) -> None:
        response = self.client.post(
            "/api/boss/execute",
            json={"intent": "Explain the Decision Control Plane."},
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertIn("selection", payload)
        self.assertIn("context", payload)
        self.assertIn("candidates", payload)
        self.assertTrue(payload["context"]["matched_entities"])

    def test_learn_skill_endpoint_validates_required_fields(self) -> None:
        response = self.client.post("/api/boss/skills/learn", json={"name": "bad"})
        self.assertEqual(400, response.status_code)
        self.assertIn("Missing required field", response.get_json()["error"])

    def test_mcp_call_returns_400_for_unknown_tools(self) -> None:
        response = self.client.post("/api/mcp/call", json={"name": "nope", "arguments": {}})
        self.assertEqual(400, response.status_code)
        self.assertIn("unknown tool", response.get_json()["error"])

    def test_duplicate_skill_returns_400_instead_of_server_error(self) -> None:
        first_response = self.client.post(
            "/api/boss/skills/learn",
            json={"name": "dcp", "description": "desc", "trigger_phrases": ["decision control plane"]},
        )
        self.assertEqual(200, first_response.status_code)

        second_response = self.client.post(
            "/api/boss/skills/learn",
            json={"name": "dcp", "description": "desc", "trigger_phrases": ["decision control plane"]},
        )
        self.assertEqual(400, second_response.status_code)
        self.assertIn("skill already exists", second_response.get_json()["error"])

    def test_boss_can_learn_skill_via_natural_language_execute_request(self) -> None:
        response = self.client.post(
            "/api/boss/execute",
            json={"intent": "Learn a new skill for decision control plane questions."},
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertEqual("skills.learn", payload["selection"]["tool_name"])
        self.assertIn("decision.explain_pipeline", payload["execution"]["result"]["skill"]["preferred_tools"])

    def test_graph_native_context_and_loop_endpoints_work(self) -> None:
        context_response = self.client.post(
            "/api/boss/graph/context",
            json={"intent": "Map the graph-native context for the decision control plane."},
        )
        self.assertEqual(200, context_response.status_code)
        context_payload = context_response.get_json()
        self.assertIn("context", context_payload)
        self.assertTrue(context_payload["context"]["recommended_subagents"])

        loop_response = self.client.post(
            "/api/boss/graph/loop",
            json={
                "intent": "Run the graph-native decision loop for platform governance.",
                "goal": "Produce an audit-ready decision path.",
            },
        )
        self.assertEqual(200, loop_response.status_code)
        loop_payload = loop_response.get_json()
        self.assertIn("trace_id", loop_payload)
        self.assertIn("act", loop_payload)
        self.assertTrue(loop_payload["act"]["assigned_subagents"])

        simulation_response = self.client.post(
            "/api/boss/graph/simulate",
            json={
                "intent": "Simulate a counterfactual for the decision control plane.",
                "proposed_action": "Tighten validation before action.",
            },
        )
        self.assertEqual(200, simulation_response.status_code)
        simulation_payload = simulation_response.get_json()
        self.assertIn("counterfactual_delta", simulation_payload)

    def test_graph_native_subagent_endpoint_lists_cells(self) -> None:
        response = self.client.get("/api/boss/graph/subagents")
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertIn("subagents", payload)
        self.assertTrue(any(item["stage"] == "sense" for item in payload["subagents"]))

    def test_learn_skill_from_loop_endpoint_promotes_recent_loop(self) -> None:
        loop_response = self.client.post(
            "/api/boss/graph/loop",
            json={"intent": "Run the graph-native decision loop for platform governance."},
        )
        self.assertEqual(200, loop_response.status_code)
        trace_id = loop_response.get_json()["trace_id"]

        learn_response = self.client.post(
            "/api/boss/skills/learn-from-loop",
            json={"trace_id": trace_id},
        )
        self.assertEqual(200, learn_response.status_code)
        payload = learn_response.get_json()
        self.assertIn("skill", payload)
        self.assertTrue(payload["skill"]["preferred_tools"])

    def test_graph_context_endpoint_rejects_invalid_top_k(self) -> None:
        response = self.client.post(
            "/api/boss/graph/context",
            json={"intent": "Explain the platform.", "top_k": 0},
        )
        self.assertEqual(400, response.status_code)
        self.assertIn("at least 1", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
