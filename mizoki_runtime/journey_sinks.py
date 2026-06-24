"""Optional external upsert sinks for canonical JourneyEvents.

The default SENSE path (``JourneyIngestCell``) stays deterministic and
dependency-free: it upserts into an in-process JSONL store. These sinks let the
*same* validated, idempotent events also be written to Firestore (doc per
``event_id``) and/or BigQuery (``MERGE`` keyed on ``event_id``) when credentials
and the optional client libraries are present.

Design notes:
- ``google-cloud-firestore`` / ``google-cloud-bigquery`` are **lazily imported**
  inside the upsert path, so importing this module — and constructing a sink —
  never requires the libraries or credentials. Nothing here is added to
  ``requirements.txt``; install the clients only where the sinks run:
  ``pip install google-cloud-firestore google-cloud-bigquery``.
- The SQL builder and event->row projection are **pure functions**, so the
  idempotent MERGE shape is unit-testable without touching the cloud.
- A sink exposes ``name`` and ``upsert(event) -> str`` ("written"); the ingest
  cell delegates to it for inserted/updated events and records per-sink results.
"""

from __future__ import annotations

import json
import os
from typing import Any


# Canonical BigQuery destination. Override via MIZOKI_JOURNEY_BIGQUERY_TABLE.
DEFAULT_BIGQUERY_TABLE = "analytics.journey_events"
DEFAULT_FIRESTORE_COLLECTION = "journey_events"


def event_to_bigquery_row(event: dict[str, Any]) -> dict[str, Any]:
    """Project a JourneyEvent onto the BigQuery column set (JSON columns as text)."""
    return {
        "event_id": event["event_id"],
        "event_time": event.get("event_time"),
        "ingest_time": event.get("ingest_time"),
        "event_source": event.get("event_source"),
        "event_type": event.get("event_type"),
        "source_payload_hash": event.get("source_payload_hash"),
        "actor": json.dumps(event.get("actor", {}), sort_keys=True),
        "context": json.dumps(event.get("context", {}), sort_keys=True),
        "provenance": json.dumps(event.get("provenance", {}), sort_keys=True),
    }


def build_merge_sql(table: str) -> str:
    """Idempotent upsert: MERGE on event_id (insert-or-update the whole row)."""
    return f"""
MERGE `{table}` T
USING (
  SELECT
    @event_id AS event_id,
    @event_time AS event_time,
    @ingest_time AS ingest_time,
    @event_source AS event_source,
    @event_type AS event_type,
    @source_payload_hash AS source_payload_hash,
    @actor AS actor,
    @context AS context,
    @provenance AS provenance
) S
ON T.event_id = S.event_id
WHEN MATCHED THEN UPDATE SET
  event_time = S.event_time,
  ingest_time = S.ingest_time,
  event_source = S.event_source,
  event_type = S.event_type,
  source_payload_hash = S.source_payload_hash,
  actor = S.actor,
  context = S.context,
  provenance = S.provenance
WHEN NOT MATCHED THEN INSERT
  (event_id, event_time, ingest_time, event_source, event_type, source_payload_hash, actor, context, provenance)
  VALUES
  (S.event_id, S.event_time, S.ingest_time, S.event_source, S.event_type, S.source_payload_hash, S.actor, S.context, S.provenance)
""".strip()


class FirestoreJourneySink:
    """Upsert each JourneyEvent as a Firestore document keyed on ``event_id``."""

    def __init__(self, collection: str = DEFAULT_FIRESTORE_COLLECTION, client: Any = None) -> None:
        self.collection = collection
        self._client = client
        self.name = f"firestore:{collection}"

    def _resolve_client(self) -> Any:
        if self._client is None:
            from google.cloud import firestore  # lazy: optional dependency

            self._client = firestore.Client()
        return self._client

    def upsert(self, event: dict[str, Any]) -> str:
        client = self._resolve_client()
        client.collection(self.collection).document(event["event_id"]).set(event, merge=True)
        return "written"


class BigQueryJourneySink:
    """Upsert each JourneyEvent into BigQuery via an idempotent MERGE on ``event_id``."""

    def __init__(self, table: str = DEFAULT_BIGQUERY_TABLE, client: Any = None) -> None:
        self.table = table
        self._client = client
        self.name = f"bigquery:{table}"

    def _resolve_client(self) -> Any:
        if self._client is None:
            from google.cloud import bigquery  # lazy: optional dependency

            self._client = bigquery.Client()
        return self._client

    def upsert(self, event: dict[str, Any]) -> str:
        from google.cloud import bigquery  # lazy: optional dependency

        client = self._resolve_client()
        row = event_to_bigquery_row(event)
        parameters = [
            bigquery.ScalarQueryParameter("event_id", "STRING", row["event_id"]),
            bigquery.ScalarQueryParameter("event_time", "TIMESTAMP", row["event_time"]),
            bigquery.ScalarQueryParameter("ingest_time", "TIMESTAMP", row["ingest_time"]),
            bigquery.ScalarQueryParameter("event_source", "STRING", row["event_source"]),
            bigquery.ScalarQueryParameter("event_type", "STRING", row["event_type"]),
            bigquery.ScalarQueryParameter("source_payload_hash", "STRING", row["source_payload_hash"]),
            bigquery.ScalarQueryParameter("actor", "JSON", row["actor"]),
            bigquery.ScalarQueryParameter("context", "JSON", row["context"]),
            bigquery.ScalarQueryParameter("provenance", "JSON", row["provenance"]),
        ]
        job = client.query(
            build_merge_sql(self.table),
            job_config=bigquery.QueryJobConfig(query_parameters=parameters),
        )
        job.result()
        return "written"


def build_journey_sinks_from_env(env: dict[str, str] | None = None) -> list[Any]:
    """Build external sinks from env vars; returns [] (no-op) unless configured.

    - ``MIZOKI_JOURNEY_FIRESTORE_COLLECTION`` -> Firestore sink for that collection
    - ``MIZOKI_JOURNEY_BIGQUERY_TABLE``       -> BigQuery sink for that table
    """
    source = os.environ if env is None else env
    sinks: list[Any] = []
    collection = (source.get("MIZOKI_JOURNEY_FIRESTORE_COLLECTION") or "").strip()
    if collection:
        sinks.append(FirestoreJourneySink(collection=collection))
    table = (source.get("MIZOKI_JOURNEY_BIGQUERY_TABLE") or "").strip()
    if table:
        sinks.append(BigQueryJourneySink(table=table))
    return sinks
