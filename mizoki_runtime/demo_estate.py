"""Estate Room demo engine — statutory clocks, dynasty graphs, basis step-up.

Deterministic, stdlib-only simulation of the MIZ OKI Estate division
(Counsel pattern: request/response, no SSE). Three scenarios:

- ``ct_estate_settlement`` — the five Connecticut statutory clocks as an
  interactive timeline with dependency arrows and deadline badges.
- ``gst_dynasty_review`` — a three-generation family/trust graph with
  per-node transfer-tax exposure and the GST grandfather flag.
- ``basis_step_up`` — an asset table with pre/post-death basis under
  IRC § 1014 and deterministic seeded valuations.

COMPLIANCE (non-negotiable): every response carries
``flagged_for_review: True`` and the exact unauthorized-practice warning.
Authorities are imported from the shared Counsel corpus, never duplicated.
"""

from __future__ import annotations

import hashlib
import json
import random
from functools import lru_cache
from typing import Any

from .demo_counsel import ALLOWED_AUTHORITY_CITATIONS, UNAUTHORIZED_PRACTICE_WARNING
from .demo_signal import DEFAULT_SEED

__all__ = [
    "SCENARIOS",
    "DEFAULT_SEED",
    "STATUTORY_CLOCK_IDS",
    "EstateRoomEngine",
    "list_scenarios",
]

# The five Connecticut statutory clocks — every ct_estate_settlement run
# must contain all five (tested invariant).
STATUTORY_CLOCK_IDS = (
    "filing_30",
    "inventory_60",
    "creditor_150",
    "elective_150",
    "ct706_183",
)

SCENARIOS: dict[str, dict[str, Any]] = {
    "ct_estate_settlement": {
        "id": "ct_estate_settlement",
        "name": "CT estate settlement — the five statutory clocks",
        "description": (
            "A Connecticut decedent's estate opens and the executor's five "
            "statutory clocks start ticking: 30-day filing, 60-day inventory, "
            "150-day creditor bar, 150-day elective share, and the 183-day "
            "CT-706/NT. The timeline shows every dependency."
        ),
        "widget": "statutory_timeline",
    },
    "gst_dynasty_review": {
        "id": "gst_dynasty_review",
        "name": "GST dynasty review — three generations, one grandfather flag",
        "description": (
            "A 1982 grandfathered dynasty structure is mapped as a "
            "three-generation family/trust graph with per-node transfer-tax "
            "exposure — and the GST grandfather flag that any modification "
            "puts at risk."
        ),
        "widget": "dynasty_graph",
    },
    "basis_step_up": {
        "id": "basis_step_up",
        "name": "Basis step-up — IRC § 1014 at date of death",
        "description": (
            "The estate's appreciated assets get their basis stepped up to "
            "date-of-death value under IRC § 1014 — the table shows exactly "
            "how much unrealized gain is eliminated, asset by asset."
        ),
        "widget": "basis_table",
    },
}


def list_scenarios() -> list[dict[str, Any]]:
    return [
        {"id": s["id"], "name": s["name"], "description": s["description"], "widget": s["widget"]}
        for s in SCENARIOS.values()
    ]


def _require_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"unknown scenario: {scenario_id!r} (expected one of: {known})")
    return SCENARIOS[scenario_id]


def _trace_id(scenario_id: str, seed: int) -> str:
    return "est-" + hashlib.sha256(f"{scenario_id}:{seed}".encode()).hexdigest()[:12]


def _authority(citation: str, note: str) -> dict[str, str]:
    if citation not in ALLOWED_AUTHORITY_CITATIONS:
        raise ValueError(f"citation not in shared corpus: {citation!r}")
    return {"citation": citation, "note": note}


# --------------------------------------------------------------------------
# Scenario builders (all deterministic for a given seed)
# --------------------------------------------------------------------------

