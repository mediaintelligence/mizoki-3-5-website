"""Decision Concierge — the Executive Briefing's guide agent, server side.

Three responsibilities, all stdlib:

1. **Allowlisted Q&A.** ``answer_question`` retrieves from a hard allowlist of
   product facts and a cached objection bank. There is no generative path: the
   concierge can only say what this file says, so it cannot invent pricing,
   certifications, or customer logos. Unknown questions get an honest fallback
   and are logged for human follow-up.
2. **Interaction memory.** ``record_event`` appends every guide interaction to
   a JSONL ledger (session id, stage, domain, role, event, payload) and
   ``summarize`` aggregates it — top objections, drop-off stage, suggestion
   acceptance, decision intents — so the briefing improves from real traffic.
3. **Boss exposure.** The runtime registers ``guide.answer`` and
   ``guide.memory_summary`` MCP tools over these functions, so the guide runs
   as a sub-agent surface under the Boss runtime.

Claim discipline (test-enforced in tests/test_briefing_guide.py): no
guarantees, no certification claims, no invented dollar figures, no pressure
language. The concierge suggests; the executive commits.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# The allowlist: every sentence the concierge may use in an answer.
# ---------------------------------------------------------------------------

PRODUCT_FACTS: list[dict[str, Any]] = [
    {
        "id": "dcp",
        "keywords": ["dcp", "decision control plane", "control plane", "govern", "autonomy", "autonomous", "control"],
        "answer": (
            "The Decision Control Plane is the governance layer every decision passes "
            "through: proposals carry evidence and a validation passport, risky moves "
            "route to a human gate, and every action is auditable and reversible by "
            "design. Autonomy is earned in stages — it is never assumed."
        ),
    },
    {
        "id": "validation",
        "keywords": ["validation", "passport", "val", "verify", "checks", "arbitration", "trust the numbers"],
        "answer": (
            "Every recommendation carries a validation passport — a battery of "
            "financial, statistical, causal, and policy checks that ran before "
            "anything reached you. A missing required check is a fail by "
            "construction; there is no way to skip the battery."
        ),
    },
    {
        "id": "cse",
        "keywords": ["counterfactual", "simulation", "cse", "what if", "scenario engine"],
        "answer": (
            "The Counterfactual Simulation Engine stress-tests a proposed move "
            "against the alternative worlds where you didn't make it — so the case "
            "you see includes what would likely have happened anyway."
        ),
    },
    {
        "id": "srpvdal",
        "keywords": ["srpvdal", "pipeline", "seven stage", "loop", "how does it work", "how it works"],
        "answer": (
            "Under the hood every decision runs the same seven-stage loop: Sense, "
            "Reason, Plan, Validate, Decide, Act, Learn. The live scenario in stage "
            "three of this briefing is that loop running for real — including the "
            "deliberate red block at Validate."
        ),
    },
    {
        "id": "two_track",
        "keywords": ["technical", "demo", "desks", "engineer", "deep dive", "deeper", "under the hood"],
        "answer": (
            "This briefing is the executive track. There is a parallel technical "
            "track — six live desks plus the Nexus boardroom at /demo — built for "
            "your operators and engineers to pressure-test the same platform."
        ),
    },
    {
        "id": "evidence",
        "keywords": ["evidence", "proof", "why should", "black box", "explain", "explainable"],
        "answer": (
            "The operating rule is: no evidence, no action. Every number on screen "
            "traces to a decision record with provenance, confidence, and the checks "
            "it passed — you can open the trace behind anything the platform proposes."
        ),
    },
    {
        "id": "desks",
        "keywords": ["desk", "hub", "which demo", "divisions", "capital", "nexus", "boardroom", "what can i see", "other demos", "signal factory"],
        "answer": (
            "Six live desks share one runtime: Signal (the marketing signal factory), "
            "Capital (treasury moves under a covenant guardrail), Counsel (four legal "
            "experts returning IRAC analyses), Estate (statutory timelines and dynasty "
            "graphs), Risk (the five-by-five matrix with one deliberate veto), and the "
            "Nexus boardroom, where one trigger ripples through every division under a "
            "single trace id. Signal and Capital are the deepest walkthroughs — start there."
        ),
    },
    {
        "id": "oracle_intent",
        "keywords": ["oracle", "intent", "anticipat", "latent", "in-market", "purchase", "predict", "before they"],
        "answer": (
            "ORACLE is the Signal division's anticipatory layer: consent-gated "
            "micro-signals score latent intent across four stages — awareness, "
            "consideration, in-market, purchase-imminent — as calibrated "
            "probabilities, never certainty. It runs observe-only by default, and "
            "promotion is gated on measured calibration and stable causal lift."
        ),
    },
    {
        "id": "replay_seed",
        "keywords": ["seed", "replay", "deterministic", "same numbers", "rerun", "remix", "reproduc", "random"],
        "answer": (
            "Every demo run is deterministic and seeded — replay the same seed and "
            "every number, gate decision, and veto lands identically. Change the seed "
            "and the desk remixes the scenario. That is the point: decisions you can "
            "re-run are decisions you can audit."
        ),
    },
    {
        "id": "pilot_path",
        "keywords": ["pilot", "get started", "next step", "trial", "proof of concept", "poc", "engage", "onboard", "sign up"],
        "answer": (
            "The path in is a scoped pilot: one domain, one decision loop, read-first "
            "connectors on a defined slice of data, and a defined exit. It runs "
            "alongside your current stack and reports its own lift. The contact page "
            "or the executive briefing's close step starts that conversation."
        ),
    },
    {
        "id": "boss_agent",
        "keywords": ["boss", "who are you", "what are you", "agent", "orchestrat", "docent", "narrat"],
        "answer": (
            "I'm the Boss agent — the orchestration layer this platform runs on. On "
            "these pages I work as a docent: I narrate live runs, answer from a "
            "vetted briefing pack, and log what I can't answer for human follow-up. "
            "In production the same layer coordinates the cells, tools, and "
            "governance gates you see in the demos."
        ),
    },
    {
        "id": "voice_output_only",
        "keywords": ["voice", "microphone", "listening", "audio", "speak", "hear me", "mute", "talk"],
        "answer": (
            "Voice here is output-only: I speak through your browser's speech "
            "synthesis and I never listen — no microphone, no audio capture, ever. "
            "You can mute me with the voice toggle, and the captions carry every word."
        ),
    },
]

OBJECTIONS: list[dict[str, Any]] = [
    {
        "id": "integration_risk",
        "keywords": ["integrat", "connect", "plug in", "our stack", "rip and replace", "migration", "implementation"],
        "answer": (
            "Integration is read-first: connectors normalize your existing systems "
            "into one canonical event envelope — nothing goes straight from a "
            "connector to an action, and nothing is ripped out. A pilot runs "
            "alongside your current stack, on a scoped slice of data."
        ),
    },
    {
        "id": "existing_bi",
        "keywords": ["bi", "dashboards", "looker", "tableau", "power bi", "already have", "reporting", "analytics team"],
        "answer": (
            "Keep your BI — it answers 'what happened'. This platform closes the "
            "loop after the dashboard: it proposes a decision, validates it, routes "
            "it through control, and measures what the action actually caused. It "
            "reads from the same stack your BI reads from."
        ),
    },
    {
        "id": "security",
        "keywords": ["security", "secure", "privacy", "data", "compliance", "gdpr", "pii", "who sees"],
        "answer": (
            "Security posture: consent-first ingestion, tenant isolation, "
            "IAM-locked services, encryption in transit, and a deploy pipeline that "
            "requires specific human approval for every production change. No audio "
            "capture, ever. Your security team can review the architecture in a "
            "technical deep-dive before any data moves."
        ),
    },
    {
        "id": "not_now",
        "keywords": ["not now", "later", "next quarter", "busy", "timing", "revisit", "wait"],
        "answer": (
            "Fair — timing is a real constraint. The one number worth taking with "
            "you is the exposure model from stage two: that is the approximate cost "
            "of each quarter of status quo, on your inputs. A board packet lets you "
            "schedule the decision without losing the analysis."
        ),
    },
    {
        "id": "budget_owner",
        "keywords": ["budget", "who pays", "owner", "sponsor", "procurement", "sign off", "approve this"],
        "answer": (
            "A pilot is sized for a single P&L owner to sponsor — one domain, one "
            "decision loop, a defined exit. If the budget conversation needs the "
            "CFO or the board, the board packet option packages the exposure model "
            "and pilot scope into that exact conversation."
        ),
    },
    {
        "id": "pricing",
        "keywords": ["price", "pricing", "cost of the", "how much", "license", "subscription"],
        "answer": (
            "Deliberately, this briefing carries no price list — pricing is scoped "
            "to the pilot: domain, data surface, and autonomy level. The pilot "
            "conversation sets it in one call, and pricing.html maps the tiers to "
            "the autonomy ladder without dollar figures."
        ),
    },
]

UNKNOWN_ANSWER = (
    "Good question — it isn't in my briefing pack, and I'd rather log it for a "
    "human follow-up than improvise an answer. It's recorded; the deep-dive or "
    "pilot conversation will open with it."
)

ALLOWED_EVENTS = {
    "guide_opened",
    "guide_collapsed",
    "guide_resumed",
    "suggestion_accepted",
    "question_asked",
    "objection_raised",
    "stage_changed",
    "signal_resolved",
    "decision_intent",
    "decision_confirmed",
    "guide_handoff",
}

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _score(text: str, keywords: list[str]) -> int:
    hay = " " + " ".join(_TOKEN_RE.findall(text.lower())) + " "
    score = 0
    for kw in keywords:
        if kw in hay:
            score += 2 if " " in kw else 1
    return score


def classify_question(question: str) -> tuple[str, str, dict[str, Any] | None]:
    """Return (kind, id, entry) — kind in {objection, fact, unknown}."""
    best: tuple[int, str, str, dict[str, Any] | None] = (0, "unknown", "none", None)
    for entry in OBJECTIONS:
        s = _score(question, entry["keywords"])
        if s > best[0]:
            best = (s, "objection", entry["id"], entry)
    for entry in PRODUCT_FACTS:
        s = _score(question, entry["keywords"])
        if s > best[0]:
            best = (s, "fact", entry["id"], entry)
    if best[0] == 0:
        return "unknown", "none", None
    return best[1], best[2], best[3]


def answer_question(question: str, domain: str = "", role: str = "") -> dict[str, Any]:
    kind, topic, entry = classify_question(question)
    if entry is None:
        return {"kind": "unknown", "topic": "none", "answer": UNKNOWN_ANSWER, "confidence": 0.0}
    confidence = 0.9 if kind == "objection" else 0.8
    return {"kind": kind, "topic": topic, "answer": entry["answer"], "confidence": confidence}


# ---------------------------------------------------------------------------
# Interaction memory
# ---------------------------------------------------------------------------

_MAX_STR = 400


def _clean(value: Any, limit: int = _MAX_STR) -> str:
    return str(value)[:limit] if isinstance(value, (str, int, float)) else ""


def record_event(
    path: Path,
    session_id: str,
    event: str,
    stage: str = "",
    domain: str = "",
    role: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if event not in ALLOWED_EVENTS:
        raise ValueError(f"unknown guide event: {event}")
    clean_payload: dict[str, str] = {}
    for key, value in (payload or {}).items():
        if isinstance(key, str) and len(clean_payload) < 8:
            clean_payload[key[:40]] = _clean(value)
    row = {
        "ts": time.time(),
        "session": _clean(session_id, 64) or uuid.uuid4().hex[:12],
        "event": event,
        "stage": _clean(stage, 24),
        "domain": _clean(domain, 24),
        "role": _clean(role, 24),
        "payload": clean_payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _load(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def summarize(path: Path) -> dict[str, Any]:
    rows = _load(path)
    sessions: dict[str, dict[str, Any]] = {}
    events: dict[str, int] = {}
    objections: dict[str, int] = {}
    questions: dict[str, int] = {}
    intents: dict[str, int] = {}
    last_stage: dict[str, str] = {}
    for row in rows:
        sid = row.get("session", "?")
        sessions.setdefault(sid, {"first": row.get("ts"), "events": 0})
        sessions[sid]["events"] += 1
        event = row.get("event", "?")
        events[event] = events.get(event, 0) + 1
        payload = row.get("payload") or {}
        if event == "objection_raised":
            key = payload.get("objection", "unknown")
            objections[key] = objections.get(key, 0) + 1
        if event == "question_asked":
            key = payload.get("topic", "none")
            questions[key] = questions.get(key, 0) + 1
        if event in ("decision_intent", "decision_confirmed"):
            key = payload.get("intent", "unknown")
            intents[f"{event}:{key}"] = intents.get(f"{event}:{key}", 0) + 1
        if row.get("stage"):
            last_stage[sid] = row["stage"]
    drop_off: dict[str, int] = {}
    for stage in last_stage.values():
        drop_off[stage] = drop_off.get(stage, 0) + 1
    opened = events.get("guide_opened", 0)
    accepted = events.get("suggestion_accepted", 0)
    return {
        "sessions": len(sessions),
        "events_total": len(rows),
        "events_by_type": dict(sorted(events.items(), key=lambda kv: -kv[1])),
        "objections_ranked": dict(sorted(objections.items(), key=lambda kv: -kv[1])),
        "question_topics": dict(sorted(questions.items(), key=lambda kv: -kv[1])),
        "decision_intents": intents,
        "last_stage_by_session": drop_off,
        "suggestion_acceptance": round(accepted / opened, 3) if opened else 0.0,
    }
