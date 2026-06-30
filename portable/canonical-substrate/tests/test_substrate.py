"""Standalone proof the bundle works in isolation — no Flask, no BossRuntime.

Run from the bundle root (portable/canonical-substrate):
    python3 -m unittest tests.test_substrate
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Make the package importable when run from the bundle root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from canonical_substrate import (  # noqa: E402
    IdentityClusterResolver,
    envelope_builder,
    journey_schema,
    normalizer,
)

_META_EVENT = {
    "event_name": "Purchase",
    "event_time": 1719945600,
    "user_data": {"em": "alice", "ph": "ph-hash", "client_ip_address": "1.2.3.4"},
    "custom_data": {"value": 59.99, "currency": "USD", "order_id": "A123",
                    "campaign_id": "111", "ad_id": "333"},
}


class SubstrateTestCase(unittest.TestCase):
    def test_normalize_to_envelope_to_identity_flow(self) -> None:
        event = normalizer().normalize("meta", _META_EVENT)
        self.assertEqual([], journey_schema().validate(event))
        self.assertEqual("meta", event["event_source"])

        built = envelope_builder().build_and_validate(event)
        self.assertTrue(built["valid"], msg=built["errors"])
        env = built["envelope"]
        self.assertEqual("2.0.0", env["schema_version"])
        self.assertEqual("Conversion", env["classification"]["category"])
        self.assertEqual("Campaign:111", env["kg_refs"]["CampaignNodeID"])
        self.assertEqual("SENSE", env["srpvdal_state"]["current_phase"])

    def test_identity_resolver_stitches_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clusters.json"
            a = IdentityClusterResolver(path).resolve({"email": "x@y.com", "user_id": "u1"})
            b = IdentityClusterResolver(path).resolve({"email": "x@y.com", "device_ifa": "d1"})
            self.assertEqual(a["identity_cluster"], b["identity_cluster"])  # shared email + persisted
            self.assertIsNone(IdentityClusterResolver(path).resolve({"ip": "9.9.9.9"})["identity_cluster"])

    def test_openrtb_normalizes(self) -> None:
        event = normalizer().normalize("openrtb", {
            "id": "auc-1", "imp": [{"id": "1", "bidfloor": 0.8}],
            "device": {"ifa": "ifa123", "ip": "1.1.1.1"},
        })
        self.assertEqual([], journey_schema().validate(event))
        self.assertEqual("auc-1", event["context"]["auction_id"])


if __name__ == "__main__":
    unittest.main()
