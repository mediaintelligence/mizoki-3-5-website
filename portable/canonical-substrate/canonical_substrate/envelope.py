"""CanonicalEventEnvelope (v2) — the universal reasoning contract.

Wraps the canonical JourneyEvent (v1) as ``canonical_payload`` and layers on the
reasoning-native sections defined by ``schemas/canonical-event-envelope.json``.
Everything here is deterministic and dependency-free, in the same style as the
v1 normalizer: the SENSE-computable layers (metadata, version vector,
classification, identity, kg_refs, relationships, time intelligence, security,
data quality, observability, SRPVDAL state, field confidence) are populated at
ingest; the loop-filled layers (evaluation, actions, learning, causal effects,
intelligence) are initialized as typed scaffolds for downstream cells to write.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from .journey import (
    JourneyEventSchema,
    _coerce_epoch_seconds,
    _iso_from_epoch_seconds,
    canonical_compact_json,
    sha256_hex,
)


ENVELOPE_SCHEMA_VERSION = "2.0.0"

# Version vector defaults (env-overridable) — recorded per envelope so a decision
# can be reproduced against the exact policy/ontology/reasoning generation.
_VERSION_ENV = {
    "policy_version": "MIZOKI_POLICY_VERSION",
    "governance_version": "MIZOKI_GOVERNANCE_VERSION",
    "ontology_version": "MIZOKI_ONTOLOGY_VERSION",
    "reasoning_version": "MIZOKI_REASONING_VERSION",
}

# Deterministic semantic classification by (source, event_type-family).
_DOMAIN_BY_SOURCE = {
    "meta": "Advertising",
    "google_ads": "Advertising",
    "openrtb": "Advertising",
    "sendgrid": "Marketing",
    "other": "General",
}
# event_type (lowered) -> (category, intent)
_CATEGORY_BY_TYPE = {
    "purchase": ("Conversion", "Commercial"),
    "conversion": ("Conversion", "Commercial"),
    "lead": ("Conversion", "Commercial"),
    "subscribe": ("Conversion", "Commercial"),
    "click": ("Engagement", "Engagement"),
    "open": ("Engagement", "Engagement"),
    "impression": ("Delivery", "Awareness"),
    "delivered": ("Delivery", "Operational"),
    "processed": ("Delivery", "Operational"),
    "bid_request": ("Auction", "Awareness"),
    "win": ("Auction", "Awareness"),
    "loss": ("Auction", "Awareness"),
    "bounce": ("Deliverability", "Operational"),
    "spamreport": ("Deliverability", "Operational"),
    "unsubscribe": ("Preference", "Operational"),
}

# Identity resolution: strongest available key wins; confidence by key strength.
_IDENTITY_PRIORITY = (
    ("user_id", 0.99),
    ("email", 0.9),
    ("phone_sha256", 0.9),
    ("device_ifa", 0.7),
    ("ip", 0.4),
)
_STRONG_IDENTITY_KEYS = {"user_id", "email", "phone_sha256", "device_ifa"}
_PII_FIELDS = ("email", "phone_sha256", "ip", "device_ifa")


def _version_vector() -> dict[str, str]:
    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        **{key: (os.environ.get(env) or "1.0.0") for key, env in _VERSION_ENV.items()},
    }


def _iso_to_epoch(value: Any) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return _coerce_epoch_seconds(value)


def classify(event_source: str, event_type: str) -> dict[str, Any]:
    domain = _DOMAIN_BY_SOURCE.get(event_source, "General")
    category, intent = _CATEGORY_BY_TYPE.get(event_type.strip().lower(), ("Event", "Operational"))
    return {
        "domain": domain,
        "category": category,
        "subcategory": event_type,
        "intent": intent,
        # Deterministic rule-based classification is certain; LLM-derived events
        # can override via field_confidence on the classification key.
        "confidence": 1.0,
    }


def _resolve_identity(actor: dict[str, Any]) -> dict[str, Any]:
    present = [(key, conf) for key, conf in _IDENTITY_PRIORITY if actor.get(key)]
    if not present:
        return {"identity_id": None, "confidence": 0.0, "resolution_method": None,
                "identity_cluster": None, "anonymous": True}
    strongest_key = present[0][0]
    identity_id = f"Identity:{sha256_hex(str(actor[strongest_key]))[:16]}"
    anonymous = not any(key in _STRONG_IDENTITY_KEYS for key, _ in present)
    return {
        "identity_id": identity_id,
        "confidence": present[0][1],
        "resolution_method": "+".join(key for key, _ in present),
        # Cross-event clustering needs a stateful resolver cell; pending at SENSE.
        "identity_cluster": None,
        "anonymous": anonymous,
    }


def _kg_refs(event: dict[str, Any], identity_id: str | None) -> dict[str, Any]:
    ctx = event.get("context", {})
    actor = event.get("actor", {})
    ext = ctx.get("ext", {}) if isinstance(ctx.get("ext"), dict) else {}

    def node(label: str, value: Any) -> str | None:
        return f"{label}:{value}" if value else None

    return {
        "CampaignNodeID": node("Campaign", ctx.get("campaign_id")),
        "CreativeNodeID": node("Creative", ctx.get("ad_id")),
        "AudienceNodeID": node("Audience", ext.get("audience_id") or ext.get("adgroup_id")),
        "CustomerNodeID": node("Customer", actor.get("user_id")),
        "OrderNodeID": node("Order", ctx.get("order_id")),
        "IdentityNodeID": identity_id,
        "SessionNodeID": node("Session", ext.get("session_id")),
    }


def _relationships(event_node: str, kg: dict[str, Any], causal: dict[str, Any]) -> list[dict[str, Any]]:
    edge_for = {
        "CampaignNodeID": "BELONGS_TO",
        "CreativeNodeID": "ATTRIBUTED_TO",
        "AudienceNodeID": "TARGETED",
        "CustomerNodeID": "PERFORMED_BY",
        "OrderNodeID": "RESULTED_IN",
        "IdentityNodeID": "IDENTIFIED_AS",
    }
    rels = [
        {"type": rel, "source": event_node, "target": kg[ref]}
        for ref, rel in edge_for.items()
        if kg.get(ref)
    ]
    for parent in causal.get("parent_events", []):
        rels.append({"type": "GENERATED_BY", "source": parent, "target": event_node})
    return rels


class CanonicalEnvelopeBuilder:
    """Build a validated CanonicalEventEnvelope from a v1 JourneyEvent."""

    def __init__(self, envelope_schema_path, journey_schema: JourneyEventSchema) -> None:
        self.schema = JourneyEventSchema(envelope_schema_path)  # generic validator
        self.journey_schema = journey_schema

    def build(
        self,
        journey_event: dict[str, Any],
        *,
        business_context: dict[str, Any] | None = None,
        reasoning_context: dict[str, Any] | None = None,
        causal: dict[str, Any] | None = None,
        intelligence: dict[str, Any] | None = None,
        field_confidence: dict[str, Any] | None = None,
        processing_time: float | None = None,
    ) -> dict[str, Any]:
        if not isinstance(journey_event, dict):
            raise ValueError("journey_event must be a JSON object")

        event_id = journey_event.get("event_id", "")
        actor = journey_event.get("actor", {}) if isinstance(journey_event.get("actor"), dict) else {}
        ctx = journey_event.get("context", {}) if isinstance(journey_event.get("context"), dict) else {}
        v1_prov = journey_event.get("provenance", {}) if isinstance(journey_event.get("provenance"), dict) else {}
        event_source = journey_event.get("event_source", "other")
        event_type = journey_event.get("event_type", "event")

        proc_seconds = processing_time if processing_time is not None else time.time()
        processing_iso = _iso_from_epoch_seconds(proc_seconds)
        event_time = journey_event.get("event_time")
        ingest_time = journey_event.get("ingest_time")
        event_epoch = _iso_to_epoch(event_time)
        latency_ms = round((proc_seconds - event_epoch) * 1000, 2) if event_epoch is not None else None

        identity = _resolve_identity(actor)
        kg = _kg_refs(journey_event, identity["identity_id"])
        causal_block = {
            "parent_events": list((causal or {}).get("parent_events", [])),
            "caused_by": list((causal or {}).get("caused_by", [])),
            "predicted_effect": (causal or {}).get("predicted_effect"),
            "counterfactual_id": (causal or {}).get("counterfactual_id"),
        }
        relationships = _relationships(f"Event:{event_id}", kg, causal_block)

        v1_errors = self.journey_schema.validate(journey_event)
        scalar_fields = [actor.get(key) for key in actor] + [value for key, value in ctx.items() if key != "ext"]
        non_null = sum(1 for value in scalar_fields if value not in (None, ""))
        completeness = round(non_null / len(scalar_fields), 4) if scalar_fields else 0.0

        pii = [field for field in _PII_FIELDS if actor.get(field)]
        ext = ctx.get("ext", {}) if isinstance(ctx.get("ext"), dict) else {}

        if field_confidence is None:
            field_confidence = {key: 1.0 for key, value in ctx.items() if key != "ext" and value is not None}

        envelope_id = f"env-{event_id}"
        version_vector = _version_vector()

        envelope = {
            "schema_version": ENVELOPE_SCHEMA_VERSION,
            "envelope_id": envelope_id,
            "metadata": {
                "envelope_id": envelope_id,
                "event_source": event_source,
                "event_type": event_type,
                "created_at": processing_iso,
                "schema_version": ENVELOPE_SCHEMA_VERSION,
            },
            "provenance": {
                "model_version": v1_prov.get("model_version"),
                "request_id": v1_prov.get("request_id"),
                "prompt_hash": v1_prov.get("prompt_hash"),
                "response_schema_hash": v1_prov.get("response_schema_hash"),
                "connector_version": v1_prov.get("connector_version", "unknown"),
                "source_payload_hash": journey_event.get("source_payload_hash") or v1_prov.get("source_payload_hash"),
                "pipeline": v1_prov.get("pipeline"),
                **version_vector,
            },
            "identity": identity,
            "security": {
                "classification": "restricted" if pii else "internal",
                "pii": pii,
                "gdpr": ext.get("gdpr") if isinstance(ext.get("gdpr"), bool) else None,
                "hipaa": False,
                "encrypted": False,
                "retention_policy": "standard-365d",
                "consent": ext.get("consent") if isinstance(ext.get("consent"), str) else None,
            },
            "data_quality": {
                "schema_valid": not v1_errors,
                "validation_errors": v1_errors,
                "missing_fields": [
                    field for field in ("event_id", "event_time", "event_source", "event_type", "provenance", "actor", "context")
                    if not journey_event.get(field)
                ],
                "completeness": completeness,
                "freshness_seconds": round(latency_ms / 1000, 4) if latency_ms is not None else None,
                "duplicate_probability": 0.0,
            },
            "business_context": {
                "objective_id": (business_context or {}).get("objective_id"),
                "kpi": (business_context or {}).get("kpi"),
                "target": (business_context or {}).get("target"),
                "priority": (business_context or {}).get("priority"),
                "owner": (business_context or {}).get("owner"),
            },
            "reasoning_context": {
                "business_unit": (reasoning_context or {}).get("business_unit"),
                "goal": (reasoning_context or {}).get("goal"),
                "objective": (reasoning_context or {}).get("objective"),
                "constraint_set": list((reasoning_context or {}).get("constraint_set", [])),
                "guardrails": list((reasoning_context or {}).get("guardrails", [])),
                "policies": list((reasoning_context or {}).get("policies", [])),
            },
            "kg_refs": kg,
            "relationships": relationships,
            "classification": classify(event_source, event_type),
            "field_confidence": field_confidence,
            "causal": causal_block,
            "time_intelligence": {
                "event_time": event_time,
                "source_time": event_time,
                "ingest_time": ingest_time,
                "processing_time": processing_iso,
                "decision_time": None,
                "latency_ms": latency_ms,
                "watermark": processing_iso,
            },
            "srpvdal_state": {
                "current_phase": "SENSE",
                "previous_phase": None,
                "next_phase": "REASON",
                "retry_count": 0,
                "phase_history": [
                    {"phase": "SENSE", "at": processing_iso, "outcome": "normalized", "duration_ms": None}
                ],
            },
            "observability": {
                "trace_id": f"trace-{sha256_hex(event_id)[:16]}",
                "span_id": f"span-{sha256_hex(event_id + '|sense')[:12]}",
                "workflow_id": "wf.journey.ingest",
                "execution_id": v1_prov.get("request_id") or f"exec-{sha256_hex(event_id)[:12]}",
                "agent_id": "agent.boss",
                "cell_id": "cell.sense.journey_ingest",
            },
            "intelligence": {
                "reasoning_engine": (intelligence or {}).get("reasoning_engine"),
                "planner": (intelligence or {}).get("planner"),
                "validator": (intelligence or {}).get("validator"),
                "decision_engine": (intelligence or {}).get("decision_engine"),
                "learning_engine": (intelligence or {}).get("learning_engine"),
                "confidence": (intelligence or {}).get("confidence"),
            },
            # Loop-filled scaffolds — written by REASON -> LEARN, empty at SENSE.
            "evaluation": {},
            "actions": {"recommended": [], "approved": [], "executed": [], "rolled_back": [], "status": None},
            "learning": {},
            "canonical_payload": journey_event,
            "audit": [
                {"phase": "SENSE", "actor": "cell.sense.journey_ingest", "at": processing_iso,
                 "note": "normalized to JourneyEvent v1 and wrapped in CanonicalEventEnvelope v2"}
            ],
        }
        return envelope

    def build_and_validate(self, journey_event: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        envelope = self.build(journey_event, **kwargs)
        errors = self.schema.validate(envelope)
        return {"envelope": envelope, "valid": not errors, "errors": errors}

    def discovery_block(self) -> dict[str, Any]:
        return {
            "schema": self.schema.schema.get("$id"),
            "schema_version": ENVELOPE_SCHEMA_VERSION,
            "wraps": "journey-event.json (v1) as canonical_payload",
            "layers": [
                "metadata", "provenance", "identity", "security", "data_quality",
                "business_context", "reasoning_context", "kg_refs", "relationships",
                "classification", "field_confidence", "causal", "time_intelligence",
                "srpvdal_state", "observability", "intelligence", "evaluation",
                "actions", "learning", "canonical_payload", "audit",
            ],
            "version_vector": _version_vector(),
        }
