"""Capital Desk demo engine — governed capital-allocation decisions.

Signal-pattern engine (SSE streaming) for the MIZ OKI Capital division:
financial events are fused into per-entity return signals, gated by the
shared ReLU gate, and planned moves run the shared guardrails PLUS one
capital-specific rule — ``covenant_headroom`` — which blocks any move that
drops modeled covenant headroom below 15%.

The ReLU gate, guardrails, and default seed are imported from
``demo_signal`` (reuse, never duplicate). Every scenario carries exactly
ONE deliberate ``covenant_headroom`` block.
"""

from __future__ import annotations

import hashlib
import json
import random
from functools import lru_cache
from typing import Any, Iterator

from .demo_signal import DEFAULT_SEED, GuardrailSet, ReLUGate, build_causal_truth

__all__ = [
    "SCENARIOS",
    "DEFAULT_SEED",
    "COVENANT_HEADROOM_FLOOR_PCT",
    "CapitalGuardrailSet",
    "CapitalDeskPipeline",
    "list_scenarios",
]

COVENANT_HEADROOM_FLOOR_PCT = 15.0

_BASE_OFFSET = "2026-01-05T09:00:{sec:02d}Z"


def _iso(step: int) -> str:
    return _BASE_OFFSET.format(sec=min(step, 59))


