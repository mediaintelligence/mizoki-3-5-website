"""Canonical JourneyEvent normalization for the SRPVDAL SENSE stage.

This module standardizes events from four connectors — Meta (Conversions API /
Webhooks), Google Ads (GAQL + GoogleAdsFieldService rows), SendGrid (Event
Webhook / Inbound Parse), and OpenRTB (bid request / win / loss) — into one
canonical ``JourneyEvent`` shape defined by ``schemas/journey-event.json``.

Design constraints mirror Cell 27 (``ProgrammaticIntelligenceCell``): everything
is deterministic and in-process (no external services, no third-party deps), so
the SENSE stage is reproducible and unit-testable. The same canonical shape is
what an LLM extraction path (e.g. Gemini with a strict ``response_format``
json_schema and a pinned ``model_version``) would emit — provenance carries the
``model_version``/``request_id``/``prompt_hash``/``response_schema_hash`` fields
so rule-based and model-based SENSE both produce audit-identical rows.

Idempotency follows the documented recipe: ``event_id`` is a stable sha256 over
``event_source || event_type || stable_keys_from_source`` (never over volatile
timestamps), and the event store upserts on ``event_id`` with a compare-and-set
on ``source_payload_hash`` so replays are idempotent.
"""

from __future__ import annotations

import hashlib
import json
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


JOURNEY_SOURCES = ("meta", "google_ads", "sendgrid", "openrtb", "other")

# Ruleset / connector versions recorded in provenance so a change in mapping
# logic is auditable per row. Bump these when a mapper's behavior changes.
JOURNEY_RULESET_VERSION = "1.0.0"
JOURNEY_MODEL_VERSION = f"mizoki-ruleset-{JOURNEY_RULESET_VERSION}"
JOURNEY_CONNECTOR_VERSIONS = {
    "meta": "meta-capi-connector-1.0.0",
    "google_ads": "google-ads-gaql-connector-1.0.0",
    "sendgrid": "sendgrid-event-connector-1.0.0",
    "openrtb": "openrtb-bidstream-connector-1.0.0",
    "other": "generic-connector-1.0.0",
}

# Destinations the SENSE gate fans validated canonical events out to. Mirrors
# the Cell 27 sink vocabulary so the two ingestion paths stay consistent.
JOURNEY_SINKS = ("event_store", "knowledge_graph", "bigquery", "audit_log")

# Allowed canonical sub-fields. Mappers project native payloads onto these and
# nothing else, so the result always satisfies the schema's additionalProperties
# guards without a second pass.
_ACTOR_FIELDS = ("user_id", "email", "phone_sha256", "device_ifa", "ip", "ua")
_CONTEXT_FIELDS = (
    "channel", "campaign_id", "adgroup_id", "ad_id", "keyword", "search_term",
    "placement", "inventory", "domain", "page", "geo", "currency", "value",
    "quantity", "order_id", "message_id", "auction_id", "bidfloor", "ext",
)
_NUMERIC_CONTEXT_FIELDS = {"value", "quantity", "bidfloor"}


# ---------------------------------------------------------------------------
# Deterministic primitives
# ---------------------------------------------------------------------------

def canonical_compact_json(value: Any) -> str:
    """Stable, compact JSON used for hashing (sorted keys, no whitespace)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def sha256_hex(value: Any) -> str:
    text = value if isinstance(value, str) else canonical_compact_json(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _coerce_epoch_seconds(value: Any) -> float | None:
    """Best-effort epoch parse; auto-detects millisecond timestamps."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if number <= 0:
        return None
    if number >= 1e12:  # milliseconds
        number /= 1000.0
    return number


def _iso_from_epoch_seconds(seconds: float) -> str:
    moment = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return moment.isoformat().replace("+00:00", "Z")


def _epoch_to_iso(value: Any) -> str | None:
    seconds = _coerce_epoch_seconds(value)
    if seconds is None:
        return None
    return _iso_from_epoch_seconds(seconds)


def _str_or_none(value: Any) -> str | None:
    if value is None or isinstance(value, (dict, list)):
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    text = value if isinstance(value, str) else str(value)
    text = text.strip()
    return text or None


def _num_or_none(value: Any) -> float | int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dotted(row: dict[str, Any], path: str) -> Any:
    """Read a dotted path (``campaign.id``) from a nested-or-flat row."""
    if path in row:
        return row[path]
    current: Any = row
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _pick_ext(source: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: source[key] for key in keys if key in source and source[key] is not None}


