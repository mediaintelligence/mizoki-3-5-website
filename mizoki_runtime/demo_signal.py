"""Signal Factory demo engine.

Fully deterministic, stdlib-only simulation of the MIZ OKI Signal division:
raw marketing signals are "manufactured" into governed autonomous decisions
through the 7-stage SRPVDAL pipeline (Sense -> Reason -> Plan -> Validate ->
Decide -> Act -> Learn) with a visible ReLU gate and guardrails.

Design rules (see docs/DEMO_BUILD_PROMPT.md):
- All randomness flows through ``random.Random(seed)`` — same seed, same run.
- Timestamps are synthetic and derived from a fixed base clock, so two runs
  with the same seed are byte-identical.
- No external calls, no new dependencies.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

__all__ = [
    "SCENARIOS",
    "DEFAULT_SEED",
    "GATE_UPLIFT_FLOOR",
    "GATE_CONFIDENCE_FLOOR",
    "GATE_SAMPLE_FLOOR",
    "SyntheticEventGenerator",
    "normalize",
    "ReLUGate",
    "GuardrailSet",
    "SignalFactoryPipeline",
    "build_causal_truth",
    "list_scenarios",
]

DEFAULT_SEED = 42
DEFAULT_EVENT_COUNT = 18

# Fixed synthetic clock — keeps runs reproducible for deep-equality tests.
_BASE_TIME = datetime(2026, 1, 5, 9, 0, 0, tzinfo=timezone.utc)


def _iso(offset_seconds: float) -> str:
    moment = _BASE_TIME + timedelta(seconds=offset_seconds)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# 1.1 Scenarios
# --------------------------------------------------------------------------
# Each entity profile drives both event synthesis and the aggregated signal:
#   (entity_id, metric, uplift, confidence, sample_size, weak, note)
# Profiles are engineered so each scenario shows the gate filtering for every
# failure reason, and the plan stage contains exactly one guardrail block.

SCENARIOS: dict[str, dict[str, Any]] = {
    "ecommerce_roas": {
        "id": "ecommerce_roas",
        "name": "E-commerce ROAS optimization",
        "description": (
            "Google Ads clicks and conversions, GA4 page and cart events, and "
            "Meta impressions are fused into per-campaign ROAS signals; the "
            "strongest audiences win incremental budget."
        ),
        "metric": "roas_delta",
        "sources": ("google_ads", "ga4", "meta"),
        "event_types": {
            "google_ads": ("click", "conversion"),
            "ga4": ("page_view", "add_to_cart"),
            "meta": ("impression",),
        },
        "profiles": (
            {"entity_id": "campaign_7", "uplift": 0.22, "confidence": 0.86, "sample_size": 48, "weak": False},
            {"entity_id": "audience_hv", "uplift": 0.14, "confidence": 0.78, "sample_size": 30, "weak": False},
            {"entity_id": "campaign_3", "uplift": 0.03, "confidence": 0.81, "sample_size": 40, "weak": False},
            {"entity_id": "campaign_9", "uplift": 0.09, "confidence": 0.55, "sample_size": 25, "weak": True},
            {"entity_id": "audience_cold", "uplift": 0.12, "confidence": 0.74, "sample_size": 8, "weak": True},
        ),
        "hypothesis_template": "{entity} is outperforming account ROAS by {uplift_pct}%",
        # (action_type, entity, magnitude_pct, expected_value, confidence, supporting_conversions)
        "planned_actions": (
            ("budget_increase", "campaign_7", 12.0, 8400.0, 0.86, 48),
            ("bid_adjust", "campaign_7", 8.0, 3100.0, 0.82, 48),
            # Deliberate guardrail block: +25% budget swing exceeds the 20% cap.
            ("budget_increase", "audience_hv", 25.0, 6200.0, 0.78, 30),
        ),
        "learning_note": (
            "Concentrating spend on campaign_7 compounded ROAS instead of "
            "diluting learning across weak segments — the ReLU gate held the floor."
        ),
    },
    "leadgen_cpa": {
        "id": "leadgen_cpa",
        "name": "Lead-gen CPA reduction",
        "description": (
            "Search clicks, landing-page form submits, and CRM lead-quality "
            "events combine into CPA-delta signals; bids move only where lead "
            "quality holds up."
        ),
        "metric": "cpa_delta",
        "sources": ("google_ads", "ga4", "crm"),
        "event_types": {
            "google_ads": ("click",),
            "ga4": ("form_submit",),
            "crm": ("lead_scored", "lead_qualified"),
        },
        "profiles": (
            {"entity_id": "form_fastlane", "uplift": 0.18, "confidence": 0.84, "sample_size": 36, "weak": False},
            {"entity_id": "kw_brand", "uplift": 0.11, "confidence": 0.77, "sample_size": 22, "weak": False},
            {"entity_id": "kw_generic", "uplift": 0.02, "confidence": 0.72, "sample_size": 31, "weak": True},
            {"entity_id": "lead_seg_b", "uplift": 0.08, "confidence": 0.61, "sample_size": 19, "weak": False},
            {"entity_id": "lp_variant_c", "uplift": 0.21, "confidence": 0.80, "sample_size": 9, "weak": True},
        ),
        "hypothesis_template": "{entity} is beating target CPA by {uplift_pct}%",
        "planned_actions": (
            ("bid_adjust", "kw_brand", -12.0, 4700.0, 0.77, 22),
            ("budget_increase", "form_fastlane", 10.0, 5900.0, 0.84, 36),
            # Deliberate guardrail block: -35% bid swing exceeds the 30% cap.
            ("bid_adjust", "form_fastlane", -35.0, 5200.0, 0.80, 36),
        ),
        "learning_note": (
            "CPA improved fastest where CRM lead-quality confirmed the click "
            "signal; bid moves stayed inside the 30% governance envelope."
        ),
    },
    "email_reengagement": {
        "id": "email_reengagement",
        "name": "Email re-engagement",
        "description": (
            "Opens (with Apple MPP proxy-opens flagged), clicks, and "
            "unsubscribes are separated into trustworthy engagement signals; "
            "proxy-inflated segments are filtered before any send decision."
        ),
        "metric": "engagement_delta",
        "sources": ("email",),
        "event_types": {
            "email": ("open", "click", "unsubscribe"),
        },
        "profiles": (
            {"entity_id": "seg_winback_30", "uplift": 0.16, "confidence": 0.80, "sample_size": 26, "weak": False},
            {"entity_id": "seg_lapsed_90", "uplift": 0.07, "confidence": 0.73, "sample_size": 18, "weak": False},
            {"entity_id": "seg_mpp_proxy", "uplift": 0.19, "confidence": 0.48, "sample_size": 33, "weak": True},
            {"entity_id": "seg_new", "uplift": 0.04, "confidence": 0.75, "sample_size": 21, "weak": False},
            {"entity_id": "seg_dormant_365", "uplift": 0.10, "confidence": 0.76, "sample_size": 6, "weak": True},
        ),
        "hypothesis_template": "{entity} is re-engaging {uplift_pct}% above list baseline",
        "planned_actions": (
            ("creative_rotate", "seg_winback_30", 100.0, 2600.0, 0.80, 26),
            ("budget_increase", "seg_winback_30", 9.0, 1900.0, 0.78, 26),
            # Deliberate guardrail block: suppression cohort has only 12
            # confirmed conversions — below the 15-conversion sample floor.
            ("suppress_segment", "seg_lapsed_90", 100.0, 1400.0, 0.73, 12),
        ),
        "learning_note": (
            "Proxy-open inflation was quarantined at the gate; verified-click "
            "segments carried the re-engagement lift."
        ),
    },
}


def list_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "id": scenario["id"],
            "name": scenario["name"],
            "description": scenario["description"],
            "metric": scenario["metric"],
            "sources": list(scenario["sources"]),
        }
        for scenario in SCENARIOS.values()
    ]


# --------------------------------------------------------------------------
# Dataclasses
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RawEvent:
    event_id: str
    source: str
    event_type: str
    entity_id: str
    value: float
    timestamp: str
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanonicalEvent:
    canonical_id: str
    entities: list[str]
    relationships: list[dict[str, str]]
    confidence: float
    security_scope: dict[str, str]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Signal:
    entity_id: str
    metric: str
    uplift: float
    confidence: float
    sample_size: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------
# 1.2 SyntheticEventGenerator
# --------------------------------------------------------------------------

class SyntheticEventGenerator:
    """Deterministic raw-event synthesis for a scenario."""

    def generate(
        self,
        scenario_id: str,
        count: int = DEFAULT_EVENT_COUNT,
        seed: int = DEFAULT_SEED,
    ) -> list[RawEvent]:
        scenario = _require_scenario(scenario_id)
        rng = random.Random(seed)
        profiles = scenario["profiles"]
        sources = scenario["sources"]
        events: list[RawEvent] = []
        for index in range(count):
            profile = profiles[index % len(profiles)]
            source = sources[index % len(sources)]
            event_type = rng.choice(scenario["event_types"][source])
            weak = bool(profile["weak"])
            if weak:
                value = round(rng.uniform(0.5, 6.0), 2)
            else:
                value = round(rng.uniform(18.0, 240.0), 2)
            payload = self._payload(scenario_id, source, event_type, rng, weak)
            events.append(
                RawEvent(
                    event_id=f"evt_{index + 1:03d}",
                    source=source,
                    event_type=event_type,
                    entity_id=profile["entity_id"],
                    value=value,
                    timestamp=_iso(index * 7),
                    raw_payload=payload,
                )
            )
        return events

    @staticmethod
    def _payload(
        scenario_id: str,
        source: str,
        event_type: str,
        rng: random.Random,
        weak: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"n": rng.randint(1, 4) if weak else rng.randint(3, 9)}
        if source == "google_ads":
            payload.update({"network": "search", "match_type": rng.choice(["exact", "phrase"])})
        elif source == "ga4":
            payload.update({"session_engaged": rng.random() > 0.2, "device": rng.choice(["mobile", "desktop"])})
        elif source == "meta":
            payload.update({"placement": rng.choice(["feed", "reels"]), "frequency": round(rng.uniform(1.0, 3.4), 1)})
        elif source == "crm":
            payload.update({"lead_grade": rng.choice(["A", "B", "C"]), "sql_ready": rng.random() > 0.5})
        elif source == "email":
            # ~30% of email-scenario opens are Apple MPP proxy opens.
            proxy = event_type == "open" and rng.random() < 0.45
            payload.update({"mpp_proxy": proxy, "client": "apple_mail" if proxy else rng.choice(["gmail", "outlook"])})
        if scenario_id == "email_reengagement" and payload.get("mpp_proxy"):
            payload["proxy_note"] = "Apple MPP prefetch — not a human open"
        return payload


# --------------------------------------------------------------------------
# 1.3 Canonical normalization
# --------------------------------------------------------------------------

_SOURCE_CONFIDENCE = {
    "google_ads": 0.90,
    "crm": 0.88,
    "ga4": 0.84,
    "meta": 0.80,
    "email": 0.76,
}

_TYPE_CONFIDENCE_DELTA = {
    "conversion": 0.05,
    "lead_qualified": 0.05,
    "add_to_cart": 0.02,
    "form_submit": 0.03,
    "lead_scored": 0.02,
    "click": 0.0,
    "page_view": -0.02,
    "impression": -0.08,
    "open": -0.06,
    "unsubscribe": 0.0,
}


def normalize(raw_event: RawEvent | dict[str, Any]) -> CanonicalEvent:
    """Every raw event becomes a CanonicalEvent before SRPVDAL.

    Nothing goes straight from connector to action.
    """
    raw = raw_event.to_dict() if isinstance(raw_event, RawEvent) else dict(raw_event)
    confidence = _SOURCE_CONFIDENCE.get(raw["source"], 0.7)
    confidence += _TYPE_CONFIDENCE_DELTA.get(raw["event_type"], 0.0)
    if raw.get("raw_payload", {}).get("mpp_proxy"):
        confidence -= 0.30
    confidence = round(max(0.05, min(confidence, 0.99)), 2)
    return CanonicalEvent(
        canonical_id=f"can_{raw['event_id']}",
        entities=[raw["entity_id"], "tenant:demo"],
        relationships=[
            {"from": raw["event_id"], "type": "NORMALIZED_TO", "to": f"can_{raw['event_id']}"},
            {"from": f"can_{raw['event_id']}", "type": "OBSERVED_FOR", "to": raw["entity_id"]},
        ],
        confidence=confidence,
        security_scope={"tenant": "demo"},
        provenance={
            "source": raw["source"],
            "connector": f"{raw['source']}_connector",
            "received_at": raw["timestamp"],
            "transform": "demo_normalizer_v1",
        },
    )


# --------------------------------------------------------------------------
# 1.4 Signal aggregation + ReLU gate
# --------------------------------------------------------------------------

GATE_UPLIFT_FLOOR = 0.05
GATE_CONFIDENCE_FLOOR = 0.70
GATE_SAMPLE_FLOOR = 15

REASON_UPLIFT = "uplift below 5% floor"
REASON_CONFIDENCE = "confidence below 0.70"
REASON_SAMPLE = "sample too small (n=%d < 15)"


def aggregate_signals(scenario_id: str) -> list[Signal]:
    """Aggregate the scenario's canonical events into per-entity signals.

    The per-entity uplift/confidence/sample values are the scenario's
    calibrated profile numbers — deterministic by construction.
    """
    scenario = _require_scenario(scenario_id)
    return [
        Signal(
            entity_id=profile["entity_id"],
            metric=scenario["metric"],
            uplift=profile["uplift"],
            confidence=profile["confidence"],
            sample_size=profile["sample_size"],
        )
        for profile in scenario["profiles"]
    ]


class ReLUGate:
    """max(0, uplift) gating with confidence and sample floors."""

    @staticmethod
    def score(signal: Signal | dict[str, Any]) -> float:
        data = signal.to_dict() if isinstance(signal, Signal) else dict(signal)
        return round(
            max(0.0, float(data["uplift"]))
            * float(data["confidence"])
            * math.log(1 + int(data["sample_size"])),
            6,
        )

    @classmethod
    def evaluate(cls, signal: Signal | dict[str, Any]) -> dict[str, Any]:
        data = signal.to_dict() if isinstance(signal, Signal) else dict(signal)
        reasons: list[str] = []
        if float(data["uplift"]) < GATE_UPLIFT_FLOOR:
            reasons.append(REASON_UPLIFT)
        if float(data["confidence"]) < GATE_CONFIDENCE_FLOOR:
            reasons.append(REASON_CONFIDENCE)
        if int(data["sample_size"]) < GATE_SAMPLE_FLOOR:
            reasons.append(REASON_SAMPLE % int(data["sample_size"]))
        return {
            "entity_id": data["entity_id"],
            "score": cls.score(data),
            "passed": not reasons,
            "reasons": reasons,
            "reason": "; ".join(reasons),
        }


# --------------------------------------------------------------------------
# 1.5 GuardrailSet (Validate stage)
# --------------------------------------------------------------------------

class GuardrailSet:
    BUDGET_SWING_CAP_PCT = 20.0
    BID_SWING_CAP_PCT = 30.0
    CONFIDENCE_FLOOR = 0.70
    SAMPLE_FLOOR = 15

    @classmethod
    def evaluate(cls, action: dict[str, Any]) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        magnitude = abs(float(action.get("magnitude_pct", 0.0)))
        action_type = action.get("type", "")
        confidence = float(action.get("confidence", 0.0))
        supporting = int(action.get("supporting_conversions", 0))

        budget_action = action_type in ("budget_increase", "budget_decrease")
        budget_ok = (not budget_action) or magnitude <= cls.BUDGET_SWING_CAP_PCT
        checks.append({
            "rule_id": "budget_swing_cap",
            "name": "Budget swing cap (±20%)",
            "passed": budget_ok,
            "detail": (
                f"Proposed budget change {magnitude:.0f}% exceeds the 20% cap."
                if not budget_ok
                else (f"Budget change {magnitude:.0f}% within the 20% cap." if budget_action else "Not a budget action.")
            ),
        })

        bid_action = action_type == "bid_adjust"
        bid_ok = (not bid_action) or magnitude <= cls.BID_SWING_CAP_PCT
        checks.append({
            "rule_id": "bid_swing_cap",
            "name": "Bid swing cap (±30%)",
            "passed": bid_ok,
            "detail": (
                f"Proposed bid change {magnitude:.0f}% exceeds the 30% cap."
                if not bid_ok
                else (f"Bid change {magnitude:.0f}% within the 30% cap." if bid_action else "Not a bid action.")
            ),
        })

        confidence_ok = confidence >= cls.CONFIDENCE_FLOOR
        checks.append({
            "rule_id": "confidence_floor",
            "name": "Decision confidence ≥ 0.70",
            "passed": confidence_ok,
            "detail": (
                f"Decision confidence {confidence:.2f} meets the 0.70 floor."
                if confidence_ok
                else f"Decision confidence {confidence:.2f} is below the 0.70 floor."
            ),
        })

        sample_ok = supporting >= cls.SAMPLE_FLOOR
        checks.append({
            "rule_id": "sample_floor",
            "name": "Supporting conversions ≥ 15",
            "passed": sample_ok,
            "detail": (
                f"{supporting} supporting conversions meet the 15-conversion floor."
                if sample_ok
                else f"Only {supporting} supporting conversions — below the 15-conversion floor."
            ),
        })

        checks.append({
            "rule_id": "rollback_ready",
            "name": "Rollback token minted",
            "passed": True,
            "detail": f"Rollback token {action.get('rollback_token', '')} minted before execution.",
        })
        return checks


# --------------------------------------------------------------------------
# 1.6 SignalFactoryPipeline
# --------------------------------------------------------------------------

class SignalFactoryPipeline:
    STAGES = ("sense", "reason", "plan", "validate", "decide", "act", "learn")

    def __init__(self) -> None:
        self.generator = SyntheticEventGenerator()
        self.gate = ReLUGate()
        self.guardrails = GuardrailSet()

    # -- public API --------------------------------------------------------

    def run(self, scenario_id: str, seed: int = DEFAULT_SEED) -> dict[str, Any]:
        return self._execute(scenario_id, seed)["pipeline_run"]

    def run_streaming(self, scenario_id: str, seed: int = DEFAULT_SEED) -> Iterator[dict[str, Any]]:
        """Yield SSE-ready frames. Pacing is the caller's job (delay_hint_ms)."""
        bundle = self._execute(scenario_id, seed)
        run = bundle["pipeline_run"]
        for raw in bundle["raw_events"]:
            yield {"type": "raw_event", "data": raw, "delay_hint_ms": 120}
        for canonical in bundle["canonical_events"]:
            yield {"type": "canonical_event", "data": canonical, "delay_hint_ms": 100}
        for verdict in bundle["gate_verdicts"]:
            yield {"type": "signal_gate", "data": verdict, "delay_hint_ms": 350}
        for stage in run["stages"]:
            yield {"type": "stage", "data": stage, "delay_hint_ms": 600}
        yield {"type": "decision_card", "data": run["decision_card"], "delay_hint_ms": 800}
        yield {
            "type": "done",
            "data": {"trace_id": run["trace_id"], "scenario": scenario_id, "seed": seed},
            "delay_hint_ms": 0,
        }

    # -- internals ----------------------------------------------------------

    def _execute(self, scenario_id: str, seed: int) -> dict[str, Any]:
        scenario = _require_scenario(scenario_id)
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")
        trace_id = "sig-" + hashlib.sha256(f"{scenario_id}:{seed}".encode()).hexdigest()[:12]

        raw_events = [event.to_dict() for event in self.generator.generate(scenario_id, seed=seed)]
        canonical_events = [normalize(event).to_dict() for event in raw_events]

        signals = [signal.to_dict() for signal in aggregate_signals(scenario_id)]
        gate_verdicts = []
        for signal in signals:
            verdict = self.gate.evaluate(signal)
            verdict["signal"] = signal
            gate_verdicts.append(verdict)
        passing = [verdict for verdict in gate_verdicts if verdict["passed"]]

        hypotheses = [
            {
                "entity_id": verdict["entity_id"],
                "hypothesis": scenario["hypothesis_template"].format(
                    entity=verdict["entity_id"],
                    uplift_pct=round(verdict["signal"]["uplift"] * 100),
                ),
                "confidence": verdict["signal"]["confidence"],
                "gate_score": verdict["score"],
            }
            for verdict in passing
        ]

        actions = []
        for index, spec in enumerate(scenario["planned_actions"], start=1):
            action_type, entity_id, magnitude_pct, expected_value, confidence, supporting = spec
            action_id = f"act_{scenario_id}_{index}"
            actions.append({
                "action_id": action_id,
                "type": action_type,
                "entity_id": entity_id,
                "magnitude_pct": magnitude_pct,
                "expected_value": expected_value,
                "confidence": confidence,
                "supporting_conversions": supporting,
                "rollback_token": _rollback_token(trace_id, action_id),
            })

        validations = []
        for action in actions:
            checks = self.guardrails.evaluate(action)
            blocked = any(not check["passed"] for check in checks)
            validations.append({
                "action_id": action["action_id"],
                "entity_id": action["entity_id"],
                "type": action["type"],
                "checks": checks,
                "blocked": blocked,
                "blocked_by": [check["rule_id"] for check in checks if not check["passed"]],
            })

        blocked_ids = {item["action_id"] for item in validations if item["blocked"]}
        surviving = [action for action in actions if action["action_id"] not in blocked_ids]
        ranked = sorted(
            (
                {
                    **action,
                    "decision_score": round(action["expected_value"] * action["confidence"], 2),
                }
                for action in surviving
            ),
            key=lambda item: item["decision_score"],
            reverse=True,
        )
        for rank, action in enumerate(ranked, start=1):
            action["rank"] = rank

        executions = [
            {
                "action_id": action["action_id"],
                "entity_id": action["entity_id"],
                "type": action["type"],
                "mode": "dry_run",
                "rollback_token": action["rollback_token"],
                "status": "executed",
            }
            for action in ranked
        ]

        learn_rng = random.Random(seed + 7)
        learnings = []
        for action in ranked:
            factor = round(learn_rng.uniform(0.90, 1.10), 3)
            predicted = action["expected_value"]
            actual = round(predicted * factor, 2)
            learnings.append({
                "action_id": action["action_id"],
                "predicted_delta": predicted,
                "simulated_actual_delta": actual,
                "error_pct": round((actual - predicted) / predicted * 100, 2),
            })

        funnel = {
            "events_sensed": len(raw_events),
            "signals_formed": len(signals),
            "passed_gate": len(passing),
            "validated": len(surviving),
            "executed": len(executions),
        }

        top_action = ranked[0] if ranked else None
        top_verdict = next(
            (verdict for verdict in passing if top_action and verdict["entity_id"] == top_action["entity_id"]),
            passing[0] if passing else None,
        )
        provenance_chain = []
        if top_action and top_verdict:
            entity_raw = [event for event in raw_events if event["entity_id"] == top_action["entity_id"]]
            provenance_chain = [
                {"stage": "raw", "ref": ", ".join(event["event_id"] for event in entity_raw[:4]),
                 "detail": f"{len(entity_raw)} raw events sensed for {top_action['entity_id']}."},
                {"stage": "canonical", "ref": ", ".join("can_" + event["event_id"] for event in entity_raw[:4]),
                 "detail": "Normalized by demo_normalizer_v1 with tenant-scoped provenance."},
                {"stage": "signal", "ref": f"{top_verdict['signal']['metric']}:{top_action['entity_id']}",
                 "detail": (
                     f"uplift {top_verdict['signal']['uplift']:+.2f}, confidence "
                     f"{top_verdict['signal']['confidence']:.2f}, n={top_verdict['signal']['sample_size']}"
                 )},
                {"stage": "gate", "ref": f"relu:{top_verdict['score']}",
                 "detail": "Passed the ReLU gate: uplift, confidence, and sample floors all met."},
                {"stage": "guardrails", "ref": top_action["action_id"],
                 "detail": "All 5 guardrails passed; rollback token minted."},
                {"stage": "decision", "ref": top_action["action_id"],
                 "detail": (
                     f"Ranked #1 by expected_value × confidence = {top_action['decision_score']}."
                 )},
            ]

        decision_card = {
            "trace_id": trace_id,
            "scenario": scenario_id,
            "executed_action": top_action,
            "provenance_chain": provenance_chain,
            "funnel": funnel,
            "guardrail_block": next(iter(
                {
                    "action_id": item["action_id"],
                    "entity_id": item["entity_id"],
                    "type": item["type"],
                    "blocked_by": item["blocked_by"],
                }
                for item in validations if item["blocked"]
            ), None),
            "causal_truth": build_causal_truth(top_action, top_verdict, validations, actions),
        }

        stages = [
            _stage_trace("sense", 0,
                         f"Sensed {len(raw_events)} raw events across "
                         f"{len(scenario['sources'])} connectors; normalized all of them into canonical events.",
                         [{"raw": raw, "canonical": canonical}
                          for raw, canonical in zip(raw_events, canonical_events)],
                         {"raw_events": len(raw_events), "canonical_events": len(canonical_events)}),
            _stage_trace("reason", 1,
                         f"Formed {len(signals)} entity signals; {len(passing)} passed the ReLU gate, "
                         f"{len(signals) - len(passing)} were filtered with visible reasons.",
                         gate_verdicts + [{"hypothesis": item} for item in hypotheses],
                         {"signals_formed": len(signals), "passed_gate": len(passing),
                          "filtered": len(signals) - len(passing)}),
            _stage_trace("plan", 2,
                         f"Proposed {len(actions)} actions from surviving hypotheses.",
                         actions,
                         {"proposed_actions": len(actions)}),
            _stage_trace("validate", 3,
                         f"Ran {len(actions) * 5} guardrail checks; blocked "
                         f"{len(blocked_ids)} action(s) before execution.",
                         validations,
                         {"actions_checked": len(actions), "blocked": len(blocked_ids)}),
            _stage_trace("decide", 4,
                         f"Ranked {len(ranked)} surviving actions by expected_value × confidence.",
                         ranked,
                         {"decided": len(ranked)}),
            _stage_trace("act", 5,
                         f"Executed {len(executions)} action(s) in dry-run mode with rollback tokens.",
                         executions,
                         {"executed": len(executions)}),
            _stage_trace("learn", 6,
                         "Compared predicted vs simulated-actual deltas and wrote one learning back to the graph.",
                         learnings + [{"learning_note": scenario["learning_note"]}],
                         {"learnings": len(learnings)}),
        ]

        pipeline_run = {
            "trace_id": trace_id,
            "scenario": scenario_id,
            "scenario_name": scenario["name"],
            "seed": seed,
            "stages": stages,
            "decision_card": decision_card,
            "funnel": funnel,
        }
        return {
            "pipeline_run": pipeline_run,
            "raw_events": raw_events,
            "canonical_events": canonical_events,
            "gate_verdicts": gate_verdicts,
        }


