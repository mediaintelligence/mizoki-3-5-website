"""Counsel Room demo engine — Mixture-of-Legal-Experts (MoLE).

A legal scenario fans out to 4 domain experts (Connecticut / Trust / Estate /
Tax), each returns an IRAC analysis, and a synthesizer reconciles them and
surfaces cross-domain conflicts.

Everything is scripted and deterministic: no external calls, no LLMs, no new
dependencies. The authority corpus mirrors the production
``legal_expertise_integration.py`` corpus.

COMPLIANCE (non-negotiable): every response carries
``flagged_for_review: True`` and an ``unauthorized_practice_warning``.
"""

from __future__ import annotations

import re
from typing import Any

__all__ = [
    "EXPERTS",
    "ALLOWED_AUTHORITY_CITATIONS",
    "UNAUTHORIZED_PRACTICE_WARNING",
    "MAX_QUERY_LENGTH",
    "ScenarioLibrary",
    "MixtureRouter",
    "ConflictDetector",
    "LegalSynthesizer",
    "list_scenarios",
]

MAX_QUERY_LENGTH = 500

UNAUTHORIZED_PRACTICE_WARNING = (
    "This is AI-augmented legal research, not legal advice. Engage a "
    "Connecticut-licensed attorney before acting on any output."
)

EXPERTS = ("ct_law", "trust_law", "estate_law", "tax_law")

EXPERT_LABELS = {
    "ct_law": "Connecticut Law",
    "trust_law": "Trust Law",
    "estate_law": "Estate Law",
    "tax_law": "Tax Law",
}

# The only citations any expert may emit (mirrors the production corpus).
ALLOWED_AUTHORITY_CITATIONS = frozenset({
    "CGS § 45a-499n",
    "CGS § 45a-499o",
    "CGS § 45a-487a",
    "CGS § 45a-251",
    "CGS § 45a-436",
    "CGS § 12-391",
    "CGS § 12-642",
    "CGS § 12-701",
    "UTC § 411",
    "UTC § 801",
    "UTC § 802",
    "Restatement (Third) of Trusts",
    "IRC § 2001",
    "IRC § 2010",
    "IRC § 2503(b)",
    "IRC § 2601",
    "IRC §§ 2036–2038",
    "IRC § 1014",
    "Treas. Reg. § 26.2601-1(b)(4)",
    "Crummey v. Commissioner",
    "North Carolina Dept. of Revenue v. Kaestner",
})


# --------------------------------------------------------------------------
# 2.1 ScenarioLibrary
# --------------------------------------------------------------------------

_SCENARIOS: dict[str, dict[str, Any]] = {
    "trust_modification_gst": {
        "id": "trust_modification_gst",
        "title": (
            "Modify an irrevocable CT trust by beneficiary consent — trust "
            "has grandfathered GST status."
        ),
        "description": (
            "All beneficiaries of a 1982 irrevocable Connecticut trust want "
            "to consent to a modification. The trust has never had additions "
            "and enjoys grandfathered GST-exempt status."
        ),
        "keywords": (
            "modify", "modification", "change", "amend", "irrevocable",
            "trust", "beneficiary", "beneficiaries", "consent", "gst",
            "grandfathered", "grandfather", "generation", "skipping",
            "connecticut",
        ),
    },
    "ct_probate_opening": {
        "id": "ct_probate_opening",
        "title": (
            "Open probate for a CT decedent — executor duties and statutory "
            "deadlines."
        ),
        "description": (
            "A Connecticut resident has died with a will. The named executor "
            "needs the opening sequence, the statutory clock, and the "
            "elective-share exposure mapped."
        ),
        "keywords": (
            "probate", "open", "opening", "decedent", "executor", "estate",
            "deadline", "deadlines", "inventory", "creditor", "creditors",
            "elective", "share", "death", "died", "will", "holographic",
            "handwritten", "witness", "witnesses",
        ),
    },
    "crummey_annual_gift": {
        "id": "crummey_annual_gift",
        "title": (
            "Make annual exclusion gifts to an irrevocable trust with "
            "Crummey powers."
        ),
        "description": (
            "A settlor wants this year's annual-exclusion gifts to land "
            "inside an insurance trust with Crummey withdrawal rights — "
            "notices, Form 709, and CT-709 mechanics included."
        ),
        "keywords": (
            "crummey", "annual", "exclusion", "gift", "gifts", "withdrawal",
            "notice", "notices", "709", "ct-709", "present", "interest",
            "insurance",
        ),
    },
}