def _build_ct_estate_settlement(rng: random.Random) -> dict[str, Any]:
    gross_estate = 100_000 * rng.randint(38, 92)  # $3.8M–$9.2M
    timeline = [
        {
            "clock_id": "filing_30",
            "label": "Petition + original will filed with the Probate Court",
            "day": 30,
            "badge": "day 30",
            "depends_on": [],
            "authority": _authority("CGS § 45a-251", "execution and proof of wills"),
            "detail": (
                "The application and original will go to the Probate Court for "
                "the decedent's domicile district within 30 days of death."
            ),
        },
        {
            "clock_id": "inventory_60",
            "label": "Inventory of estate assets at date-of-death values",
            "day": 60,
            "badge": "day 60 of appointment",
            "depends_on": ["filing_30"],
            "authority": None,
            "detail": (
                "The executor files the inventory within two months of "
                "appointment — the same appraisals later document the "
                "IRC § 1014 basis step-up."
            ),
        },
        {
            "clock_id": "creditor_150",
            "label": "Creditor claim window closes",
            "day": 150,
            "badge": "day 150",
            "depends_on": ["filing_30"],
            "authority": None,
            "detail": (
                "Newspaper notice opens the 150-day creditor-claim period; "
                "distributions before it closes risk clawback."
            ),
        },
        {
            "clock_id": "elective_150",
            "label": "Spousal elective-share window closes",
            "day": 150,
            "badge": "day 150",
            "depends_on": ["filing_30"],
            "authority": _authority("CGS § 45a-436", "spousal elective share; 150-day election"),
            "detail": (
                "The surviving spouse has 150 days from the executor's "
                "appointment to elect the statutory one-third share against "
                "the will."
            ),
        },
        {
            "clock_id": "ct706_183",
            "label": "CT-706/NT estate tax return filed",
            "day": 183,
            "badge": "6 months",
            "depends_on": ["inventory_60"],
            "authority": _authority("CGS § 12-391", "CT estate tax; six-month return"),
            "detail": (
                "Every Connecticut estate — taxable or not — files the return "
                "within six months; the court cannot close the file without it."
            ),
        },
    ]
    ledger = [
        {
            "entry_id": f"led_{index + 1:02d}",
            "clock_id": clock["clock_id"],
            "recorded_day": max(1, clock["day"] - rng.randint(3, 12)),
            "note": f"Calendar entry armed for {clock['label'].lower()}.",
        }
        for index, clock in enumerate(timeline)
    ]
    return {
        "estate": {
            "decedent": "Eleanor Voss",
            "domicile": "Fairfield Probate District",
            "gross_estate": gross_estate,
            "has_surviving_spouse": True,
            "executor": "named in will, appointment accepted",
        },
        "timeline": timeline,
        "governance_ledger": ledger,
        "authorities": [
            _authority("CGS § 45a-251", "execution and proof of wills"),
            _authority("CGS § 45a-436", "spousal elective share; 150-day election"),
            _authority("CGS § 12-391", "CT estate tax; six-month return"),
            _authority("IRC § 1014", "basis step-up at death"),
        ],
        "finale": {
            "headline": "Five clocks calendared on day one — the executor is judgment-proof.",
            "summary": (
                "All five statutory clocks are armed with dependency-aware "
                "reminders; no distribution can fire before the 150-day "
                "creditor and elective-share windows close."
            ),
            "key_numbers": [
                {"label": "gross estate", "value": f"${gross_estate:,}"},
                {"label": "statutory clocks", "value": "5"},
                {"label": "earliest safe distribution", "value": "day 151"},
            ],
        },
    }


def _build_gst_dynasty_review(rng: random.Random) -> dict[str, Any]:
    trust_corpus = 1_000_000 * rng.randint(18, 42)  # $18M–$42M
    g2_exposure = round(trust_corpus * 0.40)
    g3_exposure = round(trust_corpus * 0.40 * 0.40)
    nodes = [
        {"node_id": "g1_settlor", "kind": "person", "label": "Settlor (G1, dec.)",
         "generation": 1, "transfer_tax_exposure": 0, "gst_grandfathered": None,
         "note": "Funded the 1982 trust; no additions since."},
        {"node_id": "dynasty_trust", "kind": "trust", "label": "1982 Dynasty Trust",
         "generation": 1, "transfer_tax_exposure": 0, "gst_grandfathered": True,
         "note": "Irrevocable on Sept 25, 1985 — grandfathered from GST."},
        {"node_id": "g2_child_a", "kind": "person", "label": "Child A (G2)",
         "generation": 2, "transfer_tax_exposure": g2_exposure, "gst_grandfathered": None,
         "note": "Estate-tax exposure if corpus vests outright at G2."},
        {"node_id": "g2_child_b", "kind": "person", "label": "Child B (G2)",
         "generation": 2, "transfer_tax_exposure": g2_exposure, "gst_grandfathered": None,
         "note": "Same exposure profile as Child A."},
        {"node_id": "g3_gc_a", "kind": "person", "label": "Grandchild A (G3)",
         "generation": 3, "transfer_tax_exposure": g3_exposure, "gst_grandfathered": None,
         "note": "Skip person — GST attaches here if the grandfather is lost."},
        {"node_id": "g3_gc_b", "kind": "person", "label": "Grandchild B (G3)",
         "generation": 3, "transfer_tax_exposure": g3_exposure, "gst_grandfathered": None,
         "note": "Skip person — GST attaches here if the grandfather is lost."},
    ]
    edges = [
        {"from": "g1_settlor", "to": "dynasty_trust", "relation": "settled"},
        {"from": "dynasty_trust", "to": "g2_child_a", "relation": "income_beneficiary"},
        {"from": "dynasty_trust", "to": "g2_child_b", "relation": "income_beneficiary"},
        {"from": "g2_child_a", "to": "g3_gc_a", "relation": "parent_of"},
        {"from": "g2_child_b", "to": "g3_gc_b", "relation": "parent_of"},
        {"from": "dynasty_trust", "to": "g3_gc_a", "relation": "remainder_beneficiary"},
        {"from": "dynasty_trust", "to": "g3_gc_b", "relation": "remainder_beneficiary"},
    ]
    return {
        "graph": {"nodes": nodes, "edges": edges},
        "grandfather_flag": {
            "grandfathered": True,
            "at_risk_if": (
                "Any modification that shifts a beneficial interest to a "
                "lower generation or extends vesting terminates the "
                "exemption for the entire trust."
            ),
            "gst_rate_if_lost": 0.40,
            "corpus_at_stake": trust_corpus,
        },
        "authorities": [
            _authority("IRC § 2601", "GST tax; grandfathered-trust exemption"),
            _authority("Treas. Reg. § 26.2601-1(b)(4)", "modification safe harbors"),
            _authority("IRC § 2001", "transfer-tax rate schedule"),
        ],
        "finale": {
            "headline": "The grandfather flag is worth more than any modification.",
            "summary": (
                "Losing the 1985 grandfather would expose the full corpus to "
                "a flat 40% GST at each skip — the graph makes the cost of a "
                "careless amendment visible before anyone drafts one."
            ),
            "key_numbers": [
                {"label": "trust corpus", "value": f"${trust_corpus:,}"},
                {"label": "GST rate if lost", "value": "40%"},
                {"label": "generations mapped", "value": "3"},
            ],
        },
    }


