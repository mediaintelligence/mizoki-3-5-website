"""Canonical reasoning substrate — portable, dependency-free SENSE-stage layer.

A point-in-time export of the canonical event contract built in the
`mizoki-3-5-website` Flask runtime, packaged for lifting into the production agent
runtime (boss-agent-adk / MIZOKICloudRun) as the single source of truth.

Pipeline:
    native connector payload
      -> JourneyEventNormalizer.normalize()          (v1 JourneyEvent)
      -> CanonicalEnvelopeBuilder.build_and_validate() (v2 CanonicalEventEnvelope)
      -> IdentityResolutionCell.resolve_actor()        (cross-event identity_cluster)

Everything is stdlib-only and deterministic. The optional external sinks
(`journey_sinks`) and the Gemini/Vertex extractor (`journey_gemini`) lazily import
their cloud SDKs, so importing this package pulls in no third-party dependencies.

Quick start:

    from canonical_substrate import normalizer, envelope_builder, IdentityResolutionCell

    event = normalizer().normalize("meta", payload)           # -> v1 JourneyEvent dict
    built = envelope_builder().build_and_validate(event)      # -> {"envelope", "valid", "errors"}
    cluster = IdentityResolutionCell("identity_clusters.json").resolve_actor(event["actor"])
    built["envelope"]["identity"]["identity_cluster"] = cluster["identity_cluster"]

(The Flask `JourneyIngestCell.normalize_event()` wraps normalize+validate into one
`{"event", "valid", "errors"}` call — use that shape if you prefer the cell API.)
"""

from __future__ import annotations

from pathlib import Path

from .envelope import CanonicalEnvelopeBuilder
from .identity import IdentityClusterResolver, IdentityResolutionCell
from .journey import (
    JourneyEventNormalizer,
    JourneyEventSchema,
    JourneyEventStore,
    JourneyIngestCell,
)

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
JOURNEY_SCHEMA_PATH = SCHEMA_DIR / "journey-event.json"
ENVELOPE_SCHEMA_PATH = SCHEMA_DIR / "canonical-event-envelope.json"

__all__ = [
    "CanonicalEnvelopeBuilder",
    "IdentityClusterResolver",
    "IdentityResolutionCell",
    "JourneyEventNormalizer",
    "JourneyEventSchema",
    "JourneyEventStore",
    "JourneyIngestCell",
    "JOURNEY_SCHEMA_PATH",
    "ENVELOPE_SCHEMA_PATH",
    "journey_schema",
    "normalizer",
    "envelope_builder",
]


def journey_schema() -> JourneyEventSchema:
    """v1 JourneyEvent schema validator bound to the bundled schema file."""
    return JourneyEventSchema(JOURNEY_SCHEMA_PATH)


def normalizer() -> JourneyEventNormalizer:
    """Multi-connector normalizer (meta / google_ads / sendgrid / openrtb / other)."""
    return JourneyEventNormalizer(journey_schema())


def envelope_builder() -> CanonicalEnvelopeBuilder:
    """v2 CanonicalEventEnvelope builder bound to both bundled schemas."""
    return CanonicalEnvelopeBuilder(ENVELOPE_SCHEMA_PATH, journey_schema())