class ScenarioLibrary:
    """Scripted scenarios plus free-text routing via keyword token overlap."""

    @staticmethod
    def get(scenario_id: str) -> dict[str, Any]:
        if scenario_id not in _SCENARIOS:
            known = ", ".join(sorted(_SCENARIOS))
            raise ValueError(f"unknown scenario_id: {scenario_id!r} (expected one of: {known})")
        return _SCENARIOS[scenario_id]

    @staticmethod
    def all() -> list[dict[str, Any]]:
        return list(_SCENARIOS.values())

    @staticmethod
    def match_free_text(text: str) -> tuple[str, float]:
        """Return (scenario_id, match_score). Always returns the best scenario."""
        tokens = set(re.findall(r"[a-z0-9\-]+", (text or "").lower()))
        best_id = next(iter(_SCENARIOS))
        best_score = -1.0
        for scenario_id, scenario in _SCENARIOS.items():
            keywords = set(scenario["keywords"])
            overlap = len(tokens & keywords)
            score = overlap / max(1, len(keywords))
            if overlap > 0:
                score += overlap * 0.1  # weight absolute overlap over ratio
            if score > best_score:
                best_id, best_score = scenario_id, score
        return best_id, round(max(best_score, 0.0), 4)


def list_scenarios() -> list[dict[str, Any]]:
    return [
        {"id": s["id"], "title": s["title"], "description": s["description"]}
        for s in _SCENARIOS.values()
    ]


# --------------------------------------------------------------------------
# 2.2 MixtureRouter
# --------------------------------------------------------------------------

_ROUTING: dict[str, list[dict[str, Any]]] = {
    "trust_modification_gst": [
        {"expert": "ct_law", "relevance": 0.94,
         "rationale": "Modification authority lives in the Connecticut UTC (CGS § 45a-499n/-499o)."},
        {"expert": "trust_law", "relevance": 0.91,
         "rationale": "Material-purpose doctrine and fiduciary duties govern whether consent suffices."},
        {"expert": "tax_law", "relevance": 0.88,
         "rationale": "Grandfathered GST-exempt status is at risk under Treas. Reg. § 26.2601-1(b)(4)."},
        {"expert": "estate_law", "relevance": 0.42,
         "rationale": "No probate estate is open; estate administration is peripheral here."},
    ],
    "ct_probate_opening": [
        {"expert": "estate_law", "relevance": 0.95,
         "rationale": "Executor duties, inventory, creditor claims, and accountings are core estate administration."},
        {"expert": "ct_law", "relevance": 0.92,
         "rationale": "Connecticut Probate Court procedure and statutory deadlines control the sequence."},
        {"expert": "tax_law", "relevance": 0.58,
         "rationale": "CT estate tax (CGS § 12-391), federal portability, and basis step-up need calendaring."},
        {"expert": "trust_law", "relevance": 0.44,
         "rationale": "No inter vivos trust is in play unless a pour-over surfaces during inventory."},
    ],
    "crummey_annual_gift": [
        {"expert": "tax_law", "relevance": 0.95,
         "rationale": "Present-interest qualification under IRC § 2503(b) and Crummey doctrine is the crux."},
        {"expert": "trust_law", "relevance": 0.90,
         "rationale": "Trustee notice duties and withdrawal-power mechanics are fiduciary questions."},
        {"expert": "ct_law", "relevance": 0.72,
         "rationale": "Connecticut layers its own gift tax (CGS § 12-642) and CT-709 filing on top."},
        {"expert": "estate_law", "relevance": 0.48,
         "rationale": "Estate inclusion is a downstream concern; no administration is pending."},
    ],
}


