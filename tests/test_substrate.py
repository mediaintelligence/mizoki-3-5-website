"""Tests for the canonical reasoning substrate ported from mizoki-3-5-website.

Covers the SENSE-stage layer — JourneyEvent v1 normalization, CanonicalEventEnvelope
v2 construction, cross-event identity clusters — plus the Virtuoso model plane.
"""

import tempfile
import unittest
from pathlib import Path

from mizoki_runtime import create_runtime
from mizoki_runtime.identity import IdentityClusterResolver
from mizoki_runtime.virtuoso import GLOBAL_FALLBACK


REPO_ROOT = Path(__file__).resolve().parents[1]


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


class SubstrateRuntimeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_substrate_tools_are_registered(self) -> None:
        tool_names = {tool["name"] for tool in self.runtime.list_tools()}
        expected = {
            "journey.normalize_event",
            "journey.ingest_events",
            "journey.recent_events",
            "journey.build_envelope",
            "identity.resolve",
            "identity.cluster_stats",
            "virtuoso.registry",
            "virtuoso.resolve_model",
            "virtuoso.scan_legacy",
            "virtuoso.reasoning_traces",
        }
        self.assertTrue(expected.issubset(tool_names), msg=f"missing: {expected - tool_names}")

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
            self.assertTrue(event["event_time"])
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

    def test_journey_ingest_persists_and_reports_sinks(self) -> None:
        summary = self.runtime.ingest_journey_events("meta", [_META_EVENT])
        sendgrid_summary = self.runtime.ingest_journey_events("sendgrid", [_SENDGRID_EVENT])
        self.assertEqual("SENSE", summary["srpvdal_phase"])
        self.assertTrue(summary["sinks"])
        self.assertTrue(all(sink["status"] == "written" for sink in summary["sinks"]))
        recent = self.runtime.recent_journey_events(limit=10)
        self.assertEqual(2, len(recent))
        self.assertEqual({"meta", "sendgrid"}, {event["event_source"] for event in recent})
        self.assertEqual(2, summary["received"] + sendgrid_summary["received"])

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

    def test_build_envelope_is_deterministic(self) -> None:
        a = self.runtime.build_journey_envelope("meta", _META_EVENT)["envelope"]
        b = self.runtime.build_journey_envelope("meta", _META_EVENT)["envelope"]
        self.assertEqual(a["envelope_id"], b["envelope_id"])
        self.assertEqual(a["identity"]["identity_id"], b["identity"]["identity_id"])
        self.assertEqual(a["kg_refs"], b["kg_refs"])

    def test_build_envelope_populates_resolved_identity_cluster(self) -> None:
        result = self.runtime.build_journey_envelope("meta", _META_EVENT)
        self.assertTrue(result["valid"], msg=result["errors"])
        cluster = result["envelope"]["identity"]["identity_cluster"]
        self.assertIsNotNone(cluster)
        self.assertTrue(cluster.startswith("Cluster:"))
        self.assertEqual(cluster, result["identity_resolution"]["identity_cluster"])
        again = self.runtime.build_journey_envelope("meta", _META_EVENT)
        self.assertEqual(cluster, again["envelope"]["identity"]["identity_cluster"])

    def test_identity_resolver_stitches_on_shared_strong_key(self) -> None:
        resolver = IdentityClusterResolver(Path(self.temp_dir.name) / "id_stitch.json")
        a = resolver.resolve({"email": "e1", "user_id": "u1"})
        b = resolver.resolve({"email": "e1", "device_ifa": "d1"})
        c = resolver.resolve({"email": "e9"})
        self.assertEqual(a["identity_cluster"], b["identity_cluster"])
        self.assertNotEqual(a["identity_cluster"], c["identity_cluster"])
        self.assertGreaterEqual(b["cluster_size"], 3)

    def test_identity_resolver_merges_previously_separate_clusters(self) -> None:
        resolver = IdentityClusterResolver(Path(self.temp_dir.name) / "id_merge.json")
        first = resolver.resolve({"email": "alice@x.com"})
        second = resolver.resolve({"device_ifa": "dev-9"})
        self.assertNotEqual(first["identity_cluster"], second["identity_cluster"])
        bridge = resolver.resolve({"email": "alice@x.com", "device_ifa": "dev-9"})
        self.assertTrue(bridge["newly_merged"])
        after = resolver.resolve({"device_ifa": "dev-9"})
        self.assertEqual(bridge["identity_cluster"], after["identity_cluster"])

    def test_identity_resolver_ignores_weak_ip_only_actor(self) -> None:
        resolver = IdentityClusterResolver(Path(self.temp_dir.name) / "id_ip.json")
        result = resolver.resolve({"ip": "1.2.3.4"})
        self.assertIsNone(result["identity_cluster"])
        self.assertTrue(result["anonymous"])
        self.assertEqual([], result["linked_keys"])

    def test_identity_resolver_persists_across_instances(self) -> None:
        path = Path(self.temp_dir.name) / "id_persist.json"
        first = IdentityClusterResolver(path).resolve({"email": "persist@x.com"})
        reloaded = IdentityClusterResolver(path).resolve({"email": "persist@x.com"})
        self.assertEqual(first["identity_cluster"], reloaded["identity_cluster"])

    def test_discover_includes_journey_and_virtuoso_blocks(self) -> None:
        discovery = self.runtime.boss.discover()
        self.assertIn("journey", discovery)
        self.assertIn("envelope", discovery["journey"])
        self.assertIn("identity_resolution", discovery["journey"])
        self.assertEqual(GLOBAL_FALLBACK, discovery["virtuoso"]["global_fallback"])

    def test_virtuoso_tools_are_callable_through_mcp(self) -> None:
        resolved = self.runtime.call_tool("virtuoso.resolve_model", {"role": "coding_arch"})
        self.assertEqual(GLOBAL_FALLBACK, resolved["result"]["model"])
        scan = self.runtime.call_tool("virtuoso.scan_legacy", {"text": "gpt-5.2-turbo"})
        self.assertEqual(["gpt-5.2"], scan["result"]["violations"])
        traces = self.runtime.call_tool("virtuoso.reasoning_traces", {})
        self.assertEqual([], traces["result"]["traces"])


if __name__ == "__main__":
    unittest.main()
