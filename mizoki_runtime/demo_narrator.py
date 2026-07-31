"""Trace Narrator — deterministic plain-English narration of any demo run.

The "Why?" button behind every finale card. Template-based, 4–6 sentences,
citing entity names, uplift/confidence/sample numbers, which rule blocked
what and why, and the expected-value ranking. No LLM, no tokens — the same
seed always produces the same words, so this is explainable AI with zero
abuse surface.
"""

from __future__ import annotations

from typing import Any

from . import demo_capital, demo_counsel, demo_estate, demo_nexus, demo_risk, demo_signal
from .demo_signal import DEFAULT_SEED

__all__ = ["NARRATABLE_DEMOS", "narrate"]

NARRATABLE_DEMOS = ("signal", "capital", "counsel", "estate", "risk", "nexus")


def narrate(demo: str, scenario: str, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    """Return ``{"narration": str, "trace_id": str}`` for the given run."""
    if demo not in NARRATABLE_DEMOS:
        known = ", ".join(NARRATABLE_DEMOS)
        raise ValueError(f"unknown demo: {demo!r} (expected one of: {known})")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    return _NARRATORS[demo](scenario, seed)


# --------------------------------------------------------------------------
# Pipeline narrations (Signal + Capital share their shape)
# --------------------------------------------------------------------------

def _narrate_pipeline(run: dict[str, Any], flavor: str) -> dict[str, Any]:
    funnel = run["funnel"]
    card = run["decision_card"]
    action = card["executed_action"] or {}
    block = card["guardrail_block"]

    reason_stage = next(s for s in run["stages"] if s["stage"] == "reason")
    verdicts = [item for item in reason_stage["items"] if "signal" in item]
    passing = [v for v in verdicts if v["passed"]]
    top_signal = next(
        (v["signal"] for v in passing if v["entity_id"] == action.get("entity_id")),
        passing[0]["signal"] if passing else None,
    )
    decide_stage = next(s for s in run["stages"] if s["stage"] == "decide")
    ranked = decide_stage["items"]

    sentences = [
        (
            f"This run sensed {funnel['events_sensed']} raw {flavor} events, formed "
            f"{funnel['signals_formed']} entity signals, and passed {funnel['passed_gate']} "
            f"of them through the ReLU gate."
        ),
    ]
    if top_signal:
        sentences.append(
            f"The strongest signal came from {top_signal['entity_id']}: uplift "
            f"{top_signal['uplift'] * 100:+.0f}%, confidence {top_signal['confidence']:.2f}, "
            f"on a sample of {top_signal['sample_size']} — comfortably above every floor."
        )
    if block:
        sentences.append(
            f"One proposed move, {block['action_id']} on {block['entity_id']}, was blocked by "
            f"the {', '.join(block['blocked_by'])} rule before it could execute — that is the "
            f"governor doing its job, not a failure."
        )
    if ranked:
        ranking = ", then ".join(
            f"{item['entity_id']} ({item['type']}, score {item['decision_score']})"
            for item in ranked[:3]
        )
        sentences.append(
            f"The surviving moves were ranked by expected value × confidence: {ranking}."
        )
    if action:
        sentences.append(
            f"The winner — {action['type']} {action.get('magnitude_pct', 0):+.0f}% on "
            f"{action['entity_id']} — executed in dry-run mode with rollback token "
            f"{action['rollback_token']}."
        )
    sentences.append(
        "Replay this trace with the same seed and every number above reproduces exactly."
    )
    return {"narration": " ".join(sentences), "trace_id": run["trace_id"]}


def _narrate_signal(scenario: str, seed: int) -> dict[str, Any]:
    run = demo_signal.SignalFactoryPipeline().run(scenario, seed=seed)
    return _narrate_pipeline(run, "marketing")


def _narrate_capital(scenario: str, seed: int) -> dict[str, Any]:
    run = demo_capital.CapitalDeskPipeline().run(scenario, seed=seed)
    return _narrate_pipeline(run, "financial")


# --------------------------------------------------------------------------
# Counsel / Estate / Risk / Nexus
# --------------------------------------------------------------------------

def _narrate_counsel(scenario: str, seed: int) -> dict[str, Any]:
    response = demo_counsel.LegalSynthesizer().synthesize(scenario_id=scenario)
    consulted = [entry for entry in response["routing"] if entry["consulted"]]
    top = consulted[0] if consulted else None
    conflicts = response["conflicts"]
    sentences = [
        (
            f"The question routed to {len(consulted)} of four domain experts, led by "
            f"{top['expert_label']} at relevance {top['relevance']:.2f}."
            if top else "The question routed through the Mixture-of-Legal-Experts."
        ),
        (
            f"Each consulted expert filed a full IRAC analysis — "
            f"{len(response['expert_analyses'])} in total — citing only authorities from "
            "the shared corpus."
        ),
    ]
    if conflicts:
        first = conflicts[0]
        sentences.append(
            f"One cross-domain conflict surfaced ({first['conflict_id']}, severity "
            f"{first['severity']}): {first['summary']}"
        )
    else:
        sentences.append("No cross-domain conflict pattern fired on this scenario.")
    sentences.append(
        f"The synthesizer merged the analyses into a single answer with a "
        f"{len(response['compliance_checklist'])}-step, deadline-stamped checklist."
    )
    sentences.append(
        "Every response is flagged for attorney review — the platform renders "
        "research, never legal advice."
    )
    trace = "cns-" + scenario
    return {"narration": " ".join(sentences), "trace_id": trace}


def _narrate_estate(scenario: str, seed: int) -> dict[str, Any]:
    run = demo_estate.EstateRoomEngine().run(scenario, seed=seed)
    finale = run["finale"]
    sentences: list[str] = []
    if scenario == "ct_estate_settlement":
        clocks = ", ".join(f"day {c['day']} ({c['clock_id']})" for c in run["timeline"])
        sentences.append(
            f"The executor's five statutory clocks were armed on day one: {clocks}."
        )
        sentences.append(
            "Dependency arrows keep the order honest — the inventory feeds the "
            "CT-706/NT, and no distribution can fire before the 150-day windows close."
        )
    elif scenario == "gst_dynasty_review":
        flag = run["grandfather_flag"]
        sentences.append(
            f"Three generations and {len(run['graph']['nodes'])} nodes were mapped, with "
            f"${flag['corpus_at_stake']:,} of corpus protected by the GST grandfather flag."
        )
        sentences.append(flag["at_risk_if"])
    else:
        totals = run["totals"]
        sentences.append(
            f"{len(run['assets'])} assets were stepped up to date-of-death value under "
            f"IRC § 1014, eliminating ${totals['unrealized_gain_eliminated']:,} of "
            "unrealized gain."
        )
        sentences.append(
            "The same appraisals do double duty as the 60-day inventory record."
        )
    sentences.append(finale["summary"])
    sentences.append(
        "Everything here is advisory and flagged for attorney review — "
        "fiduciary actions never execute autonomously."
    )
    return {"narration": " ".join(sentences), "trace_id": run["trace_id"]}


def _narrate_risk(scenario: str, seed: int) -> dict[str, Any]:
    run = demo_risk.RiskSentinelEngine().run(scenario, seed=seed)
    auto = next(e for e in run["escalations"] if e["kind"] == "auto_mitigated")
    veto = next(e for e in run["escalations"] if e["kind"] == "vetoed")
    sentences = [
        (
            f"{run['funnel']['events_sensed']} enterprise events landed on the 5×5 "
            f"severity×likelihood matrix; only two earned an escalation."
        ),
        (
            f"The first, on {auto['entity_id']}, was auto-mitigated under the "
            f"{auto['rule_id']} rule: {auto['mitigation']}"
        ),
        (
            f"The second, on {veto['entity_id']}, was VETOED under the "
            f"{veto['rule_id']} rule — {veto['detail']}"
        ),
        (
            f"The veto carries a full evidence chain and rollback token "
            f"{veto['rollback_token']}, mirroring the ACT-991 authorization pattern."
        ),
        "Same seed, same matrix, same two escalations — every time.",
    ]
    return {"narration": " ".join(sentences), "trace_id": run["trace_id"]}


def _narrate_nexus(scenario: str, seed: int) -> dict[str, Any]:
    run = demo_nexus.NexusRunEngine().run(scenario, seed=seed)
    capital_seg = next(s for s in run["divisions"] if s["division"] == "capital")
    risk_seg = next(s for s in run["divisions"] if s["division"] == "risk")
    blocked = capital_seg["verdict"].get("blocked") or {}
    veto = risk_seg["verdict"].get("veto") or {}
    order = " → ".join(seg["division"] for seg in run["divisions"])
    sentences = [
        (
            f"The trigger — {run['trigger']['title']} — opened trace "
            f"{run['nexus_trace_id']} and rippled through {order}."
        ),
        (
            f"Capital blocked variant {blocked.get('action_id', '—')} under the "
            f"{', '.join(blocked.get('blocked_by', []) or ['covenant_headroom'])} rule, and Risk "
            f"vetoed {veto.get('entity_id', '—')} under the {veto.get('rule_id', '—')} rule."
            if blocked or veto else
            "Each division rendered its own verdict on the shared trace."
        ),
        (
            "Counsel flagged the indemnity clause for attorney review, and the "
            "Estate lane recorded a governance ledger entry — restraint logged "
            "as a decision."
        ),
        (
            "Every division's verdict hangs off the single trace id, so the "
            "whole cascade replays from one provenance graph."
        ),
        f"{run['tagline']}",
    ]
    return {"narration": " ".join(sentences), "trace_id": run["nexus_trace_id"]}


_NARRATORS = {
    "signal": _narrate_signal,
    "capital": _narrate_capital,
    "counsel": _narrate_counsel,
    "estate": _narrate_estate,
    "risk": _narrate_risk,
    "nexus": _narrate_nexus,
}