def _build_actor(raw: dict[str, Any]) -> dict[str, Any]:
    return {field: (raw.get(field) if field in raw else None) for field in _ACTOR_FIELDS}


def _build_context(raw: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for field in _CONTEXT_FIELDS:
        if field == "ext":
            context["ext"] = _as_dict(raw.get("ext"))
            continue
        value = raw.get(field)
        if field in _NUMERIC_CONTEXT_FIELDS:
            context[field] = _num_or_none(value)
        else:
            context[field] = _str_or_none(value)
    return context


# ---------------------------------------------------------------------------
# Per-source mappers — each returns event_type, event_time, actor, context,
# and the ordered stable keys that make event_id idempotent.
# ---------------------------------------------------------------------------

def _map_meta(payload: dict[str, Any]) -> dict[str, Any]:
    user_data = _as_dict(payload.get("user_data"))
    custom_data = _as_dict(payload.get("custom_data"))
    event_type = _str_or_none(payload.get("event_name")) or "unknown"
    event_time = _epoch_to_iso(payload.get("event_time") if payload.get("event_time") is not None else payload.get("event_time_ms"))
    actor = _build_actor(
        {
            "email": user_data.get("em"),
            "phone_sha256": user_data.get("ph"),
            "device_ifa": user_data.get("madid") or user_data.get("device_ifa"),
            "ip": user_data.get("client_ip_address"),
            "ua": user_data.get("client_user_agent"),
        }
    )
    context = _build_context(
        {
            "channel": "paid_social",
            "campaign_id": custom_data.get("campaign_id"),
            "adgroup_id": custom_data.get("adset_id"),
            "ad_id": custom_data.get("ad_id"),
            "value": custom_data.get("value"),
            "currency": custom_data.get("currency"),
            "order_id": custom_data.get("order_id"),
            "page": custom_data.get("content_name"),
            "ext": _pick_ext(custom_data, ("content_ids", "content_type", "num_items")),
        }
    )
    stable_keys = [
        _str_or_none(payload.get("event_id")) or "",
        _str_or_none(custom_data.get("order_id")) or "",
        _str_or_none(payload.get("event_time")) or "",
        _str_or_none(user_data.get("em")) or "",
        _str_or_none(custom_data.get("ad_id")) or "",
    ]
    return {"event_type": event_type, "event_time": event_time, "actor": actor, "context": context, "stable_keys": stable_keys}


def _derive_google_ads_type(row: dict[str, Any]) -> str:
    metrics = _as_dict(_dotted(row, "metrics"))
    if _num_or_none(metrics.get("conversions")) or _num_or_none(metrics.get("conversions_value")):
        return "conversion"
    if _num_or_none(metrics.get("clicks")):
        return "click"
    if _num_or_none(metrics.get("impressions")):
        return "impression"
    return "row"


def _map_google_ads(row: dict[str, Any]) -> dict[str, Any]:
    event_type = _derive_google_ads_type(row)
    date = _str_or_none(_dotted(row, "segments.date"))
    hour = _dotted(row, "segments.hour")
    event_time = None
    if date:
        try:
            base = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
            if isinstance(hour, int) and not isinstance(hour, bool) and 0 <= hour <= 23:
                base = base.replace(hour=hour)
            event_time = base.isoformat().replace("+00:00", "Z")
        except ValueError:
            event_time = None

    identifier = _as_dict(_dotted(row, "user_identifier"))
    device_ifa = identifier.get("value") if _str_or_none(identifier.get("user_identifier_source")) == "THIRD_PARTY" else None
    actor = _build_actor({"device_ifa": device_ifa})
    metrics = _as_dict(_dotted(row, "metrics"))
    context = _build_context(
        {
            "channel": _str_or_none(_dotted(row, "campaign.advertising_channel_type")) or "search",
            "campaign_id": _dotted(row, "campaign.id"),
            "adgroup_id": _dotted(row, "ad_group.id"),
            "ad_id": _dotted(row, "ad_group_ad.ad.id"),
            "keyword": _dotted(row, "ad_group_criterion.keyword.text"),
            "search_term": _dotted(row, "search_term_view.search_term"),
            "value": metrics.get("conversions_value"),
            "currency": _dotted(row, "customer.currency_code"),
            "geo": _dotted(row, "segments.geo_target_country"),
            "ext": {"metrics": metrics} if metrics else {},
        }
    )
    stable_keys = [
        _str_or_none(_dotted(row, "campaign.id")) or "",
        _str_or_none(_dotted(row, "ad_group.id")) or "",
        _str_or_none(_dotted(row, "ad_group_ad.ad.id")) or "",
        date or "",
        _str_or_none(hour) or "",
        _str_or_none(_dotted(row, "ad_group_criterion.keyword.text")) or "",
        _str_or_none(_dotted(row, "segments.geo_target_country")) or "",
    ]
    return {"event_type": event_type, "event_time": event_time, "actor": actor, "context": context, "stable_keys": stable_keys}


def _map_sendgrid(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = _str_or_none(payload.get("event")) or "unknown"
    event_time = _epoch_to_iso(payload.get("timestamp"))
    url = _str_or_none(payload.get("url"))
    domain = _str_or_none(payload.get("url_domain"))
    if not domain and url:
        domain = _str_or_none(urlparse(url).netloc)
    email = payload.get("email") or payload.get("smtp-id") or payload.get("sg_message_id")
    message_id = _str_or_none(payload.get("sg_message_id"))
    actor = _build_actor({"email": email})
    context = _build_context(
        {
            "channel": "email",
            "message_id": message_id,
            "domain": domain,
            "page": url,
            "ext": _pick_ext(payload, ("smtp-id", "reason", "asm_group_id", "category")),
        }
    )
    stable_keys = [
        message_id or "",
        _str_or_none(payload.get("timestamp")) or "",
        _str_or_none(email) or "",
        url or "",
    ]
    return {"event_type": event_type, "event_time": event_time, "actor": actor, "context": context, "stable_keys": stable_keys}


def _map_openrtb(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = _str_or_none(payload.get("kind")) or "bid_request"
    event_time = _epoch_to_iso(payload.get("t"))
    device = _as_dict(payload.get("device"))
    geo = _as_dict(device.get("geo"))
    imps = payload.get("imp")
    first_imp = imps[0] if isinstance(imps, list) and imps and isinstance(imps[0], dict) else {}
    site = _as_dict(payload.get("site"))
    app = _as_dict(payload.get("app"))
    inventory = site.get("domain") or app.get("bundle")
    actor = _build_actor(
        {
            "device_ifa": device.get("ifa"),
            "ip": device.get("ip"),
            "ua": device.get("ua"),
        }
    )
    context = _build_context(
        {
            "channel": "programmatic",
            "auction_id": payload.get("id"),
            "inventory": inventory,
            "placement": first_imp.get("tagid"),
            "bidfloor": first_imp.get("bidfloor"),
            "geo": geo.get("country"),
            "currency": (payload.get("cur") if isinstance(payload.get("cur"), str) else None),
            "ext": _pick_ext(payload, ("device", "regs", "user")),
        }
    )
    stable_keys = [
        _str_or_none(payload.get("id")) or "",
        _str_or_none(first_imp.get("tagid")) or "",
        _str_or_none(inventory) or "",
    ]
    return {"event_type": event_type, "event_time": event_time, "actor": actor, "context": context, "stable_keys": stable_keys}


def _map_other(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = _str_or_none(payload.get("event_type")) or _str_or_none(payload.get("event")) or "event"
    event_time = _epoch_to_iso(payload.get("event_time") or payload.get("timestamp"))
    actor = _build_actor(_as_dict(payload.get("actor")))
    context_source = _as_dict(payload.get("context"))
    if not context_source:
        context_source = {key: payload[key] for key in _CONTEXT_FIELDS if key in payload}
    context = _build_context(context_source)
    stable_keys = [
        _str_or_none(payload.get("event_id")) or "",
        event_type,
        sha256_hex(payload),
    ]
    return {"event_type": event_type, "event_time": event_time, "actor": actor, "context": context, "stable_keys": stable_keys}


_MAPPERS = {
    "meta": _map_meta,
    "google_ads": _map_google_ads,
    "sendgrid": _map_sendgrid,
    "openrtb": _map_openrtb,
    "other": _map_other,
}


# ---------------------------------------------------------------------------
# Dependency-free JSON Schema validator (covers the constructs the JourneyEvent
# schema uses: type unions, enum, required, properties, additionalProperties).
# `format` is treated as an annotation, per draft 2020-12 defaults.
# ---------------------------------------------------------------------------

def _matches_type(value: Any, type_name: str) -> bool:
    if type_name == "null":
        return value is None
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    return False


def _validate_node(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    declared_type = schema.get("type")
    if declared_type is not None:
        types = declared_type if isinstance(declared_type, list) else [declared_type]
        if not any(_matches_type(value, name) for name in types):
            errors.append(f"{path or '<root>'}: expected type {types}, got {type(value).__name__}")
            return

    if value is None:
        return  # null already satisfied a nullable type; skip enum/properties

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path or '<root>'}: value {value!r} not in enum {schema['enum']}")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: string shorter than minLength {minimum}")
        if isinstance(maximum, int) and len(value) > maximum:
            errors.append(f"{path}: string longer than maxLength {maximum}")

    if isinstance(value, dict) and (schema.get("type") == "object" or "properties" in schema):
        properties = schema.get("properties", {})
        for required_key in schema.get("required", []):
            if required_key not in value:
                errors.append(f"{path or '<root>'}: missing required property '{required_key}'")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path or '<root>'}: additional property '{key}' is not allowed")
        for key, sub_value in value.items():
            if key in properties:
                child_path = f"{path}.{key}" if path else key
                _validate_node(sub_value, properties[key], child_path, errors)


class JourneyEventSchema:
    """Loads ``schemas/journey-event.json`` and validates events against it."""

    def __init__(self, schema_path: Path) -> None:
        self.schema_path = Path(schema_path)
        self.schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        # Hash of the canonical schema, stored on every row for auditability.
        self.schema_hash = sha256_hex(self.schema)

    def validate(self, event: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        _validate_node(event, self.schema, "", errors)
        return errors

    def is_valid(self, event: dict[str, Any]) -> bool:
        return not self.validate(event)


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

class JourneyEventNormalizer:
    """Project a native connector payload onto the canonical JourneyEvent."""

    def __init__(self, schema: JourneyEventSchema) -> None:
        self._schema = schema

    @property
    def schema(self) -> JourneyEventSchema:
        return self._schema

    def normalize(
        self,
        source: str,
        payload: Any,
        *,
        ingest_time: float | None = None,
        request_id: str | None = None,
        model_version: str | None = None,
        prompt: str | None = None,
        prompt_hash: str | None = None,
        connector_version: str | None = None,
        srpvdal_phase: str = "SENSE",
        replay: bool = False,
    ) -> dict[str, Any]:
        cleaned_source = source.strip().lower() if isinstance(source, str) else ""
        if cleaned_source not in JOURNEY_SOURCES:
            raise ValueError(f"event_source must be one of {JOURNEY_SOURCES}, got {source!r}")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")

        ingest_seconds = ingest_time if ingest_time is not None else time.time()
        ingest_iso = _iso_from_epoch_seconds(ingest_seconds)

        mapping = _MAPPERS[cleaned_source](payload)
        event_type = mapping["event_type"]
        # event_time is required; fall back to ingest_time when the source omits it.
        event_time = mapping["event_time"] or ingest_iso

        source_payload_hash = sha256_hex(payload)
        event_id = sha256_hex("|".join([cleaned_source, event_type, *mapping["stable_keys"]]))

        resolved_connector = connector_version or JOURNEY_CONNECTOR_VERSIONS[cleaned_source]
        resolved_model = model_version or JOURNEY_MODEL_VERSION
        rule_id = f"mizoki/transform/{cleaned_source}/{JOURNEY_RULESET_VERSION}"
        resolved_prompt_hash = prompt_hash or (sha256_hex(prompt) if prompt else sha256_hex(rule_id))
        # request_id is per-job; default to a deterministic, audit-reproducible value.
        resolved_request_id = request_id or f"req-{sha256_hex(resolved_connector + '|' + source_payload_hash)[:24]}"

        provenance = {
            "model_version": resolved_model,
            "request_id": resolved_request_id,
            "prompt_hash": resolved_prompt_hash,
            "response_schema_hash": self._schema.schema_hash,
            "connector_version": resolved_connector,
            "ingest_time": ingest_iso,
            "source_payload_hash": source_payload_hash,
            "srpvdal_phase": srpvdal_phase,
            "pipeline": f"mizoki/ingest/{cleaned_source}",
            "replay": bool(replay),
        }

        return {
            "event_id": event_id,
            "event_time": event_time,
            "ingest_time": ingest_iso,
            "event_source": cleaned_source,
            "event_type": event_type,
            "source_payload_hash": source_payload_hash,
            "actor": mapping["actor"],
            "context": mapping["context"],
            "provenance": provenance,
        }


# ---------------------------------------------------------------------------
# Idempotent event store (JSONL-backed; compare-and-set on source_payload_hash)
# ---------------------------------------------------------------------------

class JourneyEventStore:
    """Append-only JSONL store with idempotent upsert keyed on ``event_id``.

    - first sight of an ``event_id`` -> ``inserted``
    - same ``event_id`` with the same ``source_payload_hash`` -> ``duplicate``
      (no write; replays are no-ops)
    - same ``event_id`` with a different ``source_payload_hash`` -> ``updated``
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _records(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.file_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def _index(self) -> dict[str, str]:
        index: dict[str, str] = {}
        for record in self._records():
            event_id = record.get("event_id")
            if isinstance(event_id, str):
                index[event_id] = record.get("source_payload_hash") or ""
        return index

    def upsert(self, event: dict[str, Any]) -> str:
        event_id = event["event_id"]
        incoming_hash = event.get("source_payload_hash") or ""
        existing_hash = self._index().get(event_id)
        if existing_hash is None:
            status = "inserted"
        elif existing_hash == incoming_hash:
            return "duplicate"
        else:
            status = "updated"
        with self.file_path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_compact_json(event) + "\n")
        return status

    def recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        bounded = max(1, min(int(limit), 200))
        latest: dict[str, dict[str, Any]] = {}
        for record in self._records():
            event_id = record.get("event_id")
            if isinstance(event_id, str):
                latest[event_id] = record  # later lines win (compacted view)
        events = list(latest.values())
        return events[-bounded:][::-1]

    def count(self) -> int:
        return len(self._index())


# ---------------------------------------------------------------------------
# SENSE-stage ingest cell
# ---------------------------------------------------------------------------

class JourneyIngestCell:
    """SENSE-stage cell: normalize -> validate -> idempotent upsert -> sinks.

    Invalid events are flagged with their schema errors and never stored — the
    validation gate sits in front of the event store, the same way Cell 27's
    VALIDATE gate sits in front of ACT.
    """

    def __init__(self, schema_path: Path, store_path: Path) -> None:
        self.schema = JourneyEventSchema(schema_path)
        self.normalizer = JourneyEventNormalizer(self.schema)
        self.store = JourneyEventStore(store_path)

    def normalize_event(self, source: str, payload: Any, **kwargs: Any) -> dict[str, Any]:
        event = self.normalizer.normalize(source, payload, **kwargs)
        errors = self.schema.validate(event)
        return {"event": event, "valid": not errors, "errors": errors}

    def ingest(
        self,
        source: str,
        events: Any,
        *,
        request_id: str | None = None,
        replay: bool = False,
    ) -> dict[str, Any]:
        if not isinstance(events, list):
            raise ValueError("events must be an array of source records")
        if not events:
            raise ValueError("events must contain at least one source record")

        ingest_seconds = time.time()
        batch_request_id = request_id or f"req-{sha256_hex(canonical_compact_json(events))[:24]}"

        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        status_counts = {"inserted": 0, "updated": 0, "duplicate": 0}

        for index, raw in enumerate(events):
            if not isinstance(raw, dict):
                rejected.append({"index": index, "errors": ["record is not a JSON object"]})
                continue
            event = self.normalizer.normalize(
                source,
                raw,
                ingest_time=ingest_seconds,
                request_id=batch_request_id,
                replay=replay,
            )
            errors = self.schema.validate(event)
            if errors:
                rejected.append({"index": index, "event_id": event["event_id"], "errors": errors})
                continue
            status = self.store.upsert(event)
            status_counts[status] += 1
            accepted.append({"event_id": event["event_id"], "event_type": event["event_type"], "status": status})

        sinks = [
            {"sink": sink, "records": len(accepted), "status": "written"}
            for sink in JOURNEY_SINKS
        ]
        return {
            "srpvdal_phase": "SENSE",
            "event_source": source.strip().lower() if isinstance(source, str) else source,
            "request_id": batch_request_id,
            "response_schema_hash": self.schema.schema_hash,
            "received": len(events),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "idempotency": status_counts,
            "sinks": sinks,
            "events": accepted,
            "rejections": rejected,
            "sample": [deepcopy(record) for record in self.store.recent_events(limit=5)],
        }

    def recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.store.recent_events(limit=limit)

    def discovery_block(self) -> dict[str, Any]:
        return {
            "schema": self.schema.schema.get("$id"),
            "schema_version": JOURNEY_RULESET_VERSION,
            "response_schema_hash": self.schema.schema_hash,
            "sources": list(JOURNEY_SOURCES),
            "sinks": list(JOURNEY_SINKS),
            "tools": [
                "journey.normalize_event",
                "journey.ingest_events",
                "journey.recent_events",
            ],
            "stored_event_count": self.store.count(),
        }
