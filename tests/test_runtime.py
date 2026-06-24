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
                "journey.ingest_events",
                "journey.normalize_event",
                "journey.recent_events",
                "kg.describe_entity",
                "kg.list_neighbors",
                "programmatic.ingest_bidstream",
                "programmatic.recent_runs",
                "programmatic.run_pipeline",
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

    def test_programmatic_pipeline_runs_full_srpvdal_and_persists(self) -> None:
        events = _seat_events("seat-waste", "openx", total=30, wins=10, revenue_per_win=0.0)
        trace = self.runtime.run_programmatic_pipeline(events, objective="Cut wasted spend.")

        for stage in ("sense", "reason", "plan", "validate", "decide", "act", "learn"):
            self.assertIn(stage, trace)
        self.assertEqual(30, trace["sense"]["ingested_event_count"])
        self.assertEqual(4, len(trace["sense"]["sinks"]))
        self.assertTrue(
            any(anomaly["type"] == "spend_no_return" for anomaly in trace["reason"]["anomalies"])
        )
        self.assertTrue(any(item["type"].startswith("suppress") for item in trace["plan"]["candidates"]))
        self.assertEqual("validate", trace["validate"]["gate"])
        # auto_execute defaults to False, so approved actions wait for sign-off.
        self.assertEqual("needs_approval", trace["decide"]["status"])
        self.assertTrue(all(action["status"] == "pending_approval" for action in trace["act"]["actions"]))

        runs = self.runtime.recent_programmatic_runs(limit=5)
        self.assertEqual(1, len(runs))
        self.assertEqual(trace["trace_id"], runs[0]["trace_id"])

    def test_programmatic_safety_gate_blocks_unsafe_scaling(self) -> None:
        # A seat with both a consent gap and a low win rate yields a suppress plan
        # (safe) and an increase-bid plan (scales spend on non-consented supply).
        events = _seat_events(
            "seat-risky", "ssp-x", total=30, wins=3, revenue_per_win=4.0, consent=False
        )
        trace = self.runtime.run_programmatic_pipeline(events)

        results = {item["action_id"]: item for item in trace["validate"]["results"]}
        blocked_types = {results[action_id]["type"] for action_id in trace["validate"]["blocked"]}
        self.assertIn("increase_bid", blocked_types)
        self.assertTrue(trace["validate"]["passed"])  # the suppress plan still clears the gate
        consent_anomalies = [a for a in trace["reason"]["anomalies"] if a["type"] == "consent_gap"]
        self.assertTrue(consent_anomalies)

    def test_programmatic_auto_execute_approves_scale_opportunity(self) -> None:
        events = _seat_events("seat-star", "openx", total=30, wins=10, revenue_per_win=4.0)
        trace = self.runtime.run_programmatic_pipeline(events, auto_execute=True)

        self.assertEqual("approved", trace["decide"]["status"])
        self.assertTrue(trace["act"]["executed"])
        executed = [action for action in trace["act"]["actions"] if action["status"] == "executed"]
        self.assertTrue(executed)
        self.assertTrue(all(action["rollback"]["available"] for action in executed))

    def test_programmatic_ingest_only_runs_sense_stage(self) -> None:
        events = _seat_events("seat-a", "openx", total=12, wins=4, revenue_per_win=2.0)
        sense = self.runtime.ingest_bidstream(events)
        self.assertEqual(12, sense["ingested_event_count"])
        self.assertIn("openx", sense["coverage"]["exchanges"])
        self.assertEqual(4, len(sense["sinks"]))

    def test_programmatic_rejects_empty_or_invalid_events(self) -> None:
        with self.assertRaises(ValueError):
            self.runtime.run_programmatic_pipeline([])
        with self.assertRaises(ValueError):
            self.runtime.ingest_bidstream("not-a-list")

    def test_journey_normalizes_each_connector_into_canonical_schema(self) -> None:
        cases = {
            "meta": (_META_EVENT, "Purchase", "campaign_id", "111"),
            "google_ads": (_GOOGLE_ADS_ROW, "conversion", "campaign_id", "111"),
            "sendgrid": (_SENDGRID_EVENT, "click", "message_id", "SG.x.y"),
            "openrtb": (_OPENRTB_REQUEST, "bid_request", "auction_id", "auc-1"),
        }
        for source, (payload, expected_type, context_key, context_value) in cases.items():
            result = self.runtime.normalize_journey_event(source, payload)
            self.assertTrue(result["valid"], msg=f"{source} errors: {result['errors']}")
            event = result["event"]
            self.assertEqual(source, event["event_source"])
            self.assertEqual(expected_type, event["event_type"])
            self.assertEqual(context_value, event["context"][context_key])
            self.assertTrue(event["event_time"])  # always populated (schema-required)
            self.assertEqual([], self.runtime.journey.schema.validate(event))

    def test_journey_provenance_pins_model_and_schema_hash(self) -> None:
        result = self.runtime.normalize_journey_event("sendgrid", _SENDGRID_EVENT)
        provenance = result["event"]["provenance"]
        for field in (
            "model_version",
            "request_id",
            "prompt_hash",
            "response_schema_hash",
            "connector_version",
            "ingest_time",
        ):
            self.assertTrue(provenance[field], msg=f"missing provenance.{field}")
        self.assertEqual("SENSE", provenance["srpvdal_phase"])
        self.assertEqual(self.runtime.journey.schema.schema_hash, provenance["response_schema_hash"])
        self.assertEqual("mizoki/ingest/sendgrid", provenance["pipeline"])

    def test_journey_event_id_is_stable_and_ingest_is_idempotent(self) -> None:
        first = self.runtime.normalize_journey_event("meta", _META_EVENT)["event"]
        second = self.runtime.normalize_journey_event("meta", _META_EVENT)["event"]
        self.assertEqual(first["event_id"], second["event_id"])

        initial = self.runtime.ingest_journey_events("meta", [_META_EVENT])
        self.assertEqual(1, initial["accepted"])
        self.assertEqual(1, initial["idempotency"]["inserted"])

        replayed = self.runtime.ingest_journey_events("meta", [_META_EVENT], replay=True)
        self.assertEqual(1, replayed["idempotency"]["duplicate"])
        self.assertEqual(0, replayed["idempotency"]["inserted"])
        self.assertEqual(1, self.runtime.journey.store.count())

    def test_journey_ingest_persists_and_fans_out_to_sinks(self) -> None:
        batch = [_META_EVENT, _SENDGRID_EVENT]
        summary = self.runtime.ingest_journey_events("meta", [_META_EVENT])
        sendgrid_summary = self.runtime.ingest_journey_events("sendgrid", [_SENDGRID_EVENT])
        self.assertEqual("SENSE", summary["srpvdal_phase"])
        self.assertEqual(4, len(summary["sinks"]))
        self.assertTrue(all(sink["status"] == "written" for sink in summary["sinks"]))
        recent = self.runtime.recent_journey_events(limit=10)
        self.assertEqual(2, len(recent))
        self.assertEqual({"meta", "sendgrid"}, {event["event_source"] for event in recent})
        self.assertEqual(len(batch), summary["received"] + sendgrid_summary["received"])

    def test_journey_validation_gate_rejects_bad_records(self) -> None:
        result = self.runtime.ingest_journey_events("meta", [_META_EVENT, "not-an-object"])
        self.assertEqual(1, result["accepted"])
        self.assertEqual(1, result["rejected"])
        self.assertEqual(1, result["rejections"][0]["index"])
        self.assertTrue(result["rejections"][0]["errors"])

    def test_journey_rejects_unknown_source_and_bad_payload(self) -> None:
        with self.assertRaises(ValueError):
            self.runtime.normalize_journey_event("tiktok", _META_EVENT)
        with self.assertRaises(ValueError):
            self.runtime.normalize_journey_event("meta", "not-a-dict")
        with self.assertRaises(ValueError):
            self.runtime.ingest_journey_events("meta", [])