def _build_basis_step_up(rng: random.Random) -> dict[str, Any]:
    specs = (
        ("asset_brokerage", "Brokerage portfolio", "2003", 8, 26),
        ("asset_residence", "Primary residence, Greenwich", "1998", 6, 21),
        ("asset_cre", "Commercial building, Stamford", "2009", 11, 24),
        ("asset_closely_held", "Closely-held business interest", "1991", 4, 19),
        ("asset_art", "Art collection", "2012", 2, 7),
    )
    assets = []
    total_eliminated = 0
    for asset_id, label, acquired, low, high in specs:
        dod_value = 100_000 * rng.randint(low * 2, high * 2)
        cost_basis = round(dod_value * rng.uniform(0.18, 0.55), -3)
        eliminated = int(dod_value - cost_basis)
        total_eliminated += eliminated
        assets.append({
            "asset_id": asset_id,
            "label": label,
            "acquired": acquired,
            "cost_basis": int(cost_basis),
            "date_of_death_value": dod_value,
            "stepped_basis": dod_value,
            "unrealized_gain_eliminated": eliminated,
        })
    return {
        "assets": assets,
        "totals": {
            "date_of_death_value": sum(a["date_of_death_value"] for a in assets),
            "unrealized_gain_eliminated": total_eliminated,
        },
        "authorities": [
            _authority("IRC § 1014", "basis step-up at death"),
            _authority("IRC § 2001", "federal estate tax"),
        ],
        "finale": {
            "headline": "Appraise once, use twice — inventory and § 1014 basis.",
            "summary": (
                "Date-of-death appraisals gathered for the 60-day inventory "
                "double as the IRC § 1014 basis record, eliminating "
                f"${total_eliminated:,} of unrealized gain in one pass."
            ),
            "key_numbers": [
                {"label": "assets stepped up", "value": str(len(assets))},
                {"label": "gain eliminated", "value": f"${total_eliminated:,}"},
                {"label": "appraisals reused", "value": "inventory + basis"},
            ],
        },
    }


_BUILDERS = {
    "ct_estate_settlement": _build_ct_estate_settlement,
    "gst_dynasty_review": _build_gst_dynasty_review,
    "basis_step_up": _build_basis_step_up,
}


@lru_cache(maxsize=64)
def _cached_run_json(scenario_id: str, seed: int) -> str:
    scenario = _require_scenario(scenario_id)
    rng = random.Random(seed)
    body = _BUILDERS[scenario_id](rng)
    run = {
        "trace_id": _trace_id(scenario_id, seed),
        "scenario": scenario_id,
        "scenario_name": scenario["name"],
        "widget": scenario["widget"],
        "seed": seed,
        **body,
        "flagged_for_review": True,
        "unauthorized_practice_warning": UNAUTHORIZED_PRACTICE_WARNING,
    }
    return json.dumps(run)


class EstateRoomEngine:
    """Counsel-pattern engine: deterministic request/response runs."""

    def run(self, scenario_id: str, seed: int = DEFAULT_SEED) -> dict[str, Any]:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")
        _require_scenario(scenario_id)
        return json.loads(_cached_run_json(scenario_id, seed))
