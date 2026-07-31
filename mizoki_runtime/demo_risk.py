"""Risk Sentinel demo engine — enterprise events on a 5×5 risk matrix.

Deterministic, stdlib-only simulation of the MIZ OKI Risk division:
12–16 seeded enterprise events (contract clause changes, spend spikes,
PII access anomalies, covenant drift) land on a 5×5 severity×likelihood
matrix. Every scenario produces exactly TWO escalations — one
auto-mitigated (green) and one VETOED (red) with a rule id, an evidence
chain, and an ``hmac-demo:`` rollback token, mirroring the ACT-991 story
on /console.
"""

from __future__ import annotations

import hashlib
import json
import random
from functools import lru_cache
from typing import Any

from .demo_signal import DEFAULT_SEED

__all__ = [
    "SCENARIOS",
    "DEFAULT_SEED",
    "RiskSentinelEngine",
    "list_scenarios",
]

_BASE_TS = "2026-01-05T09:{minute:02d}:00Z"

_EVENT_CATEGORIES = (
    ("contract_clause_change", "Contract clause change"),
    ("spend_spike", "Spend spike"),
    ("pii_access_anomaly", "PII access anomaly"),
    ("covenant_drift", "Covenant drift"),
)

SCENARIOS: dict[str, dict[str, Any]] = {
    "quarterly_close": {
        "id": "quarterly_close",
        "name": "Quarterly close watch",
        "description": (
            "Close week: journal reclasses, covenant snapshots, and access "
            "grants all spike at once. The Sentinel sorts noise from the two "
            "events that actually deserve an escalation."
        ),
        "event_count": 14,
        "entities": ("gl_journal", "term_loan_b", "close_checklist", "erp_access",
                     "vendor_accruals", "fx_reval"),
        "auto_escalation": {
            "category": "covenant_drift",
            "entity": "term_loan_b",
            "severity": 4,
            "likelihood": 3,
            "rule_id": "covenant_drift_watch",
            "detail": "Modeled leverage drifted to 0.4 turns from the covenant ceiling during close.",
            "mitigation": "Auto-booked a discretionary reserve and re-ran the covenant model — headroom restored to 19%.",
            "evidence_chain": (
                "treasury covenant_snapshot can_fin_007",
                "leverage model rerun v3 (deterministic)",
                "reserve journal drafted + posted dry-run",
            ),
        },
        "veto_escalation": {
            "category": "spend_spike",
            "entity": "vendor_accruals",
            "severity": 5,
            "likelihood": 4,
            "rule_id": "close_week_spend_freeze",
            "detail": "A $1.9M accrual release was queued for auto-approval inside the close window.",
            "evidence_chain": (
                "ap queue item ap_4471 flagged by anomaly screen",
                "close_week_spend_freeze rule matched (window day 3 of 5)",
                "authorization request escalated — ACT-991 pattern",
            ),
        },
    },
    "vendor_breach_drill": {
        "id": "vendor_breach_drill",
        "name": "Vendor breach drill",
        "description": (
            "A tabletop breach at a data vendor: access anomalies, an "
            "indemnity clause edit, and panic spend requests. One event "
            "auto-mitigates; one gets vetoed with the evidence to prove why."
        ),
        "event_count": 15,
        "entities": ("vendor_dataco", "dpa_contract", "iam_grants", "incident_bridge",
                     "pr_retainer", "backup_vendor"),
        "auto_escalation": {
            "category": "pii_access_anomaly",
            "entity": "iam_grants",
            "severity": 4,
            "likelihood": 4,
            "rule_id": "pii_access_quarantine",
            "detail": "Service account queried 6× its baseline row count against the customer PII store.",
            "mitigation": "Credentials rotated and grant scoped to masked views automatically; access normal within minutes.",
            "evidence_chain": (
                "access telemetry z-score 4.2 vs 30-day baseline",
                "pii_access_quarantine rule matched",
                "rotation + scope-down executed dry-run with audit entry",
            ),
        },
        "veto_escalation": {
            "category": "contract_clause_change",
            "entity": "dpa_contract",
            "severity": 5,
            "likelihood": 3,
            "rule_id": "indemnity_clause_review",
            "detail": "The replacement vendor's paper swaps mutual indemnity for a one-way cap at fees paid.",
            "evidence_chain": (
                "clause diff: §9 indemnity — mutual → one-way (cap: fees paid)",
                "indemnity_clause_review rule matched; counsel lane flagged",
                "signature request vetoed — ACT-991 pattern",
            ),
        },
    },
    "campaign_compliance": {
        "id": "campaign_compliance",
        "name": "Campaign compliance sweep",
        "description": (
            "A live media push under compliance watch: frequency caps, spend "
            "velocity, and audience consent all monitored. The aggressive "
            "reallocation variant meets the veto it deserves."
        ),
        "event_count": 13,
        "entities": ("campaign_7", "audience_hv", "consent_ledger", "creative_pool",
                     "spend_pacer", "brand_safety"),
        "auto_escalation": {
            "category": "spend_spike",
            "entity": "spend_pacer",
            "severity": 3,
            "likelihood": 4,
            "rule_id": "frequency_cap_throttle",
            "detail": "Frequency on audience_hv crossed 3.4/day against a 3.0 cap during the CPM shock.",
            "mitigation": "Pacer auto-throttled delivery 12% and rebalanced toward under-exposed segments.",
            "evidence_chain": (
                "frequency telemetry 3.4/day vs cap 3.0",
                "frequency_cap_throttle rule matched",
                "throttle applied dry-run; exposure normalized",
            ),
        },
        "veto_escalation": {
            "category": "spend_spike",
            "entity": "campaign_7",
            "severity": 4,
            "likelihood": 4,
            "rule_id": "aggressive_reallocation_veto",
            "detail": "The +25% reallocation variant would breach the budget-swing envelope while CPMs are inflated.",
            "evidence_chain": (
                "reallocation variant B: +25% into campaign_7 during CPM +38%",
                "aggressive_reallocation_veto rule matched (envelope ±20%)",
                "execution vetoed with rollback token minted — ACT-991 pattern",
            ),
        },
    },
}


