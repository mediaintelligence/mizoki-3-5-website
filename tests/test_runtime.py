import json
import tempfile
import unittest
from pathlib import Path

from mizoki_runtime import create_runtime
from mizoki_runtime.journey import JourneyIngestCell
from mizoki_runtime.journey_gemini import (
    GeminiJourneyExtractor,
    VertexGeminiJourneyExtractor,
    gemini_extractor_metadata,
    to_vertex_response_schema,
    vertex_extractor_metadata,
)
from mizoki_runtime.journey_sinks import (
    BigQueryJourneySink,
    FirestoreJourneySink,
    build_journey_sinks_from_env,
    build_merge_sql,
    event_to_bigquery_row,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "journey-event.json"


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

    def _cell(self, sinks):
        store = Path(self.temp_dir.name) / "journey_sink_test.jsonl"
        return JourneyIngestCell(SCHEMA_PATH, store, external_sinks=sinks)

    def test_journey_forwards_writes_to_external_sinks_and_skips_duplicates(self) -> None:
        sink = _RecordingSink()
        cell = self._cell([sink])

        first = cell.ingest("meta", [_META_EVENT])
        self.assertEqual(1, first["external_sinks"][0]["written"])
        self.assertEqual([_first_event_id(cell, "meta", _META_EVENT)], sink.events)

        # A replay is a store duplicate, so it must NOT be forwarded again.
        replay = cell.ingest("meta", [_META_EVENT], replay=True)
        self.assertEqual(0, replay["external_sinks"][0]["written"])
        self.assertEqual(1, len(sink.events))

    def test_journey_external_sink_errors_degrade_without_failing_batch(self) -> None:
        cell = self._cell([_RecordingSink(name="boom", fail=True)])
        result = cell.ingest("sendgrid", [_SENDGRID_EVENT])
        self.assertEqual(1, result["accepted"])  # in-process store still succeeded
        self.assertEqual(0, result["external_sinks"][0]["written"])
        self.assertTrue(result["external_sinks"][0]["errors"])

    def test_firestore_sink_upserts_document_by_event_id(self) -> None:
        client = _FakeFirestoreClient()
        sink = FirestoreJourneySink(collection="journey_events", client=client)
        event = self.runtime.normalize_journey_event("meta", _META_EVENT)["event"]
        self.assertEqual("written", sink.upsert(event))
        self.assertIn(event["event_id"], client.store)
        stored = client.store[event["event_id"]]
        self.assertTrue(stored["merge"])
        self.assertEqual(event["event_source"], stored["event"]["event_source"])

    def test_bigquery_merge_sql_and_row_projection(self) -> None:
        event = self.runtime.normalize_journey_event("openrtb", _OPENRTB_REQUEST)["event"]
        sql = build_merge_sql("analytics.journey_events")
        self.assertIn("MERGE `analytics.journey_events`", sql)
        self.assertIn("ON T.event_id = S.event_id", sql)
        row = event_to_bigquery_row(event)
        self.assertEqual(event["event_id"], row["event_id"])
        self.assertEqual("auc-1", json.loads(row["context"])["auction_id"])
        self.assertEqual(event["event_source"], json.loads(row["provenance"])["pipeline"].split("/")[-1])

    def test_build_journey_sinks_from_env(self) -> None:
        self.assertEqual([], build_journey_sinks_from_env({}))
        sinks = build_journey_sinks_from_env(
            {
                "MIZOKI_JOURNEY_FIRESTORE_COLLECTION": "je",
                "MIZOKI_JOURNEY_BIGQUERY_TABLE": "analytics.journey_events",
            }
        )
        self.assertEqual({"firestore:je", "bigquery:analytics.journey_events"}, {sink.name for sink in sinks})
        self.assertIsInstance(sinks[0], FirestoreJourneySink)
        self.assertIsInstance(sinks[1], BigQueryJourneySink)

    def test_gemini_extractor_threads_provenance_into_canonical_event(self) -> None:
        captured = {}

        def fake_transport(url, headers, body):
            captured["url"] = url
            captured["headers"] = headers
            captured["body"] = json.loads(body.decode("utf-8"))
            model_event = {
                "event_source": "sendgrid",
                "event_type": "click",
                "actor": {"email": "sam@example.com"},
                "context": {"channel": "email", "message_id": "SG.x.y"},
                "event_time": "2026-06-22T14:03:12Z",
            }
            return {
                "modelVersion": "gemini-2.0-pro-exp-02-05",
                "responseId": "resp-123",
                "candidates": [{"content": {"parts": [{"text": json.dumps(model_event)}]}}],
            }

        extractor = GeminiJourneyExtractor(self.runtime.journey.normalizer, transport=fake_transport)
        result = extractor.extract("Emit one JourneyEvent for a SendGrid click.", event_source="sendgrid")

        self.assertTrue(result["valid"], msg=result["errors"])
        event = result["event"]
        self.assertEqual("sendgrid", event["event_source"])
        self.assertEqual("click", event["event_type"])
        self.assertEqual("sam@example.com", event["actor"]["email"])
        self.assertEqual("2026-06-22T14:03:12Z", event["event_time"])
        self.assertEqual("gemini-2.0-pro-exp-02-05", event["provenance"]["model_version"])
        self.assertEqual("resp-123", event["provenance"]["request_id"])
        self.assertEqual(self.runtime.journey.schema.schema_hash, event["provenance"]["response_schema_hash"])
        self.assertEqual("mizoki/ingest/llm", event["provenance"]["pipeline"])
        # The request pins the model + enforces the strict schema response_format.
        self.assertTrue(captured["body"]["response_format"]["strict"])
        self.assertEqual("gemini-2.0-pro-exp-02-05", captured["body"]["model_version"])
        self.assertEqual("2026-06-01", captured["headers"]["X-Api-Revision"])

    def test_gemini_extractor_requires_credentials_without_transport(self) -> None:
        extractor = GeminiJourneyExtractor(self.runtime.journey.normalizer, api_key=None)
        self.assertFalse(extractor.configured)
        with self.assertRaises(RuntimeError):
            extractor.extract("Emit one JourneyEvent.")

    def test_gemini_extractor_metadata_reports_pinned_model(self) -> None:
        meta = gemini_extractor_metadata({})
        self.assertEqual("google-gemini", meta["provider"])
        self.assertEqual("gemini-2.0-pro-exp-02-05", meta["model"])
        self.assertTrue(meta["strict_response_format"])
        self.assertFalse(meta["configured"])
        self.assertTrue(gemini_extractor_metadata({"GEMINI_API_KEY": "x"})["configured"])

    def test_vertex_extractor_uses_adc_client_and_threads_provenance(self) -> None:
        model_event = {
            "event_source": "google_ads",
            "event_type": "conversion",
            "actor": {"device_ifa": "ifa-9"},
            "context": {"channel": "search", "campaign_id": "111", "value": 59.99},
            "event_time": "2026-06-22T14:00:00Z",
        }
        client = _FakeGenaiClient(model_event, model_version="gemini-2.0-pro", response_id="vtx-1")
        extractor = VertexGeminiJourneyExtractor(self.runtime.journey.normalizer, project="proj-x", client=client)
        self.assertTrue(extractor.configured)
        result = extractor.extract("Extract a Google Ads conversion JourneyEvent.", event_source="google_ads")

        self.assertTrue(result["valid"], msg=result["errors"])
        event = result["event"]
        self.assertEqual("google_ads", event["event_source"])
        self.assertEqual("conversion", event["event_type"])
        self.assertEqual("gemini-2.0-pro", event["provenance"]["model_version"])
        self.assertEqual("vtx-1", event["provenance"]["request_id"])
        self.assertEqual(self.runtime.journey.schema.schema_hash, event["provenance"]["response_schema_hash"])
        self.assertEqual("vertex://proj-x/us-central1/" + extractor.model, result["model_provenance"]["raw_uri"])
        # The config carries a strict, Vertex-shaped response_schema and JSON mime.
        sent = client.models.calls[0]
        self.assertEqual("application/json", sent["config"]["response_mime_type"])
        self.assertIn("response_schema", sent["config"])

    def test_vertex_extractor_requires_project_without_client(self) -> None:
        extractor = VertexGeminiJourneyExtractor(self.runtime.journey.normalizer, project="")
        self.assertFalse(extractor.configured)
        with self.assertRaises(RuntimeError):
            extractor.extract("Extract a JourneyEvent.")

    def test_vertex_response_schema_is_vertex_compatible(self) -> None:
        vertex_schema = to_vertex_response_schema(self.runtime.journey.schema.schema)
        # No JSON-Schema meta keys Vertex rejects.
        self.assertNotIn("$schema", vertex_schema)
        self.assertNotIn("$id", vertex_schema)
        self.assertNotIn("additionalProperties", vertex_schema)
        # Nullable unions are rewritten to type + nullable.
        ingest = vertex_schema["properties"]["ingest_time"]
        self.assertEqual("string", ingest["type"])
        self.assertTrue(ingest["nullable"])
        self.assertNotIn("additionalProperties", vertex_schema["properties"]["context"])

    def test_vertex_extractor_metadata_reports_adc_and_project(self) -> None:
        meta = vertex_extractor_metadata({})
        self.assertEqual("google-vertex-ai", meta["provider"])
        self.assertEqual("application-default-credentials", meta["auth"])
        self.assertEqual("us-central1", meta["location"])
        self.assertFalse(meta["configured"])
        self.assertTrue(vertex_extractor_metadata({"GOOGLE_CLOUD_PROJECT": "p"})["configured"])


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


class _RecordingSink:
    """Duck-typed external sink used to assert delegation without cloud libs."""

    def __init__(self, name="recording", fail=False):
        self.name = name
        self.fail = fail
        self.events = []

    def upsert(self, event):
        if self.fail:
            raise RuntimeError("simulated sink failure")
        self.events.append(event["event_id"])
        return "written"


class _FakeDoc:
    def __init__(self, store, key):
        self._store = store
        self._key = key

    def set(self, event, merge=False):
        self._store[self._key] = {"event": event, "merge": merge}


class _FakeCollection:
    def __init__(self, store):
        self._store = store

    def document(self, key):
        return _FakeDoc(self._store, key)


class _FakeFirestoreClient:
    def __init__(self):
        self.store = {}

    def collection(self, _name):
        return _FakeCollection(self.store)


def _first_event_id(cell, source, payload):
    return cell.normalizer.normalize(source, payload)["event_id"]


class _FakeGenaiResponse:
    def __init__(self, text, model_version, response_id):
        self.text = text
        self.model_version = model_version
        self.response_id = response_id


class _FakeGenaiModels:
    def __init__(self, payload, model_version, response_id):
        self._payload = payload
        self._model_version = model_version
        self._response_id = response_id
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        return _FakeGenaiResponse(json.dumps(self._payload), self._model_version, self._response_id)


class _FakeGenaiClient:
    """Duck-typed google-genai client: exposes .models.generate_content(...)."""

    def __init__(self, payload, *, model_version="gemini-2.0-pro", response_id="vtx-1"):
        self.models = _FakeGenaiModels(payload, model_version, response_id)


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