class MixtureRouter:
    DEFAULT_TOP_K = 3
    CONSULT_FLOOR = 0.5

    @classmethod
    def route(cls, scenario: dict[str, Any] | str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
        scenario_id = scenario if isinstance(scenario, str) else scenario["id"]
        ScenarioLibrary.get(scenario_id)
        routed = []
        entries = sorted(_ROUTING[scenario_id], key=lambda item: item["relevance"], reverse=True)
        for rank, entry in enumerate(entries):
            consulted = rank < top_k and entry["relevance"] >= cls.CONSULT_FLOOR
            routed.append({
                "expert": entry["expert"],
                "expert_label": EXPERT_LABELS[entry["expert"]],
                "relevance": entry["relevance"],
                "rationale": entry["rationale"],
                "consulted": consulted,
            })
        return routed


# --------------------------------------------------------------------------
# 2.3 Expert analyzers (scripted IRAC — the centerpiece of the demo)
# --------------------------------------------------------------------------

_ANALYSES: dict[str, dict[str, dict[str, Any]]] = {
    "trust_modification_gst": {
        "ct_law": {
            "expert": "ct_law",
            "irac": {
                "issue": (
                    "Whether an irrevocable Connecticut trust may be modified by "
                    "beneficiary consent under the Connecticut Uniform Trust Code, "
                    "and what procedural path that modification must take."
                ),
                "rule": (
                    "CGS § 45a-499n permits modification or termination of a "
                    "noncharitable irrevocable trust upon consent: with the settlor "
                    "and all beneficiaries consenting, even if inconsistent with a "
                    "material purpose; without the settlor, the court must find the "
                    "modification is not inconsistent with a material purpose of the "
                    "trust. CGS § 45a-499o separately allows modification for "
                    "unanticipated circumstances, and CGS § 45a-487a authorizes "
                    "binding nonjudicial settlement agreements on matters a court "
                    "could approve."
                ),
                "application": (
                    "This 1982 trust predates the CTUTC but the code applies to "
                    "trusts whenever created. If the settlor is deceased or will not "
                    "join, the beneficiaries need a Probate Court finding that the "
                    "proposed change does not defeat a material purpose — a "
                    "spendthrift provision is presumptive evidence of one. A "
                    "nonjudicial settlement agreement under CGS § 45a-487a can reach "
                    "administrative terms without court involvement."
                ),
                "conclusion": (
                    "State law very likely permits the consent modification, either "
                    "through court approval under CGS § 45a-499n or an NJSA limited "
                    "to administrative matters. State-law validity, however, says "
                    "nothing about the federal GST consequences — that risk is "
                    "assessed separately by the tax expert."
                ),
            },
            "authorities": [
                {"citation": "CGS § 45a-499n", "note": "modification by consent (CTUTC)"},
                {"citation": "CGS § 45a-499o", "note": "modification for unanticipated circumstances"},
                {"citation": "CGS § 45a-487a", "note": "nonjudicial settlement agreements"},
            ],
            "confidence": 0.92,
        },
        "trust_law": {
            "expert": "trust_law",
            "irac": {
                "issue": (
                    "Whether the proposed consent modification is consistent with "
                    "the trust's material purpose, and what duties the trustee owes "
                    "while the beneficiaries pursue it."
                ),
                "rule": (
                    "UTC § 411 conditions non-settlor consent modifications on the "
                    "modification not being inconsistent with a material purpose of "
                    "the trust; the Restatement (Third) of Trusts frames material "
                    "purpose as a purpose of particular significance to the settlor's "
                    "plan. Throughout, the trustee remains bound by the duty of good "
                    "faith administration under UTC § 801 and the duty of loyalty "
                    "under UTC § 802."
                ),
                "application": (
                    "A modification that merely updates administrative provisions or "
                    "trustee succession rarely offends a material purpose; one that "
                    "reshapes beneficial interests among generations very often does. "
                    "The trustee should stay neutral, disclose fully to all qualified "
                    "beneficiaries, and avoid advocating an outcome that favors one "
                    "class of beneficiaries over another."
                ),
                "conclusion": (
                    "Doctrinally the consent path is open, but the further the "
                    "modification reaches into dispositive terms, the weaker the "
                    "material-purpose footing becomes — and dispositive changes are "
                    "precisely the ones that endanger the GST grandfather. Keep the "
                    "instrument's dispositive skeleton intact."
                ),
            },
            "authorities": [
                {"citation": "UTC § 411", "note": "modification by consent; material-purpose limit"},
                {"citation": "UTC § 801", "note": "duty of good-faith administration"},
                {"citation": "UTC § 802", "note": "duty of loyalty"},
                {"citation": "Restatement (Third) of Trusts", "note": "material-purpose doctrine"},
            ],
            "confidence": 0.89,
        },
        "tax_law": {
            "expert": "tax_law",
            "irac": {
                "issue": (
                    "Whether modifying a trust that was irrevocable on September 25, "
                    "1985 terminates its grandfathered exemption from the "
                    "generation-skipping transfer tax."
                ),
                "rule": (
                    "IRC § 2601 imposes the GST tax, but trusts irrevocable on "
                    "September 25, 1985 with no later additions are grandfathered. "
                    "Treas. Reg. § 26.2601-1(b)(4) provides safe harbors: a "
                    "modification keeps the exemption only if it does not shift a "
                    "beneficial interest to a beneficiary in a lower generation and "
                    "does not extend the time for vesting beyond the perpetuities "
                    "period measured from the original instrument."
                ),
                "application": (
                    "A beneficiary-consent modification of dispositive terms is "
                    "exactly the fact pattern the regulation polices. If the change "
                    "shifts value toward grandchildren or stretches vesting, the "
                    "entire trust loses grandfather protection — exposing future "
                    "distributions to a flat 40% GST tax computed with IRC § 2001 "
                    "rates. Administrative-only changes fit comfortably within the "
                    "safe harbor."
                ),
                "conclusion": (
                    "Do not execute the modification before a written GST analysis "
                    "concludes it fits Treas. Reg. § 26.2601-1(b)(4). If any "
                    "dispositive shift is wanted, model the cost of losing the "
                    "exemption first — this is the controlling risk in the entire "
                    "engagement."
                ),
            },
            "authorities": [
                {"citation": "IRC § 2601", "note": "GST tax; grandfathered-trust exemption"},
                {"citation": "Treas. Reg. § 26.2601-1(b)(4)", "note": "modification safe harbors"},
                {"citation": "IRC § 2001", "note": "transfer-tax rate schedule"},
            ],
            "confidence": 0.93,
        },
    },
    "ct_probate_opening": {
        "estate_law": {
            "expert": "estate_law",
            "irac": {
                "issue": (
                    "What the named executor must do — and by when — to open and "
                    "administer a Connecticut decedent's probate estate without "
                    "personal exposure."
                ),
                "rule": (
                    "The will must be proved and admitted under CGS § 45a-251, with "
                    "the application customarily filed within 30 days of death. The "
                    "executor then marshals assets, files the inventory within two "
                    "months of appointment, administers the 150-day creditor-claim "
                    "window, and accounts before distribution. The surviving spouse's "
                    "statutory share under CGS § 45a-436 must be protected until the "
                    "election window closes."
                ),
                "application": (
                    "The opening sequence is: petition and will to the Probate Court "
                    "(day 30), acceptance of appointment and any bond, newspaper "
                    "notice starting the 150-day creditor period, inventory by day 60 "
                    "of appointment, and the elective-share watch — the spouse has "
                    "150 days from the executor's appointment to elect against the "
                    "will. Distributions before day 150 risk clawback."
                ),
                "conclusion": (
                    "Calendar five clocks on day one: 30-day filing, 60-day "
                    "inventory, 150-day creditor bar, 150-day elective share, and "
                    "the 6-month estate-tax return. An executor who respects those "
                    "clocks and accounts before distributing is essentially "
                    "judgment-proof; one who distributes early is a guarantor."
                ),
            },
            "authorities": [
                {"citation": "CGS § 45a-251", "note": "execution and proof of wills"},
                {"citation": "CGS § 45a-436", "note": "spousal elective share; 150-day election"},
            ],
            "confidence": 0.91,
        },
        "ct_law": {
            "expert": "ct_law",
            "irac": {
                "issue": (
                    "Which Connecticut Probate Court has jurisdiction, and what "
                    "procedural steps Connecticut law layers onto the executor's "
                    "opening sequence."
                ),
                "rule": (
                    "Venue lies in the probate district where the decedent was "
                    "domiciled. The will is admitted under CGS § 45a-251's two-witness "
                    "standard, and Connecticut's estate tax regime under CGS § 12-391 "
                    "requires a return in every estate — taxable or not — before the "
                    "court will close the file."
                ),
                "application": (
                    "Connecticut practice runs the estate-tax return through the "
                    "Probate Court itself: the CT-706/NT for nontaxable estates is "
                    "filed with the court within six months of death, and the court's "
                    "statutory fee is computed from it. Out-of-state wills are "
                    "admissible if validly executed where made, but a will "
                    "handwritten and unwitnessed in Connecticut fails § 45a-251."
                ),
                "conclusion": (
                    "File in the domicile district, prove the will under § 45a-251, "
                    "and treat the six-month CT-706/NT as a hard gate — the estate "
                    "cannot close without it. The 150-day and 60-day clocks the "
                    "estate expert flagged run concurrently, not sequentially."
                ),
            },
            "authorities": [
                {"citation": "CGS § 45a-251", "note": "will formalities; two witnesses"},
                {"citation": "CGS § 12-391", "note": "CT estate tax; six-month return"},
            ],
            "confidence": 0.90,
        },
        "tax_law": {
            "expert": "tax_law",
            "irac": {
                "issue": (
                    "What estate-tax and income-tax filings the executor must make, "
                    "and which elections should be preserved while the estate is "
                    "open."
                ),
                "rule": (
                    "CGS § 12-391 requires the Connecticut estate tax return within "
                    "six months of death. Federally, IRC § 2001 imposes the estate "
                    "tax, IRC § 2010 supplies the unified credit and the portability "
                    "election for the deceased spouse's unused exclusion, and IRC "
                    "§ 1014 steps up basis in included assets to date-of-death value."
                ),
                "application": (
                    "Even a clearly nontaxable estate files the CT return inside six "
                    "months. Whether to file a federal Form 706 solely to elect "
                    "portability is a genuine decision point when a surviving spouse "
                    "exists — the election is cheap now and impossible later. The "
                    "§ 1014 step-up should be documented with date-of-death "
                    "appraisals gathered during the 60-day inventory work."
                ),
                "conclusion": (
                    "Calendar the CT six-month return immediately, decide the "
                    "portability question deliberately rather than by default, and "
                    "let the inventory appraisals do double duty as basis "
                    "documentation under IRC § 1014."
                ),
            },
            "authorities": [
                {"citation": "CGS § 12-391", "note": "CT estate tax return deadline"},
                {"citation": "IRC § 2010", "note": "unified credit; portability election"},
                {"citation": "IRC § 1014", "note": "basis step-up at death"},
                {"citation": "IRC § 2001", "note": "federal estate tax"},
            ],
            "confidence": 0.88,
        },
    },
    "crummey_annual_gift": {
        "tax_law": {
            "expert": "tax_law",
            "irac": {
                "issue": (
                    "Whether this year's gifts to the irrevocable trust qualify for "
                    "the federal annual exclusion, and what filings the gifts "
                    "trigger."
                ),
                "rule": (
                    "IRC § 2503(b) grants the annual exclusion only for gifts of a "
                    "present interest. Crummey v. Commissioner holds that a "
                    "beneficiary's unrestricted, if temporary, right to withdraw a "
                    "contribution converts an otherwise future interest into a "
                    "present one. Retained strings in the settlor invite estate "
                    "inclusion under IRC §§ 2036–2038, and Connecticut layers its "
                    "own gift tax under CGS § 12-642."
                ),
                "application": (
                    "Each contribution must be matched by a genuine withdrawal "
                    "right: written notice to every power holder, a reasonable "
                    "window (30 days is customary), and no side agreement not to "
                    "exercise. Gifts within the per-donee exclusion need no federal "
                    "tax, but a Form 709 is still commonly filed to report split "
                    "gifts or start the statute of limitations; Connecticut's CT-709 "
                    "rides the same April 15 deadline."
                ),
                "conclusion": (
                    "The exclusion is available if the Crummey mechanics are "
                    "actually observed — notice, window, no prearrangement. Treat "
                    "the notices as the tax documents they are, and keep the settlor "
                    "free of IRC §§ 2036–2038 strings."
                ),
            },
            "authorities": [
                {"citation": "IRC § 2503(b)", "note": "annual exclusion; present-interest requirement"},
                {"citation": "Crummey v. Commissioner", "note": "withdrawal right creates present interest"},
                {"citation": "IRC §§ 2036–2038", "note": "retained-interest estate inclusion"},
                {"citation": "CGS § 12-642", "note": "Connecticut gift tax"},
            ],
            "confidence": 0.93,
        },
        "trust_law": {
            "expert": "trust_law",
            "irac": {
                "issue": (
                    "What duties the trustee owes the withdrawal-power holders when "
                    "contributions arrive, and how sloppy notice practice damages "
                    "the plan."
                ),
                "rule": (
                    "UTC § 801 obliges the trustee to administer the trust in good "
                    "faith according to its terms, and UTC § 802's duty of loyalty "
                    "runs to the power holders while their withdrawal rights are "
                    "outstanding. The Restatement (Third) of Trusts treats keeping "
                    "beneficiaries reasonably informed as core administration."
                ),
                "application": (
                    "On each contribution the trustee — not the settlor — should "
                    "issue written withdrawal notices, hold liquid assets sufficient "
                    "to honor a demand during the window, and never solicit waivers "
                    "in advance. Notice files are the first thing an IRS examiner "
                    "asks for; a trustee who cannot produce them has converted a tax "
                    "problem into a fiduciary one."
                ),
                "conclusion": (
                    "Run the notices as a standing trustee procedure with proof of "
                    "delivery and a funded window. The fiduciary record and the tax "
                    "result stand or fall together."
                ),
            },
            "authorities": [
                {"citation": "UTC § 801", "note": "duty to administer in good faith"},
                {"citation": "UTC § 802", "note": "duty of loyalty to power holders"},
                {"citation": "Restatement (Third) of Trusts", "note": "duty to inform beneficiaries"},
            ],
            "confidence": 0.88,
        },
        "ct_law": {
            "expert": "ct_law",
            "irac": {
                "issue": (
                    "What Connecticut-specific filings and residency wrinkles attach "
                    "to annual-exclusion gifts made by a Connecticut settlor to an "
                    "irrevocable trust."
                ),
                "rule": (
                    "Connecticut is the only state with its own gift tax: CGS "
                    "§ 12-642 taxes lifetime transfers above the Connecticut "
                    "exemption, reported on the CT-709. Trust income taxation "
                    "follows CGS § 12-701's resident-trust rules, read against the "
                    "due-process limits of North Carolina Dept. of Revenue v. "
                    "Kaestner."
                ),
                "application": (
                    "Annual-exclusion gifts fall outside the Connecticut gift-tax "
                    "base just as they do federally, but the CT-709 is still filed "
                    "when a federal 709 is due. Because the settlor is a Connecticut "
                    "resident, the trust likely starts as a resident trust under "
                    "§ 12-701 — worth flagging now, since Kaestner limits taxing "
                    "trusts whose only nexus is a beneficiary's residence, not a "
                    "settlor's."
                ),
                "conclusion": (
                    "Mirror every federal filing with its Connecticut counterpart on "
                    "the same April 15 clock, and record the trust's § 12-701 "
                    "residency analysis at formation while the facts are fresh."
                ),
            },
            "authorities": [
                {"citation": "CGS § 12-642", "note": "Connecticut gift tax; CT-709"},
                {"citation": "CGS § 12-701", "note": "resident-trust definition"},
                {"citation": "North Carolina Dept. of Revenue v. Kaestner", "note": "due-process limits on trust taxation"},
            ],
            "confidence": 0.86,
        },
    },
}


# --------------------------------------------------------------------------
# 2.4 ConflictDetector — 4 locked patterns
# --------------------------------------------------------------------------

_GST_CONFLICT = {
    "conflict_id": "gst_grandfather_termination",
    "severity": "critical",
    "domains": ["trust_law", "tax_law"],
    "summary": (
        "Modification valid under CGS § 45a-499n may terminate grandfathered "
        "GST-exempt status under Treas. Reg. § 26.2601-1(b)(4)."
    ),
    "recommendation": (
        "Obtain GST analysis before executing the modification; consider a "
        "nonjudicial settlement limited to administrative terms."
    ),
}

_KEYWORD_CONFLICTS: list[dict[str, Any]] = [
    {
        "triggers": ("holographic", "handwritten"),
        "conflict": {
            "conflict_id": "holographic_will_ct",
            "severity": "high",
            "domains": ["ct_law", "estate_law"],
            "summary": (
                "A holographic (handwritten, unwitnessed) will executed in "
                "Connecticut fails the two-witness requirement of CGS § 45a-251, "
                "even though some other states would admit it."
            ),
            "recommendation": (
                "Verify where the will was executed; if executed in Connecticut "
                "without witnesses, plan for intestacy or seek admission under "
                "the law of the place of execution."
            ),
        },
    },
    {
        "triggers": ("retained power", "retained income", "retained control", "settlor control", "2036"),
        "conflict": {
            "conflict_id": "irc_2036_retained_powers",
            "severity": "high",
            "domains": ["trust_law", "tax_law"],
            "summary": (
                "Powers the settlor retains over a transferred interest may be "
                "valid under trust law yet pull the assets back into the gross "
                "estate under IRC §§ 2036–2038."
            ),
            "recommendation": (
                "Inventory every retained power and either release it more than "
                "three years before death or price in estate inclusion."
            ),
        },
    },
    {
        "triggers": ("kaestner", "resident trust", "nonresident beneficiary", "out-of-state beneficiary"),
        "conflict": {
            "conflict_id": "kaestner_resident_trust",
            "severity": "medium",
            "domains": ["ct_law", "tax_law"],
            "summary": (
                "Connecticut's resident-trust income tax under CGS § 12-701 may "
                "overreach where the trust's only Connecticut nexus is a "
                "beneficiary, per North Carolina Dept. of Revenue v. Kaestner."
            ),
            "recommendation": (
                "Map every Connecticut contact of the trust before conceding "
                "resident-trust status on the CT-1041."
            ),
        },
    },
]


class ConflictDetector:
    @staticmethod
    def detect(scenario_id: str, free_text: str = "") -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []
        if scenario_id == "trust_modification_gst":
            conflicts.append(dict(_GST_CONFLICT))
        text = (free_text or "").lower()
        if text:
            for pattern in _KEYWORD_CONFLICTS:
                if any(trigger in text for trigger in pattern["triggers"]):
                    conflicts.append(dict(pattern["conflict"]))
        return conflicts


# --------------------------------------------------------------------------
# 2.5 LegalSynthesizer
# --------------------------------------------------------------------------

_SYNTHESES: dict[str, dict[str, str]] = {
    "trust_modification_gst": {
        "issue": (
            "Can the beneficiaries modify this grandfathered irrevocable "
            "Connecticut trust by consent without destroying its GST exemption?"
        ),
        "rule": (
            "CGS § 45a-499n and UTC § 411 open the state-law door; Treas. Reg. "
            "§ 26.2601-1(b)(4) decides whether the federal exemption survives "
            "walking through it."
        ),
        "application": (
            "The three consulted experts converge: the consent path is "
            "procedurally available, but any shift of beneficial interests "
            "toward a lower generation or extension of vesting forfeits the "
            "grandfather. The safe route is a modification — or a CGS § 45a-487a "
            "nonjudicial settlement — confined to administrative terms."
        ),
        "conclusion": (
            "Sequence the work tax-first: written GST analysis, then drafting "
            "restricted to what the safe harbor tolerates, then consents and "
            "any Probate Court approval. One critical cross-domain conflict is "
            "flagged and must be cleared before execution."
        ),
    },
    "ct_probate_opening": {
        "issue": (
            "How does the executor open this Connecticut estate and stay "
            "personally safe while administering it?"
        ),
        "rule": (
            "CGS § 45a-251 governs admission of the will, CGS § 45a-436 the "
            "spousal election, and CGS § 12-391 the six-month estate-tax return; "
            "IRC §§ 2010 and 1014 shape the federal elections."
        ),
        "application": (
            "The experts align on a single calendar: petition by day 30, "
            "inventory by day 60 of appointment, creditor bar and elective "
            "share both at 150 days, the CT return at six months, and final "
            "accounting targeted around day 270. Portability under IRC § 2010 "
            "is the one discretionary election worth a deliberate decision."
        ),
        "conclusion": (
            "Run the five statutory clocks from day one, hold distributions "
            "until the 150-day windows close, and document date-of-death values "
            "once for both the inventory and the IRC § 1014 step-up."
        ),
    },
    "crummey_annual_gift": {
        "issue": (
            "Will this year's gifts to the Crummey trust qualify for the "
            "annual exclusion federally and in Connecticut?"
        ),
        "rule": (
            "IRC § 2503(b) requires a present interest; Crummey v. Commissioner "
            "supplies it through real withdrawal rights; CGS § 12-642 adds the "
            "Connecticut reporting layer."
        ),
        "application": (
            "Tax and trust experts agree the plan works only as well as its "
            "paper trail: contribution, same-day trustee notice, a funded "
            "30-day window, no prearranged waivers, and Form 709 / CT-709 filed "
            "by April 15. The fiduciary duties in UTC §§ 801–802 and the "
            "IRC §§ 2036–2038 retained-power screen are the two failure modes."
        ),
        "conclusion": (
            "Adopt the notice procedure as a standing trustee protocol, file "
            "both returns on the same clock, and keep the settlor's hands off "
            "the trust after funding."
        ),
    },
}

_CHECKLISTS: dict[str, list[dict[str, str]]] = {
    "trust_modification_gst": [
        {"step": "Confirm the trust was irrevocable on September 25, 1985 and verify no additions (actual or constructive) have been made since.",
         "deadline": "Before any drafting"},
        {"step": "Commission a written GST analysis under Treas. Reg. § 26.2601-1(b)(4) covering every proposed change.",
         "deadline": "Before any drafting"},
        {"step": "Classify each proposed change as administrative or dispositive; strike or isolate anything that shifts beneficial interests to a lower generation or extends vesting.",
         "deadline": "Drafting phase"},
        {"step": "Identify all qualified beneficiaries and any virtual representatives; confirm capacity and obtain written consents (CGS § 45a-499n).",
         "deadline": "Before execution"},
        {"step": "Assess material purpose — a spendthrift clause is presumptive evidence — and decide between Probate Court approval and a CGS § 45a-487a nonjudicial settlement agreement.",
         "deadline": "Before execution"},
        {"step": "Execute the modification with trustee joinder and contemporaneous documentation of the safe-harbor analysis.",
         "deadline": "Execution"},
        {"step": "Calendar Form 709 / CT-709 review for the year of modification in case any deemed transfer occurred.",
         "deadline": "April 15 of the following year"},
    ],
    "ct_probate_opening": [
        {"step": "File the petition and original will with the Probate Court for the decedent's domicile district (CGS § 45a-251 proof requirements).",
         "deadline": "30 days from death"},
        {"step": "Accept appointment, post any required bond, and obtain the fiduciary certificate.",
         "deadline": "At appointment"},
        {"step": "Publish newspaper notice to creditors, opening the claim period.",
         "deadline": "150-day claim window"},
        {"step": "File the inventory of estate assets at date-of-death values.",
         "deadline": "60 days from appointment"},
        {"step": "Monitor the surviving spouse's elective share under CGS § 45a-436 — no distributions that could impair it.",
         "deadline": "150 days from appointment"},
        {"step": "File the Connecticut estate tax return (CGS § 12-391), taxable or not, and decide the federal portability election (IRC § 2010).",
         "deadline": "183 days (6 months) from death"},
        {"step": "File the final accounting and distribute only after the creditor and election windows close.",
         "deadline": "Target 270 days"},
    ],
    "crummey_annual_gift": [
        {"step": "Confirm the trust instrument grants each intended donee a presently exercisable withdrawal right over contributions.",
         "deadline": "Before funding"},
        {"step": "Fund the gifts, keeping each donee's total within the IRC § 2503(b) annual exclusion.",
         "deadline": "Calendar year of gift"},
        {"step": "Have the trustee issue written Crummey withdrawal notices to every power holder (or guardian) the day contributions arrive.",
         "deadline": "At funding"},
        {"step": "Hold liquid assets sufficient to honor withdrawals through the notice window; obtain no advance waivers.",
         "deadline": "30-day window"},
        {"step": "Collect and archive delivery confirmations for every notice.",
         "deadline": "Close of window"},
        {"step": "File federal Form 709 and Connecticut CT-709 (CGS § 12-642) reporting the gifts.",
         "deadline": "April 15 of the following year"},
        {"step": "Screen the settlor annually for retained powers implicating IRC §§ 2036–2038.",
         "deadline": "Annual review"},
    ],
}


class LegalSynthesizer:
    def __init__(self) -> None:
        self.library = ScenarioLibrary()
        self.router = MixtureRouter()
        self.conflicts = ConflictDetector()

    def synthesize(
        self,
        scenario_id: str | None = None,
        free_text: str | None = None,
        top_k: int = MixtureRouter.DEFAULT_TOP_K,
    ) -> dict[str, Any]:
        if not scenario_id and not (free_text and free_text.strip()):
            raise ValueError("provide a scenario_id or a free-text query")
        if free_text is not None and len(free_text) > MAX_QUERY_LENGTH:
            raise ValueError(f"free-text query exceeds {MAX_QUERY_LENGTH} characters")

        match_score = None
        matched_by = "scenario_id"
        if scenario_id:
            scenario = ScenarioLibrary.get(scenario_id)
        else:
            scenario_id, match_score = ScenarioLibrary.match_free_text(free_text or "")
            scenario = ScenarioLibrary.get(scenario_id)
            matched_by = "free_text"

        routing = self.router.route(scenario_id, top_k=top_k)
        consulted = [entry["expert"] for entry in routing if entry["consulted"]]
        analyses = [
            _ANALYSES[scenario_id][expert]
            for expert in consulted
            if expert in _ANALYSES[scenario_id]
        ]
        conflicts = self.conflicts.detect(scenario_id, free_text or "")

        response: dict[str, Any] = {
            "scenario": {
                "id": scenario["id"],
                "title": scenario["title"],
                "description": scenario["description"],
                "matched_by": matched_by,
            },
            "routing": routing,
            "expert_analyses": analyses,
            "conflicts": conflicts,
            "synthesis": dict(_SYNTHESES[scenario_id]),
            "compliance_checklist": [dict(item) for item in _CHECKLISTS[scenario_id]],
            "flagged_for_review": True,
            "unauthorized_practice_warning": UNAUTHORIZED_PRACTICE_WARNING,
        }
        if matched_by == "free_text":
            response["scenario"]["match_score"] = match_score
            response["query"] = free_text
        return response