def list_scenarios() -> list[dict[str, Any]]:
    return [
        {"id": s["id"], "name": s["name"], "description": s["description"],
         "event_count": s["event_count"]}
        for s in SCENARIOS.values()
    ]


def _require_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"unknown scenario: {scenario_id!r} (expected one of: {known})")
    return SCENARIOS[scenario_id]


def _rollback_token(trace_id: str, ref: str) -> str:
    digest = hashlib.sha256(f"{trace_id}:{ref}".encode()).hexdigest()
    return f"hmac-demo:{digest[:16]}"


def _make_event(index: int, category: str, entity: str, severity: int,
                likelihood: int, detail: str, escalation: str | None) -> dict[str, Any]:
    label = dict(_EVENT_CATEGORIES)[category]
    return {
        "event_id": f"rsk_{index + 1:03d}",
        "category": category,
        "category_label": label,
        "entity_id": entity,
        "severity": severity,
        "likelihood": likelihood,
        "cell_id": f"s{severity}l{likelihood}",
        "detail": detail,
        "timestamp": _BASE_TS.format(minute=min(index * 2, 58)),
        "escalation": escalation,
    }


@lru_cache(maxsize=64)
def _cached_run_json(scenario_id: str, seed: int) -> str:
    scenario = _require_scenario(scenario_id)
    rng = random.Random(seed)
    trace_id = "rsk-" + hashlib.sha256(f"{scenario_id}:{seed}".encode()).hexdigest()[:12]

    auto = scenario["auto_escalation"]
    veto = scenario["veto_escalation"]
    count = scenario["event_count"]
    entities = scenario["entities"]

    events: list[dict[str, Any]] = []
    for index in range(count - 2):
        category = _EVENT_CATEGORIES[index % len(_EVENT_CATEGORIES)][0]
        entity = entities[index % len(entities)]
        severity = rng.randint(1, 3)
        likelihood = rng.randint(1, 4)
        detail = (
            f"Routine {dict(_EVENT_CATEGORIES)[category].lower()} on {entity} "
            f"— inside tolerance, logged to the graph."
        )
        events.append(_make_event(index, category, entity, severity, likelihood, detail, None))

    auto_event = _make_event(count - 2, auto["category"], auto["entity"],
                             auto["severity"], auto["likelihood"], auto["detail"],
                             "auto_mitigated")
    veto_event = _make_event(count - 1, veto["category"], veto["entity"],
                             veto["severity"], veto["likelihood"], veto["detail"],
                             "vetoed")
    events.extend([auto_event, veto_event])

    matrix_counts: dict[str, int] = {}
    for event in events:
        matrix_counts[event["cell_id"]] = matrix_counts.get(event["cell_id"], 0) + 1
    matrix_cells = [
        {"cell_id": f"s{sev}l{lik}", "severity": sev, "likelihood": lik,
         "count": matrix_counts.get(f"s{sev}l{lik}", 0)}
        for sev in range(1, 6)
        for lik in range(1, 6)
    ]

    escalations = [
        {
            "escalation_id": f"esc_{scenario_id}_auto",
            "kind": "auto_mitigated",
            "status": "mitigated",
            "event_id": auto_event["event_id"],
            "entity_id": auto["entity"],
            "rule_id": auto["rule_id"],
            "detail": auto["detail"],
            "mitigation": auto["mitigation"],
            "evidence_chain": list(auto["evidence_chain"]),
        },
        {
            "escalation_id": f"esc_{scenario_id}_veto",
            "kind": "vetoed",
            "status": "vetoed",
            "event_id": veto_event["event_id"],
            "entity_id": veto["entity"],
            "rule_id": veto["rule_id"],
            "detail": veto["detail"],
            "evidence_chain": list(veto["evidence_chain"]),
            "rollback_token": _rollback_token(trace_id, veto_event["event_id"]),
        },
    ]

    run = {
        "trace_id": trace_id,
        "scenario": scenario_id,
        "scenario_name": scenario["name"],
        "seed": seed,
        "events": events,
        "matrix": {"rows": 5, "cols": 5, "cells": matrix_cells},
        "escalations": escalations,
        "funnel": {
            "events_sensed": len(events),
            "escalated": 2,
            "auto_mitigated": 1,
            "vetoed": 1,
        },
        "finale": {
            "headline": "Two escalations. One quiet mitigation. One loud veto.",
            "summary": (
                f"{len(events)} events landed on the matrix; the Sentinel "
                f"auto-mitigated {auto['entity']} under {auto['rule_id']} and "
                f"vetoed {veto['entity']} under {veto['rule_id']} with a "
                "rollback token minted before anything could execute."
            ),
            "key_numbers": [
                {"label": "events on matrix", "value": str(len(events))},
                {"label": "auto-mitigated", "value": "1"},
                {"label": "vetoed", "value": "1"},
            ],
        },
    }
    return json.dumps(run)


class RiskSentinelEngine:
    """Deterministic request/response engine (page paces the matrix itself)."""

    def run(self, scenario_id: str, seed: int = DEFAULT_SEED) -> dict[str, Any]:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")
        _require_scenario(scenario_id)
        return json.loads(_cached_run_json(scenario_id, seed))
