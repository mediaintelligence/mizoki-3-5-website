# Decision Concierge — Guide Agent Spec (Executive Briefing v1.1)

**Status:** SHIPPED 2026-07-31 (owner-directed). Guided-by-default on
`/executive-briefing/`; self-drive one click away.
**Position:** the guide IS the product story — a live demonstration of
DCP-style control: suggest + highlight + unlock, while the executive commits
every critical action. Internally this is the boss agent; in the UI it is the
**Decision Concierge**.

## 1. Persona

Calm senior operator — a chief of staff for decisions. Plain language first;
at most one architecture name (DCP / VAL / CSE / SRPVDAL) per stage. Stance
line (test-enforced): **"I'll suggest; you commit."** Never a hype bot, never
an emoji mascot, never hard-sell.

## 2. Control model (non-negotiable)

- The guide **never** programmatically clicks a briefing control —
  `tests/test_briefing_guide.py::test_guide_never_clicks_briefing_controls`
  fails the build if a click call appears in `guide.js`.
- Suggestions scroll + pulse-highlight the target (`.mzg-pulse`); the
  executive presses it.
- The critical-path gate (red signal → "Commit action · resolve signal") is
  coached, never bypassed: *"the part I cannot do for you."*
- Docked, never covering: while open, the page reserves the rail's space
  (`html.mzg-docked`), so the panel cannot intercept pointer events on the
  briefing (a Playwright run caught exactly this bug pre-ship).

## 3. Dual mode

| Mode | Behavior |
|:--|:--|
| `guided` (default) | Rail open, stage scripts, suggestions, Q&A |
| `self` | Rail collapsed to a `🧭 GUIDE` tab; full briefing UI untouched |

`window.MIZOKI_CONFIG.guideMode = "guided" | "self"` sets the default;
the visitor's choice persists per session (`sessionStorage.mizokiGuideMode`).
Future: live human takeover (AE joins the session) for high-intent traffic.

## 4. Stage scripts (stage × domain × role)

Scripts live in `executive-briefing/js/guide.js` (`stageScript()`); domain
facts come from `MIZOKI.DOMAINS`, role framing from `MIZOKI.ROLES[].focus` —
data-driven, so all 8 domains and 6 roles are covered without a hand matrix.

| Stage | Job | Script core |
|:--|:--|:--|
| context | Anchor | Who are you; why domain matters (one sentence) |
| exposure | Intrigue | "What status quo costs in <domain>" + role framing + invited challenge ("high or low?") |
| live | Prove | Coach the red signal by name; "the part I cannot do for you"; inline Q&A |
| case | Explain | Role-focus translation; pilot vs board framing, "no urgency theater" |
| decision | Close | Three clean exits; role-recommended default (CEO/COO/VP→pilot, CFO/CHRO→board, CTO→deep-dive); "the only open question left is how fast you start" |

After `signal_resolved`: "That commit was yours, not mine — and that is the
point." After `decision_confirmed`: handoff line + `guide_handoff` event.

## 5. Q&A — allowlist retrieval, no generation

`POST /api/briefing/guide/ask` → `mizoki_runtime/briefing_guide.py`:
keyword-scored retrieval over **PRODUCT_FACTS** (DCP, validation passports,
CSE, SRPVDAL, two-track, evidence rule) and the **objection bank**. Unknown →
honest fallback, logged for human follow-up. There is no generative path, so
the concierge cannot invent pricing, certifications, or customer logos
(claims-linted: no guarantees, no cert names, no dollar figures, no pressure
vocabulary).

### Objection bank (cached answers)

`integration_risk` · `existing_bi` · `security` · `not_now` · `budget_owner`
· `pricing` — each resolves from a chip or free text
(`test_every_cached_objection_resolves`).

## 6. Event schema + memory (the improvement loop)

Every interaction lands in `data/guide_interactions.jsonl` via
`POST /api/briefing/guide/event` (strict allowlist):

`guide_opened · guide_collapsed · guide_resumed · suggestion_accepted ·
question_asked · objection_raised · stage_changed · signal_resolved ·
decision_intent · decision_confirmed · guide_handoff`

Row: `{ts, session, event, stage, domain, role, payload}` (sanitized,
size-capped). `GET /api/briefing/guide/summary` aggregates: sessions, events
by type, **objections ranked**, question topics, **drop-off stage**,
decision intents, **suggestion acceptance rate**.

### Under the Boss (sub-agent exposure)

The runtime registers two MCP tools, so the Boss can operate the guide as a
sub-agent and read its memory:

- `guide.answer` — the same allowlisted Q&A
- `guide.memory_summary` — the aggregate above

Ask the site Boss "what are prospects objecting to this week?" and
`guide.memory_summary` answers from real traffic.

## 7. What was deliberately not built

Free-form LLM generation on the sales surface; auto-completing the demo;
a competitor to the six-desk technical track (labels stay: executive
briefing = guided, `/demo` = technical); replacement of human sales — the
concierge books pilot / board / deep-dive; humans close.

## 8. Files

| File | Role |
|:--|:--|
| `executive-briefing/js/guide.js` | Concierge UI + state machine (canon-pinned) |
| `executive-briefing/js/app.js` | +`mizoki:briefing` event bridge (canon-pinned) |
| `mizoki_runtime/briefing_guide.py` | Fact pack, objection bank, retrieval, memory |
| `app.py` | `/api/briefing/guide/{event,ask,summary}` |
| `mizoki_runtime/runtime.py` | `guide.answer` + `guide.memory_summary` MCP tools |
| `tests/test_briefing_guide.py` | Wiring, endpoints, bank, claims lint, no-click rule |
