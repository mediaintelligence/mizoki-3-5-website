-- Canonical JourneyEvent landing table for BigQuery.
-- Mirrors schemas/journey-event.json. actor/context/provenance are stored as
-- JSON so the nested, evolving sub-shapes (context.ext, provenance) round-trip
-- without a schema migration. Idempotency is enforced by the MERGE in
-- mizoki_runtime/journey_sinks.py (BigQueryJourneySink), keyed on event_id.

CREATE TABLE IF NOT EXISTS `analytics.journey_events` (
  event_id            STRING NOT NULL,
  event_time          TIMESTAMP,
  ingest_time         TIMESTAMP,
  event_source        STRING,
  event_type          STRING,
  source_payload_hash STRING,
  actor               JSON,
  context             JSON,
  provenance          JSON
)
PARTITION BY DATE(event_time)
CLUSTER BY event_source, event_type, event_id;