# Canonical JourneyEvent test vectors (one per connector).
_META_EVENT = {
    "event_name": "Purchase",
    "event_time": 1719945600,
    "user_data": {"em": "hash", "ph": "hash", "client_ip_address": "1.2.3.4", "client_user_agent": "UA"},
    "custom_data": {
        "value": 59.99,
        "currency": "USD",
        "order_id": "A123",
        "campaign_id": "111",
        "adset_id": "222",
        "ad_id": "333",
    },
}

_GOOGLE_ADS_ROW = {
    "campaign": {"id": "111"},
    "ad_group": {"id": "222"},
    "ad_group_ad": {"ad": {"id": "333"}},
    "metrics": {"conversions": 1, "conversions_value": 59.99},
    "customer": {"currency_code": "USD"},
    "segments": {"date": "2026-06-22", "hour": 14, "geo_target_country": "US"},
}

_SENDGRID_EVENT = {
    "event": "click",
    "timestamp": 1719945600,
    "email": "sam@example.com",
    "sg_message_id": "SG.x.y",
    "url": "https://site.com/p/abc",
}

_OPENRTB_REQUEST = {
    "id": "auc-1",
    "imp": [{"id": "1", "tagid": "slot-7", "bidfloor": 0.8}],
    "site": {"domain": "news.com"},
    "device": {"ifa": "ifa123", "ip": "1.1.1.1", "ua": "UA"},
}


def _bid_event(seat, exchange, outcome, *, bid=1.5, floor=0.5, clearing=1.0, revenue=0.0, consent=True):
    event = {
        "exchange": exchange,
        "seat": seat,
        "buyer_id": "buyer-1",
        "bid_price": bid,
        "bid_floor": floor,
        "outcome": outcome,
        "currency": "USD",
        "consent": {"gdpr": 0} if consent else {"gdpr": 1},
    }
    if outcome == "win":
        event["clearing_price"] = clearing
        event["revenue"] = revenue
    return event


def _seat_events(seat, exchange, *, total, wins, revenue_per_win, consent=True):
    events = []
    for index in range(total):
        if index < wins:
            events.append(_bid_event(seat, exchange, "win", revenue=revenue_per_win, consent=consent))
        else:
            events.append(_bid_event(seat, exchange, "loss", consent=consent))
    return events


if __name__ == "__main__":
    unittest.main()
