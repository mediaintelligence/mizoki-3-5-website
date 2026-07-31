"""The Nexus Run — five division engines chained under one trace id.

The flagship demo: a single trigger ripples through Signal, Capital, Risk,
Counsel, and Estate deterministically, every division's decision hanging
off one ``nexus_trace_id``. Performs the tagline:

    One intelligence. Many domains. Shared causal memory.

Scenarios:
- ``cpm_shock`` (default): Meta CPM +38% on campaign_7 → Signal
  reallocates through the ReLU gate → Capital re-checks covenant headroom
  (one variant blocked) → Risk vetoes the aggressive variant → Counsel
  flags the replacement vendor's indemnity clause → Estate logs the
  governance ledger entry (nothing fires — restraint is also a decision).
- ``contract_breach_cascade``: a Counsel-originated ripple (indemnity
  breach → Risk veto → Capital reserve → Signal spend freeze).

Invariants (tested): the shared trace id appears in all five division
segments; ``cpm_shock`` carries exactly one Capital block and one Risk
veto; the stream terminates with ``done``; runs are deep-equal for the
same ``(scenario, seed)``.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any, Iterator

from .demo_capital import CapitalDeskPipeline
from .demo_counsel import UNAUTHORIZED_PRACTICE_WARNING
from .demo_estate import EstateRoomEngine
from .demo_risk import RiskSentinelEngine
from .demo_signal import DEFAULT_SEED, SignalFactoryPipeline

__all__ = [
    "SCENARIOS",
    "DEFAULT_SEED",
    "TAGLINE",
    "DIVISIONS",
    "NexusRunEngine",
    "list_scenarios",
]

TAGLINE = "One intelligence. Many domains. Shared causal memory."
DIVISIONS = ("signal", "capital", "risk", "counsel", "estate")

SCENARIOS: dict[str, dict[str, Any]] = {
    "cpm_shock": {
        "id": "cpm_shock",
        "name": "CPM shock — Meta CPM +38% on campaign_7",
        "description": (
            "An overnight CPM spike on the best-performing campaign ripples "
            "through all five divisions: Signal reallocates, Capital "
            "re-checks the covenant envelope, Risk vetoes the aggressive "
            "variant, Counsel flags the replacement vendor's indemnity "
            "clause, and Estate records that nothing needed to fire."
        ),
        "order": ("signal", "capital", "risk", "counsel", "estate"),
        "trigger": {
            "title": "Meta CPM +38% on campaign_7",
            "detail": (
                "Overnight auction pressure inflated CPMs 38% on the "
                "account's strongest campaign. The shock enters the Nexus "
                "as one canonical event — and every division sees it."
            ),
            "source": "meta_connector",
        },
    },
    "contract_breach_cascade": {
        "id": "contract_breach_cascade",
        "name": "Contract breach cascade — indemnity ripple",
        "description": (
            "A vendor's indemnity breach starts in Counsel and cascades: "
            "Risk vetoes the auto-renewal, Capital books a reserve, Signal "
            "freezes spend on the affected campaigns, and Estate logs the "
            "governance trail."
        ),
        "order": ("counsel", "risk", "capital", "signal", "estate"),
        "trigger": {
            "title": "Vendor indemnity breach detected",
            "detail": (
                "Contract telemetry flagged a unilateral indemnity edit in a "
                "critical vendor's renewal paper. The breach enters the "
                "Nexus as one canonical event — and the cascade begins."
            ),
            "source": "contract_connector",
        },
    },
}

# Which sub-scenario each division engine runs, per nexus scenario.
_SUB_SCENARIOS = {
    "cpm_shock": {
        "signal": "ecommerce_roas",
        "capital": "growth_reallocation",
        "risk": "campaign_compliance",
        "estate": "ct_estate_settlement",
    },
    "contract_breach_cascade": {
        "signal": "leadgen_cpa",
        "capital": "working_capital_stress",
        "risk": "vendor_breach_drill",
        "estate": "ct_estate_settlement",
    },
}


def list_scenarios() -> list[dict[str, Any]]:
    return [
        {"id": s["id"], "name": s["name"], "description": s["description"],
         "order": list(s["order"])}
        for s in SCENARIOS.values()
    ]


def _require_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"unknown scenario: {scenario_id!r} (expected one of: {known})")
    return SCENARIOS[scenario_id]


def _segment(division: str, nexus_trace_id: str, division_trace_id: str,
             headline: str, events: list[str], verdict: dict[str, Any],
             extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "division": division,
        "nexus_trace_id": nexus_trace_id,
        "division_trace_id": division_trace_id,
        "headline": headline,
        "events": events,
        "verdict": verdict,
    }
    if extra:
        payload.update(extra)
    return payload


@lru_cache(maxsize=32)
def _cached_run_json(scenario_id: str, seed: int) -> str:
    scenario = _require_scenario(scenario_id)
    nexus_trace_id = "nex-" + hashlib.sha256(f"{scenario_id}:{seed}".encode()).hexdigest()[:12]
    subs = _SUB_SCENARIOS[scenario_id]

    signal_run = SignalFactoryPipeline().run(subs["signal"], seed=seed)
    capital_run = CapitalDeskPipeline().run(subs["capital"], seed=seed)
    risk_run = RiskSentinelEngine().run(subs["risk"], seed=seed)
    estate_run = EstateRoomEngine().run(subs["estate"], seed=seed)

    signal_card = signal_run["decision_card"]
    signal_action = signal_card["executed_action"] or {}
    capital_card = capital_run["decision_card"]
    capital_block = capital_card["guardrail_block"]
    capital_action = capital_card["executed_action"] or {}
    risk_veto = next(e for e in risk_run["escalations"] if e["kind"] == "vetoed")
    risk_auto = next(e for e in risk_run["escalations"] if e["kind"] == "auto_mitigated")

    signal_seg = _segment(
        "signal", nexus_trace_id, signal_run["trace_id"],
        "Signal reallocates through the ReLU gate",
        [
            f"{signal_run['funnel']['events_sensed']} raw events fused into "
            f"{signal_run['funnel']['signals_formed']} entity signals.",
            f"{signal_run['funnel']['passed_gate']} signals cleared the ReLU gate "
            f"(uplift, confidence, and sample floors all enforced).",
            f"Top action: {signal_action.get('type', 'none')} "
            f"{signal_action.get('magnitude_pct', 0):+.0f}% → {signal_action.get('entity_id', '—')} "
            f"(EV ${signal_action.get('expected_value', 0):,.0f}).",
        ],
        {
            "status": "executed",
            "action": signal_action,
            "detail": (
                "Budget concentrates where the gate held the floor — "
                "executed dry-run with a rollback token."
            ),
        },
        {"funnel": signal_run["funnel"]},
    )

    capital_seg = _segment(
        "capital", nexus_trace_id, capital_run["trace_id"],
        "Capital re-checks covenant headroom on the shifted spend",
        [
            "The reallocated spend re-enters the desk as a capital move and "
            "faces all six guardrails.",
            f"Variant {capital_block['action_id']} blocked by "
            f"{', '.join(capital_block['blocked_by'])} — modeled headroom "
            "fell below the 15% floor.",
            f"Surviving move: {capital_action.get('type', 'none')} "
            f"{capital_action.get('magnitude_pct', 0):+.0f}% → {capital_action.get('entity_id', '—')} "
            f"(headroom {capital_action.get('headroom_after_pct', 0):.0f}%).",
        ],
        {
            "status": "one_variant_blocked",
            "blocked": capital_block,
            "action": capital_action,
            "detail": (
                "The aggressive variant never reaches execution; the "
                "covenant envelope holds."
            ),
        },
        {"funnel": capital_run["funnel"]},
    )

    risk_seg = _segment(
        "risk", nexus_trace_id, risk_run["trace_id"],
        "Risk lights the matrix and vetoes the aggressive variant",
        [
            f"{risk_run['funnel']['events_sensed']} enterprise events landed "
            "on the 5×5 severity×likelihood matrix.",
            f"Auto-mitigated: {risk_auto['entity_id']} under "
            f"{risk_auto['rule_id']} (green path).",
            f"VETOED: {risk_veto['entity_id']} under {risk_veto['rule_id']} — "
            f"rollback token {risk_veto['rollback_token']}.",
        ],
        {
            "status": "vetoed",
            "veto": risk_veto,
            "auto_mitigated": risk_auto,
            "detail": (
                "One quiet mitigation, one loud veto — the ACT-991 pattern, "
                "evidence chain attached."
            ),
        },
        {"funnel": risk_run["funnel"]},
    )

    counsel_events = (
        [
            "The replacement vendor's paper arrives for signature during the shock.",
            "Clause diff: §9 indemnity — mutual indemnity swapped for a "
            "one-way cap at fees paid.",
            "Counsel lane flags the clause for attorney review before any "
            "signature can route.",
        ]
        if scenario_id == "cpm_shock"
        else [
            "Contract telemetry surfaces the unilateral indemnity edit in "
            "the renewal paper.",
            "Counsel lane maps the breach's blast radius: renewal, data "
            "processing addendum, and two dependent SOWs.",
            "Every downstream division receives the flagged clause as a "
            "canonical event on this trace.",
        ]
    )
    counsel_seg = _segment(
        "counsel", nexus_trace_id,
        "cns-" + hashlib.sha256(f"counsel:{scenario_id}:{seed}".encode()).hexdigest()[:12],
        "Counsel flags the indemnity clause",
        counsel_events,
        {
            "status": "flagged_for_review",
            "detail": (
                "Advisory only — the clause is held for a Connecticut-licensed "
                "attorney; no autonomous signature exists on this platform."
            ),
        },
        {
            "flagged_for_review": True,
            "unauthorized_practice_warning": UNAUTHORIZED_PRACTICE_WARNING,
        },
    )

    estate_ledger_entry = {
        "entry_id": "led_nexus_01",
        "recorded_by": "estate_governance_lane",
        "note": (
            "No estate-side action required by this trace. Restraint "
            "recorded as a decision — the ledger remembers what did not fire."
        ),
        "linked_trace": nexus_trace_id,
    }
    estate_seg = _segment(
        "estate", nexus_trace_id, estate_run["trace_id"],
        "Estate records the governance ledger entry — nothing fires",
        [
            "The trace reaches the Estate lane with zero fiduciary surface.",
            "Governance ledger entry written: restraint is also a decision.",
            "The five statutory clocks stay armed and untouched.",
        ],
        {
            "status": "ledger_entry_recorded",
            "ledger_entry": estate_ledger_entry,
            "detail": "Nothing fired — and that non-action is itself auditable.",
        },
        {
            "flagged_for_review": True,
            "unauthorized_practice_warning": UNAUTHORIZED_PRACTICE_WARNING,
        },
    )

    by_division = {
        "signal": signal_seg,
        "capital": capital_seg,
        "risk": risk_seg,
        "counsel": counsel_seg,
        "estate": estate_seg,
    }
    divisions = [by_division[name] for name in scenario["order"]]

    provenance_nodes = [
        {"node_id": "trigger", "kind": "trigger", "label": scenario["trigger"]["title"]},
        {"node_id": "nexus", "kind": "trace", "label": nexus_trace_id},
    ] + [
        {
            "node_id": seg["division"],
            "kind": "division_decision",
            "label": f"{seg['division']} · {seg['verdict']['status']}",
            "division_trace_id": seg["division_trace_id"],
        }
        for seg in divisions
    ]
    provenance_edges = [
        {"from": "trigger", "to": "nexus", "relation": "OPENED_TRACE"},
    ] + [
        {"from": "nexus", "to": seg["division"], "relation": "DECIDED_IN"}
        for seg in divisions
    ]

    run = {
        "nexus_trace_id": nexus_trace_id,
        "scenario": scenario_id,
        "scenario_name": scenario["name"],
        "seed": seed,
        "tagline": TAGLINE,
        "trigger": dict(scenario["trigger"]),
        "divisions": divisions,
        "provenance": {"nodes": provenance_nodes, "edges": provenance_edges},
        "flagged_for_review": True,
        "unauthorized_practice_warning": UNAUTHORIZED_PRACTICE_WARNING,
    }
    return json.dumps(run)


class NexusRunEngine:
    """Chains the five division engines deterministically."""

    def run(self, scenario_id: str, seed: int = DEFAULT_SEED) -> dict[str, Any]:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")
        _require_scenario(scenario_id)
        return json.loads(_cached_run_json(scenario_id, seed))

    def run_streaming(self, scenario_id: str, seed: int = DEFAULT_SEED) -> Iterator[dict[str, Any]]:
        """Yield SSE-ready frames: trigger → per-division start/event/verdict
        → provenance → done. Pacing is the caller's job (delay_hint_ms)."""
        run = self.run(scenario_id, seed=seed)
        yield {"type": "trigger", "data": run["trigger"], "delay_hint_ms": 1000}
        for segment in run["divisions"]:
            yield {
                "type": "division_start",
                "data": {
                    "division": segment["division"],
                    "nexus_trace_id": segment["nexus_trace_id"],
                    "division_trace_id": segment["division_trace_id"],
                    "headline": segment["headline"],
                },
                "delay_hint_ms": 800,
            }
            for event in segment["events"]:
                yield {
                    "type": "division_event",
                    "data": {"division": segment["division"], "event": event},
                    "delay_hint_ms": 900,
                }
            yield {
                "type": "division_verdict",
                "data": {"division": segment["division"], "verdict": segment["verdict"]},
                "delay_hint_ms": 1200,
            }
        yield {"type": "provenance", "data": run["provenance"], "delay_hint_ms": 1500}
        yield {
            "type": "done",
            "data": {
                "nexus_trace_id": run["nexus_trace_id"],
                "scenario": scenario_id,
                "seed": seed,
                "tagline": TAGLINE,
            },
            "delay_hint_ms": 0,
        }
