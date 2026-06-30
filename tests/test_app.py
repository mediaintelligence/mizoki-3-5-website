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

    def test_programmatic_pipeline_and_runs_endpoints(self) -> None:
        events = [
            {
                "exchange": "openx",
                "seat": "seat-1",
                "buyer_id": "buyer-1",
                "bid_price": 1.5,
                "bid_floor": 0.5,
                "outcome": "win" if index < 10 else "loss",
                "clearing_price": 1.0,
                "revenue": 0.0,
                "currency": "USD",
            }
            for index in range(30)
        ]

        run_response = self.client.post(
            "/api/boss/programmatic/run",
            json={"events": events, "objective": "Reduce wasted spend."},
        )
        self.assertEqual(200, run_response.status_code)
        run_payload = run_response.get_json()
        self.assertIn("trace_id", run_payload)
        self.assertEqual("validate", run_payload["validate"]["gate"])
        self.assertEqual(30, run_payload["sense"]["ingested_event_count"])

        runs_response = self.client.get("/api/boss/programmatic/runs")
        self.assertEqual(200, runs_response.status_code)
        runs_payload = runs_response.get_json()
        self.assertTrue(any(run["trace_id"] == run_payload["trace_id"] for run in runs_payload["runs"]))

    def test_programmatic_ingest_endpoint_validates_events(self) -> None:
        response = self.client.post("/api/boss/programmatic/ingest", json={"events": "nope"})
        self.assertEqual(400, response.status_code)
        self.assertIn("must be an array", response.get_json()["error"])

    def test_journey_schema_is_served(self) -> None:
        response = self.client.get("/schemas/journey-event.json")
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertEqual("JourneyEvent", payload["title"])
        self.assertEqual(
            ["meta", "google_ads", "sendgrid", "openrtb", "other"],
            payload["properties"]["event_source"]["enum"],
        )
        response.close()

    def test_journey_normalize_endpoint_returns_canonical_event(self) -> None:
        response = self.client.post(
            "/api/boss/journey/normalize",
            json={
                "source": "openrtb",
                "payload": {
                    "id": "auc-1",
                    "imp": [{"id": "1", "tagid": "slot-7", "bidfloor": 0.8}],
                    "site": {"domain": "news.com"},
                    "device": {"ifa": "ifa123"},
                },
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertTrue(payload["valid"])
        self.assertEqual("openrtb", payload["event"]["event_source"])
        self.assertEqual("auc-1", payload["event"]["context"]["auction_id"])

    def test_journey_ingest_endpoint_is_idempotent(self) -> None:
        event = {
            "event": "open",
            "timestamp": 1719945600,
            "email": "lead@example.com",
            "sg_message_id": "SG.abc.def",
        }
        first = self.client.post(
            "/api/boss/journey/ingest",
            json={"source": "sendgrid", "events": [event]},
        )
        self.assertEqual(200, first.status_code)
        self.assertEqual(1, first.get_json()["idempotency"]["inserted"])

        second = self.client.post(
            "/api/boss/journey/ingest",
            json={"source": "sendgrid", "events": [event], "replay": True},
        )
        self.assertEqual(200, second.status_code)
        self.assertEqual(1, second.get_json()["idempotency"]["duplicate"])

        events_response = self.client.get("/api/boss/journey/events")
        self.assertEqual(200, events_response.status_code)
        self.assertEqual(1, len(events_response.get_json()["events"]))

    def test_journey_ingest_endpoint_validates_events(self) -> None:
        response = self.client.post("/api/boss/journey/ingest", json={"source": "meta", "events": "nope"})
        self.assertEqual(400, response.status_code)
        self.assertIn("must be an array", response.get_json()["error"])

    def test_canonical_envelope_schema_is_served(self) -> None:
        response = self.client.get("/schemas/canonical-event-envelope.json")
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertEqual("CanonicalEventEnvelope", payload["title"])
        self.assertIn("canonical_payload", payload["properties"])
        response.close()

    def test_journey_envelope_endpoint_returns_layered_envelope(self) -> None:
        response = self.client.post(
            "/api/boss/journey/envelope",
            json={
                "source": "meta",
                "payload": {
                    "event_name": "Purchase",
                    "event_time": 1719945600,
                    "user_data": {"em": "hash"},
                    "custom_data": {"campaign_id": "111", "ad_id": "333", "order_id": "A123", "value": 59.99, "currency": "USD"},
                },
                "business_context": {"kpi": "ROAS", "target": 4.0},
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertTrue(payload["valid"])
        env = payload["envelope"]
        self.assertEqual("2.0.0", env["schema_version"])
        self.assertEqual("Conversion", env["classification"]["category"])
        self.assertEqual("Campaign:111", env["kg_refs"]["CampaignNodeID"])
        self.assertEqual("SENSE", env["srpvdal_state"]["current_phase"])
        self.assertEqual("ROAS", env["business_context"]["kpi"])
        self.assertEqual("meta", env["canonical_payload"]["event_source"])

    def test_discover_exposes_envelope_block(self) -> None:
        response = self.client.get("/api/boss/discover")
        self.assertEqual(200, response.status_code)
        journey = response.get_json()["journey"]
        self.assertIn("envelope", journey)
        self.assertEqual("2.0.0", journey["envelope"]["schema_version"])
        self.assertIn("classification", journey["envelope"]["layers"])
        self.assertIn("identity_resolution", journey)
        self.assertIn("user_id", journey["identity_resolution"]["stitch_keys"])
        self.assertIn("ip", journey["identity_resolution"]["excluded_keys"])

    def test_identity_resolve_endpoint_returns_cluster(self) -> None:
        response = self.client.post(
            "/api/boss/identity/resolve",
            json={"actor": {"email": "buyer@example.com", "user_id": "u-42"}},
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertTrue(payload["identity_cluster"].startswith("Cluster:"))
        self.assertFalse(payload["anonymous"])
        # A second event sharing the email resolves to the same cluster.
        again = self.client.post(
            "/api/boss/identity/resolve",
            json={"actor": {"email": "buyer@example.com", "device_ifa": "dev-1"}},
        )
        self.assertEqual(payload["identity_cluster"], again.get_json()["identity_cluster"])

    def test_identity_resolve_endpoint_validates_actor(self) -> None:
        response = self.client.post("/api/boss/identity/resolve", json={"actor": "nope"})
        self.assertEqual(400, response.status_code)
        self.assertIn("must be an object", response.get_json()["error"])

    def test_google_ads_validate_endpoint_flags_sunset_version(self) -> None:
        response = self.client.post(
            "/api/boss/google-ads/validate",
            json={
                "query": "SELECT campaign.id FROM campaign",
                "api_version": "v19",
                "as_of": "2026-06-30",
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertFalse(payload["valid"])
        self.assertTrue(any(e["code"] == "api_version_sunset" for e in payload["errors"]))

    def test_google_ads_validate_endpoint_requires_query(self) -> None:
        response = self.client.post("/api/boss/google-ads/validate", json={"query": ""})
        self.assertEqual(400, response.status_code)

    def test_google_ads_validate_batch_endpoint(self) -> None:
        response = self.client.post(
            "/api/boss/google-ads/validate-batch",
            json={
                "queries": [
                    "SELECT campaign.id FROM campaign",
                    "SELECT campaign.bogus FROM campaign",
                ],
                "api_version": "v21",
                "as_of": "2026-06-30",
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertEqual(2, payload["received"])
        self.assertEqual(1, payload["valid"])

    def test_google_ads_versions_endpoint_returns_schedule(self) -> None:
        response = self.client.get("/api/boss/google-ads/versions?as_of=2026-06-30")
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertIn("schedule", payload)
        self.assertTrue(any(v["status"] == "sunset" for v in payload["schedule"]))

    def test_google_ads_fields_endpoint_returns_metadata(self) -> None:
        response = self.client.get("/api/boss/google-ads/fields?resource=campaign")
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertTrue(payload["known_resource"])
        self.assertIn("campaign", payload["resource"])

    def test_discover_exposes_google_ads_block(self) -> None:
        response = self.client.get("/api/boss/discover")
        self.assertEqual(200, response.status_code)
        block = response.get_json()["google_ads"]
        self.assertIn("google_ads.validate_gaql", block["tools"])
        self.assertIn("default_version", block)


if __name__ == "__main__":
    unittest.main()
