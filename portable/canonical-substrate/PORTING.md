# Porting the Canonical Reasoning Substrate into MIZOKICloudRun (boss-agent-adk)

This bundle is a **point-in-time export** of the canonical event contract that
currently lives in the `mizoki-3-5-website` Flask runtime (`mizoki_runtime/`). It is
packaged so it can be lifted into the production agent runtime
(`boss-agent-adk` / MIZOKICloudRun) and become the **single source of truth** for the
SENSE-stage contract, ending the website-vs-runtime duplication.

> After the port, the website should `import` this package (or consume the served
> schema JSON) rather than keep its own copy. Two homes for one contract will drift.

## What's in the bundle

```
canonical_substrate/
├── __init__.py            # factories: journey_schema(), normalizer(), envelope_builder()
├── journey.py             # v1 JourneyEvent: connector mappers, dependency-free JSON-Schema
│                          #   validator, normalizer, idempotent JSONL store, SENSE ingest cell
├── envelope.py            # v2 CanonicalEventEnvelope builder (21 reasoning layers)
├── identity.py            # cross-event identity-cluster resolver (persistent union-find)
├── journey_sinks.py       # OPTIONAL Firestore / BigQuery upsert sinks (lazy cloud imports)
├── journey_gemini.py      # OPTIONAL Gemini/Vertex strict-schema LLM extractor (lazy imports)
└── schemas/
    ├── journey-event.json              # v1 schema (draft 2020-12)
    ├── canonical-event-envelope.json   # v2 schema (schema_version 2.0.0)
    └── journey-event.bigquery.sql      # BQ table DDL for the optional sink
tests/test_substrate.py    # standalone proof (no Flask, no BossRuntime)
```

**Dependencies:** the core (`journey` / `envelope` / `identity`) is **stdlib-only**.
The optional sinks and the LLM extractor lazily import their cloud SDKs *inside* the
call path, so importing the package never pulls a third-party dependency. See
`requirements-optional.txt` — install only if you enable those paths.

## Verify the bundle standalone

```bash
cd portable/canonical-substrate
python3 -m unittest tests.test_substrate      # 3 tests, OK
```

## The pipeline (what to wire at SENSE)

```
native connector payload (Meta / Google Ads / SendGrid / OpenRTB / Gemini-extracted)
  → JourneyEventNormalizer.normalize(source, payload)      # v1 JourneyEvent (deterministic, idempotent event_id)
  → CanonicalEnvelopeBuilder.build_and_validate(event)     # v2 envelope: classification, kg_refs,
  →                                                        #   relationships, time/sec/dq/observability, SRPVDAL state
  → IdentityResolutionCell.resolve_actor(event["actor"])   # identity_cluster (strong-key stitching; ip excluded)
```

### Minimal wire-in (boss-agent-adk SENSE handler)

```python
from canonical_substrate import normalizer, envelope_builder, IdentityResolutionCell

_NORMALIZER = normalizer()
_ENVELOPES  = envelope_builder()
_IDENTITY   = IdentityResolutionCell("/var/lib/mizoki/identity_clusters.json")  # use durable storage

def sense_ingest(source: str, payload: dict) -> dict:
    event = _NORMALIZER.normalize(source, payload)           # raises ValueError on bad source/payload
    built = _ENVELOPES.build_and_validate(event)             # {"envelope", "valid", "errors"}
    resolution = _IDENTITY.resolve_actor(event["actor"])
    built["envelope"]["identity"]["identity_cluster"] = resolution["identity_cluster"]
    # hand built["envelope"] to REASON; the loop-filled layers
    # (evaluation/actions/learning/causal/intelligence) are typed empty scaffolds for downstream cells.
    return built
```

If the runtime already has a tool registry / MCP surface, register the same handlers
the website exposes: `journey.normalize_event`, `journey.build_envelope`,
`identity.resolve`, `identity.cluster_stats` (see `mizoki_runtime/runtime.py` in the
website repo for the exact `ToolDefinition` wiring to mirror).

## Idempotency & state caveats (read before production)

- `event_id = sha256(event_source || event_type || stable_source_keys)` — never over
  volatile timestamps. Re-ingesting the same payload is a no-op (`duplicate`).
- The default `JourneyEventStore` (JSONL) and `IdentityClusterResolver` (JSON snapshot)
  persist to **local disk**, so idempotency / clusters hold **per instance**. On
  Cloud Run (autoscaled, ephemeral disk) back them with shared storage:
  - Journey events: set `MIZOKI_JOURNEY_FIRESTORE_COLLECTION` and/or
    `MIZOKI_JOURNEY_BIGQUERY_TABLE` and install the matching client (sinks degrade
    gracefully if absent).
  - Identity clusters: the resolver's `parent`/`size` maps are the entire state —
    swap the JSON snapshot for a shared KV / Firestore doc if cross-instance
    cluster stability is required. The **cluster id is content-derived**
    (`Cluster:sha256(anchor_root)`), so it is stable across instances *for the same
    accreted identifier set* even without shared state; only the live `stats()`
    counts and merge-detection need shared state.

## Version vector (envelope provenance)

`envelope.py` stamps a version vector, env-overridable:
`MIZOKI_POLICY_VERSION` / `MIZOKI_GOVERNANCE_VERSION` / `MIZOKI_ONTOLOGY_VERSION` /
`MIZOKI_REASONING_VERSION` (default `1.0.0`). Set these per deployment so a decision
is reproducible against the exact policy/ontology/reasoning generation.

## Optional LLM extractor (Gemini / Vertex)

`journey_gemini.py` provides a Vertex (ADC, no API key — default `gemini-3.5-pro`) and
an API-key REST backend. Both thread model provenance through the normalizer so an
LLM-extracted row is audit-identical to a rule-based one. Dormant until configured
(`MIZOKI_GEMINI_PROJECT` for Vertex, or `GEMINI_API_KEY` for the REST path). Grant the
runtime SA `roles/aiplatform.user` for the Vertex path.

## Served schemas (live, for `$ref` targets)

The website serves both schemas (kept in sync with this bundle until the port lands):
- `https://mizoki3.com/schemas/journey-event.json`
- `https://mizoki3.com/schemas/canonical-event-envelope.json`