def build_causal_truth(
    top_action: dict[str, Any] | None,
    top_verdict: dict[str, Any] | None,
    validations: list[dict[str, Any]],
    actions: list[dict[str, Any]] | None = None,
    constraint_noun: str = "a declared constraint",
) -> str:
    """Plain-English "why" for the decision card, composed only from run data.

    Sentence one explains why the winner earned execution (the gate numbers and
    the ranking arithmetic). Sentence two quotes the failing guardrail check's
    own detail for the vetoed move — the veto is arithmetic, not opinion. No
    figure appears here that is not already in the trace.
    """
    parts: list[str] = []
    if top_action and top_verdict:
        signal = top_verdict["signal"]
        magnitude = top_action.get("magnitude_pct")
        magnitude_txt = "" if magnitude is None else f" {magnitude:+.0f}%"
        parts.append(
            f"{top_action['entity_id']} earned execution, not attention: uplift "
            f"{signal['uplift'] * 100:+.0f}% at confidence {signal['confidence']:.2f} "
            f"across n={signal['sample_size']} cleared the ReLU gate, and "
            f"{top_action['type']}{magnitude_txt} ranked #1 by expected value × "
            f"confidence ({top_action['expected_value']:g} × "
            f"{top_action['confidence']:.2f} = {top_action['decision_score']:g})."
        )
    blocked = [item for item in validations if item["blocked"]]
    if blocked:
        first = blocked[0]
        failing = [check["detail"] for check in first["checks"] if not check["passed"]]
        blocked_action = next(
            (a for a in (actions or []) if a["action_id"] == first["action_id"]), None
        )
        blocked_magnitude = (blocked_action or {}).get("magnitude_pct")
        blocked_magnitude_txt = (
            "" if blocked_magnitude is None else f" {blocked_magnitude:+.0f}%"
        )
        if not parts:
            # Pure veto: nothing survived validation, so the hold IS the decision.
            parts.append("No move earned execution this run — the desk held.")
        parts.append(
            f"{first['type']}{blocked_magnitude_txt} → {first['entity_id']} was "
            "vetoed before execution: "
            + " ".join(failing)
            + f" The veto is not an opinion — it is arithmetic against {constraint_noun}."
        )
    if not parts:
        parts.append(
            "No move cleared the gate and guardrails this run — the system holds "
            "rather than act on weak evidence."
        )
    return " ".join(parts)


def _stage_trace(stage: str, index: int, summary: str, items: list[dict[str, Any]],
                 counts: dict[str, int]) -> dict[str, Any]:
    return {
        "stage": stage,
        "started_at": _iso(200 + index * 30),
        "summary": summary,
        "items": items,
        "counts": counts,
    }


def _rollback_token(trace_id: str, action_id: str) -> str:
    digest = hashlib.sha256(f"{trace_id}:{action_id}".encode()).hexdigest()
    return f"hmac-demo:{digest[:16]}"


def _require_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"unknown scenario: {scenario_id!r} (expected one of: {known})")
    return SCENARIOS[scenario_id]