SCENARIOS: dict[str, dict[str, Any]] = {
    "growth_reallocation": {
        "id": "growth_reallocation",
        "name": "Growth reallocation across business units",
        "description": (
            "Unit economics, pipeline velocity, and margin telemetry are "
            "fused into per-unit return signals; capital shifts toward the "
            "units clearing the gate — inside the covenant envelope."
        ),
        "metric": "roic_delta",
        "sources": ("ledger", "fpa", "market"),
        "event_types": {
            "ledger": ("journal_entry", "margin_snapshot"),
            "fpa": ("forecast_update", "pipeline_velocity"),
            "market": ("comp_multiple", "rate_quote"),
        },
        "profiles": (
            {"entity_id": "unit_cloud", "uplift": 0.19, "confidence": 0.88, "sample_size": 41, "weak": False},
            {"entity_id": "unit_services", "uplift": 0.11, "confidence": 0.76, "sample_size": 27, "weak": False},
            {"entity_id": "unit_hardware", "uplift": 0.02, "confidence": 0.79, "sample_size": 33, "weak": False},
            {"entity_id": "unit_intl", "uplift": 0.08, "confidence": 0.58, "sample_size": 22, "weak": True},
            {"entity_id": "unit_labs", "uplift": 0.14, "confidence": 0.72, "sample_size": 9, "weak": True},
        ),
        "hypothesis_template": "{entity} is compounding ROIC {uplift_pct}% above the portfolio",
        # (type, entity, magnitude_pct, expected_value, confidence, supporting, headroom_after_pct)
        "planned_actions": (
            ("capital_shift", "unit_cloud", 12.0, 9800.0, 0.88, 41, 24.0),
            ("capital_shift", "unit_services", 8.0, 4400.0, 0.76, 27, 21.0),
            # Deliberate covenant block: this shift models headroom at 11%.
            ("capital_shift", "unit_cloud", 18.0, 12100.0, 0.85, 41, 11.0),
        ),
        "learning_note": (
            "Concentrating capital on unit_cloud compounded ROIC while the "
            "covenant_headroom rule kept leverage inside the envelope."
        ),
    },
    "debt_paydown_vs_buyback": {
        "id": "debt_paydown_vs_buyback",
        "name": "Debt paydown vs share buyback",
        "description": (
            "Rate quotes, covenant snapshots, and equity telemetry compete: "
            "retire debt or repurchase shares. The gate ranks the options; "
            "the covenant rule vetoes the aggressive one."
        ),
        "metric": "wacc_delta",
        "sources": ("treasury", "market", "ledger"),
        "event_types": {
            "treasury": ("covenant_snapshot", "cash_position"),
            "market": ("rate_quote", "share_price"),
            "ledger": ("journal_entry",),
        },
        "profiles": (
            {"entity_id": "term_loan_b", "uplift": 0.16, "confidence": 0.84, "sample_size": 36, "weak": False},
            {"entity_id": "buyback_tranche", "uplift": 0.10, "confidence": 0.74, "sample_size": 25, "weak": False},
            {"entity_id": "revolver", "uplift": 0.03, "confidence": 0.77, "sample_size": 30, "weak": False},
            {"entity_id": "convert_notes", "uplift": 0.09, "confidence": 0.52, "sample_size": 18, "weak": True},
            {"entity_id": "dividend_bump", "uplift": 0.12, "confidence": 0.71, "sample_size": 7, "weak": True},
        ),
        "hypothesis_template": "{entity} cuts weighted capital cost by {uplift_pct}%",
        "planned_actions": (
            ("debt_paydown", "term_loan_b", 10.0, 8600.0, 0.84, 36, 27.0),
            ("share_buyback", "buyback_tranche", 6.0, 5100.0, 0.74, 25, 19.0),
            # Deliberate covenant block: leveraged buyback models headroom at 9%.
            ("share_buyback", "buyback_tranche", 14.0, 7900.0, 0.78, 25, 9.0),
        ),
        "learning_note": (
            "Paying down Term Loan B beat the leveraged buyback once the "
            "covenant_headroom rule priced in the modeled 9% headroom."
        ),
    },
    "working_capital_stress": {
        "id": "working_capital_stress",
        "name": "Working-capital stress absorption",
        "description": (
            "Receivables aging, payables timing, and inventory turns are "
            "stress-tested; the desk frees trapped cash without letting any "
            "draw breach the covenant floor."
        ),
        "metric": "cash_conversion_delta",
        "sources": ("ledger", "treasury", "fpa"),
        "event_types": {
            "ledger": ("journal_entry", "aging_snapshot"),
            "treasury": ("cash_position",),
            "fpa": ("forecast_update",),
        },
        "profiles": (
            {"entity_id": "receivables_program", "uplift": 0.17, "confidence": 0.82, "sample_size": 34, "weak": False},
            {"entity_id": "payables_terms", "uplift": 0.09, "confidence": 0.75, "sample_size": 24, "weak": False},
            {"entity_id": "inventory_turns", "uplift": 0.04, "confidence": 0.73, "sample_size": 28, "weak": False},
            {"entity_id": "fx_hedge_unwind", "uplift": 0.07, "confidence": 0.56, "sample_size": 20, "weak": True},
            {"entity_id": "supplier_discount", "uplift": 0.13, "confidence": 0.74, "sample_size": 8, "weak": True},
        ),
        "hypothesis_template": "{entity} frees cash-conversion days worth {uplift_pct}%",
        "planned_actions": (
            ("working_capital_draw", "receivables_program", 9.0, 7200.0, 0.82, 34, 22.0),
            ("working_capital_draw", "payables_terms", 7.0, 3900.0, 0.75, 24, 18.0),
            # Deliberate covenant block: the deep draw models headroom at 12%.
            ("working_capital_draw", "receivables_program", 16.0, 8800.0, 0.80, 34, 12.0),
        ),
        "learning_note": (
            "The receivables program released trapped cash; the deep draw "
            "was held by covenant_headroom before it could stress leverage."
        ),
    },
    "dividend_covenant_veto": {
        "id": "dividend_covenant_veto",
        "name": "Dividend distribution vs the covenant floor",
        "description": (
            "A special distribution is proposed against the reserve base. "
            "Covenant, cash, and reserve telemetry are sensed — and the one "
            "planned move models headroom below the 15% floor. Nothing "
            "executes: the veto IS the decision, and the operator gate holds."
        ),
        "metric": "distribution_headroom_delta",
        "sources": ("treasury", "ledger", "market"),
        "event_types": {
            "treasury": ("covenant_snapshot", "cash_position"),
            "ledger": ("journal_entry", "reserve_snapshot"),
            "market": ("rate_quote",),
        },
        "profiles": (
            {"entity_id": "holdco_dividend", "uplift": 0.18, "confidence": 0.82, "sample_size": 38, "weak": False},
            {"entity_id": "debt_service", "uplift": 0.12, "confidence": 0.78, "sample_size": 31, "weak": False},
            {"entity_id": "capex_program", "uplift": 0.02, "confidence": 0.74, "sample_size": 29, "weak": False},
            {"entity_id": "reserve_build", "uplift": 0.09, "confidence": 0.54, "sample_size": 21, "weak": True},
            {"entity_id": "buyback_probe", "uplift": 0.13, "confidence": 0.71, "sample_size": 8, "weak": True},
        ),
        "hypothesis_template": "{entity} lifts distributable headroom {uplift_pct}% this quarter",
        # The ONLY planned move breaches the covenant floor (headroom 7% < 15%),
        # so this scenario executes NOTHING — the pure-veto flagship.
        "planned_actions": (
            ("special_distribution", "holdco_dividend", 16.0, 11800.0, 0.82, 38, 7.0),
        ),
        "learning_note": (
            "The distribution was held at the covenant floor. Nothing executed "
            "— the desk holds until an operator routes a smaller alternative "
            "through the gate."
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


def _require_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"unknown scenario: {scenario_id!r} (expected one of: {known})")
    return SCENARIOS[scenario_id]


_SOURCE_CONFIDENCE = {"ledger": 0.92, "treasury": 0.90, "fpa": 0.82, "market": 0.78}


class CapitalGuardrailSet:
    """The shared guardrails plus the capital-specific covenant rule."""

    HEADROOM_FLOOR_PCT = COVENANT_HEADROOM_FLOOR_PCT

    @classmethod
    def evaluate(cls, action: dict[str, Any]) -> list[dict[str, Any]]:
        checks = GuardrailSet.evaluate(action)
        headroom = float(action.get("headroom_after_pct", 100.0))
        headroom_ok = headroom >= cls.HEADROOM_FLOOR_PCT
        checks.append({
            "rule_id": "covenant_headroom",
            "name": f"Covenant headroom ≥ {cls.HEADROOM_FLOOR_PCT:.0f}%",
            "passed": headroom_ok,
            "detail": (
                f"Modeled covenant headroom {headroom:.0f}% stays above the "
                f"{cls.HEADROOM_FLOOR_PCT:.0f}% floor."
                if headroom_ok
                else (
                    f"Modeled covenant headroom {headroom:.0f}% would breach "
                    f"the {cls.HEADROOM_FLOOR_PCT:.0f}% floor — move blocked."
                )
            ),
        })
        return checks


class CapitalDeskPipeline:
    """Signal-pattern pipeline for capital allocation (with SSE frames)."""

    STAGES = ("sense", "reason", "plan", "validate", "decide", "act", "learn")

    def __init__(self) -> None:
        self.gate = ReLUGate()
        self.guardrails = CapitalGuardrailSet()

    # -- public API --------------------------------------------------------

    def run(self, scenario_id: str, seed: int = DEFAULT_SEED) -> dict[str, Any]:
        return self._bundle(scenario_id, seed)["pipeline_run"]

    def run_streaming(self, scenario_id: str, seed: int = DEFAULT_SEED) -> Iterator[dict[str, Any]]:
        """Yield SSE-ready frames. Pacing is the caller's job (delay_hint_ms)."""
        bundle = self._bundle(scenario_id, seed)
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

    def _bundle(self, scenario_id: str, seed: int) -> dict[str, Any]:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")
        _require_scenario(scenario_id)
        return json.loads(_cached_bundle_json(scenario_id, seed))

    def _execute(self, scenario_id: str, seed: int) -> dict[str, Any]:
        scenario = _require_scenario(scenario_id)
        rng = random.Random(seed)
        trace_id = "cap-" + hashlib.sha256(f"{scenario_id}:{seed}".encode()).hexdigest()[:12]

        profiles = scenario["profiles"]
        sources = scenario["sources"]
        raw_events: list[dict[str, Any]] = []
        for index in range(15):
            profile = profiles[index % len(profiles)]
            source = sources[index % len(sources)]
            event_type = rng.choice(scenario["event_types"][source])
            weak = bool(profile["weak"])
            value = round(rng.uniform(0.4, 5.0), 2) if weak else round(rng.uniform(40.0, 640.0), 2)
            raw_events.append({
                "event_id": f"fin_{index + 1:03d}",
                "source": source,
                "event_type": event_type,
                "entity_id": profile["entity_id"],
                "value": value,
                "timestamp": _iso(index),
                "raw_payload": {
                    "n": rng.randint(1, 4) if weak else rng.randint(3, 9),
                    "currency": "USD",
                    "book": rng.choice(["group", "opco"]),
                },
            })

        canonical_events = []
        for raw in raw_events:
            confidence = round(min(0.99, max(0.05, _SOURCE_CONFIDENCE[raw["source"]])), 2)
            canonical_events.append({
                "canonical_id": f"can_{raw['event_id']}",
                "entities": [raw["entity_id"], "tenant:demo"],
                "relationships": [
                    {"from": raw["event_id"], "type": "NORMALIZED_TO", "to": f"can_{raw['event_id']}"},
                    {"from": f"can_{raw['event_id']}", "type": "OBSERVED_FOR", "to": raw["entity_id"]},
                ],
                "confidence": confidence,
                "security_scope": {"tenant": "demo"},
                "provenance": {
                    "source": raw["source"],
                    "connector": f"{raw['source']}_connector",
                    "received_at": raw["timestamp"],
                    "transform": "demo_normalizer_v1",
                },
            })

        signals = [
            {
                "entity_id": profile["entity_id"],
                "metric": scenario["metric"],
                "uplift": profile["uplift"],
                "confidence": profile["confidence"],
                "sample_size": profile["sample_size"],
            }
            for profile in profiles
        ]
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
            action_type, entity_id, magnitude, expected_value, confidence, supporting, headroom = spec
            action_id = f"act_{scenario_id}_{index}"
            actions.append({
                "action_id": action_id,
                "type": action_type,
                "entity_id": entity_id,
                "magnitude_pct": magnitude,
                "expected_value": expected_value,
                "confidence": confidence,
                "supporting_conversions": supporting,
                "headroom_after_pct": headroom,
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
                {**action, "decision_score": round(action["expected_value"] * action["confidence"], 2)}
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

        learn_rng = random.Random(seed + 11)
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
                 "detail": f"{len(entity_raw)} financial events sensed for {top_action['entity_id']}."},
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
                 "detail": (
                     f"All 6 guardrails passed — covenant headroom "
                     f"{top_action['headroom_after_pct']:.0f}% clears the 15% floor; rollback token minted."
                 )},
                {"stage": "decision", "ref": top_action["action_id"],
                 "detail": f"Ranked #1 by expected_value × confidence = {top_action['decision_score']}."},
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
            "causal_truth": build_causal_truth(
                top_action, top_verdict, validations, actions,
                constraint_noun="the covenant",
            ),
        }

        stages = [
            _stage_trace("sense", 0,
                         f"Sensed {len(raw_events)} financial events across "
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
                         f"Proposed {len(actions)} capital moves from surviving hypotheses.",
                         actions,
                         {"proposed_actions": len(actions)}),
            _stage_trace("validate", 3,
                         f"Ran {len(actions) * 6} guardrail checks (including covenant_headroom); "
                         f"blocked {len(blocked_ids)} move(s) before execution.",
                         validations,
                         {"actions_checked": len(actions), "blocked": len(blocked_ids)}),
            _stage_trace("decide", 4,
                         f"Ranked {len(ranked)} surviving moves by expected_value × confidence.",
                         ranked,
                         {"decided": len(ranked)}),
            _stage_trace("act", 5,
                         f"Executed {len(executions)} move(s) in dry-run mode with rollback tokens.",
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


@lru_cache(maxsize=64)
def _cached_bundle_json(scenario_id: str, seed: int) -> str:
    return json.dumps(CapitalDeskPipeline()._execute(scenario_id, seed))


def _stage_trace(stage: str, index: int, summary: str, items: list[dict[str, Any]],
                 counts: dict[str, int]) -> dict[str, Any]:
    return {
        "stage": stage,
        "started_at": _iso(index),
        "summary": summary,
        "items": items,
        "counts": counts,
    }


def _rollback_token(trace_id: str, action_id: str) -> str:
    digest = hashlib.sha256(f"{trace_id}:{action_id}".encode()).hexdigest()
    return f"hmac-demo:{digest[:16]}"
