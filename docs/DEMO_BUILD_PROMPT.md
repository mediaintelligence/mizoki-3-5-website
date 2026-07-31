# Claude Code Build Prompt — MIZ OKI Virtual Demos: Signal Factory + Counsel Room

> Copy everything below the line into Claude Code, run from the repo root
> (`/Users/mizoki3.0/MIZOKICloudRun`). The working directory for all changes is
> the marketing site folder `# MIZ OKI 3.5/` (quote the path in every shell
> command: `"# MIZ OKI 3.5"`).

---

## ROLE

You are building two interactive product demos inside the **MIZ OKI 3.5
marketing website** (`# MIZ OKI 3.5/`), which deploys as the `mizoki-website`
Cloud Run service (Python 3.13, Flask 3.1.3 + Gunicorn, 256 MiB / 1 vCPU,
stdlib-only besides Flask). The demos showcase two product divisions:

1. **Signal Factory** — the Signal division. Shows raw marketing signals being
   "manufactured" into governed autonomous decisions through the 7-stage
   SRPVDAL pipeline (Sense → Reason → Plan → Validate → Decide → Act → Learn)
   with a visible ReLU gate and guardrails.
2. **Counsel Room** — the Counsel (legal) division. Shows the
   Mixture-of-Legal-Experts (MoLE): a legal scenario fans out to 4 domain
   experts (Connecticut / Trust / Estate / Tax), each returns an IRAC
   analysis, and a synthesizer reconciles them and surfaces cross-domain
   conflicts.

Both demos must be **fully deterministic** (seeded synthetic data, scripted
scenarios), require **zero external API/LLM calls**, and add **no new
dependencies** to `requirements.txt`.

## EXISTING CODE YOU MUST INTEGRATE WITH (read these first)

- `# MIZ OKI 3.5/app.py` — Flask app factory `create_app(runtime)`. Routes for
  pages and `/api/mcp/*`, `/api/boss/*`. Helper functions already exist:
  `json_error`, `require_json_payload`, `run_runtime_call`, `serve_page`,
  and the `_AUTH_GATED_API_PREFIXES` auth gate (only `/api/mcp/` and
  `/api/boss/` are gated — keep `/api/demo/` public).
- `# MIZ OKI 3.5/mizoki_runtime/runtime.py` — `BossRuntime` with an MCP-style
  tool registry (typed parameters: string/integer/number/boolean/array/object),
  skill store, KG, GraphRAG, decision traces, and `create_runtime(...)`.
  Register the new demo tools on this runtime so they appear in
  `GET /api/mcp/tools` and are callable via `POST /api/mcp/call` and the
  `/admin` tool runner. Study how existing tools (e.g. `graphrag.query`,
  `decision.explain_pipeline`) are registered and follow the same pattern
  exactly (parameter specs, handler signature, return shapes).
- `# MIZ OKI 3.5/tests/test_app.py` and `tests/test_runtime.py` — follow their
  style (stdlib `unittest`, Flask test client, no pytest).
- Site design system: dark theme `#0a0a0f`–`#12121a`, cyan `#00d4ff`, blue
  `#4f8fff`, purple `#a855f7`, green `#10b981`, orange `#f59e0b`, red
  `#ef4444`. Fonts: Instrument Serif (headings), DM Sans (body), JetBrains
  Mono (code/data). Pages are self-contained HTML with inline CSS. Every page
  must include `<script src="/assets/js/nav-mobile.js" defer></script>` before
  `</body>` and reuse the nav header structure from `signal.html` /
  `counsel.html` so mobile nav auto-wires.

## CONSTRAINTS (hard rules)

1. Python stdlib + Flask only. No numpy, no requests, no websockets.
2. All randomness must come from `random.Random(seed)` instances with a fixed
   default seed so runs are reproducible; accept an optional `seed` parameter.
3. Do not modify `Dockerfile`, `cloudbuild.yaml`, `requirements.txt`,
   `deploy.sh`, or anything under `.github/`.
4. Do not rename or move existing files. Only add files and extend `app.py`
   and the runtime tool-registration point.
5. `/api/demo/*` endpoints are public (do NOT add them to
   `_AUTH_GATED_API_PREFIXES`).
6. Keep per-request memory small: a full signal pipeline run must produce
   < 200 events and the SSE stream must terminate on its own within ~60s.
7. Every Counsel Room response MUST include
   `"flagged_for_review": true` and an `"unauthorized_practice_warning"`
   string. This is non-negotiable compliance behavior.
8. All new Python passes `python3 -m py_compile` and all tests pass with
   `python3 -m unittest discover tests`.

---

## PART 1 — Signal Factory engine: `mizoki_runtime/demo_signal.py`

Create a self-contained module with these components:

### 1.1 Scenarios

Three seeded scenarios selectable by id:

| id | name | signal mix |
|:---|:-----|:-----------|
| `ecommerce_roas` | E-commerce ROAS optimization | google_ads clicks/conversions, ga4 page/cart events, meta impressions |
| `leadgen_cpa` | Lead-gen CPA reduction | search clicks, form submits, CRM lead-quality events |
| `email_reengagement` | Email re-engagement | email opens (some MPP-proxy flagged), clicks, unsubscribes |

### 1.2 `SyntheticEventGenerator`

- `generate(scenario_id, count=18, seed=42) -> list[RawEvent]`
- Each `RawEvent` (dataclass → dict): `event_id`, `source`
  (`google_ads|ga4|meta|email|crm`), `event_type`, `entity_id` (e.g.
  `campaign_7`, `audience_hv`), `value` (float), `timestamp` (monotonic ISO
  strings), `raw_payload` (small dict with source-plausible fields).
- Deliberately include ~15% "weak" events (low value / low sample) and, in the
  email scenario, ~30% proxy-open events so the gate visibly filters.

### 1.3 Canonical normalization

- `normalize(raw_event) -> CanonicalEvent` with fields: `canonical_id`,
  `entities` (list), `relationships` (list of `{from, type, to}`),
  `confidence` (0–1, derived deterministically from source + type),
  `security_scope` (`tenant: "demo"`), `provenance` (`{source, connector,
  received_at, transform: "demo_normalizer_v1"}`).
- This encodes the platform principle: **nothing goes straight from connector
  to action** — every raw event becomes a CanonicalEvent before SRPVDAL.

### 1.4 Signal aggregation + `ReLUGate`

- Aggregate canonical events per entity into `Signal` objects:
  `entity_id`, `metric` (e.g. `roas_delta`, `cpa_delta`, `engagement_delta`),
  `uplift` (can be negative), `confidence`, `sample_size`.
- Gate score: `score = max(0.0, uplift) * confidence * math.log(1 + sample_size)`
- Thresholds: pass iff `uplift >= 0.05` AND `confidence >= 0.70` AND
  `sample_size >= 15`. Return per-signal gate verdicts with the reason string
  for failures (`"uplift below 5% floor"`, `"confidence below 0.70"`,
  `"sample too small (n=%d < 15)"`) — the UI displays these verbatim.

### 1.5 `GuardrailSet` (Validate stage)

Checks applied to each planned action, each returning
`{rule_id, name, passed, detail}`:

- `budget_swing_cap` — block if proposed budget change > 20%
- `bid_swing_cap` — block if proposed bid change > 30%
- `confidence_floor` — block if decision confidence < 0.70
- `sample_floor` — block if supporting conversions < 15
- `rollback_ready` — always passes; asserts a rollback token was minted

Each scenario must include **exactly one planned action that fails a
guardrail** (design the synthetic data so this happens deterministically) —
the visible red "blocked" moment is a key part of the demo narrative.

### 1.6 `SignalFactoryPipeline`

- `run(scenario_id, seed=42) -> PipelineRun` executing all 7 stages, producing
  an ordered list of `StageTrace` objects:
  `{stage, started_at, summary, items: [...], counts}` where stages are
  `sense`, `reason`, `plan`, `validate`, `decide`, `act`, `learn`.
  - **sense**: raw events + canonical events
  - **reason**: hypotheses per surviving entity (`"campaign_7 audience_hv is
    outperforming account ROAS by 22%"`) with confidence
  - **plan**: proposed actions (`budget_increase`, `bid_adjust`,
    `creative_rotate`, `suppress_segment`) with magnitude + expected value
  - **validate**: guardrail results incl. the one deliberate block
  - **decide**: surviving actions ranked by `expected_value × confidence`
  - **act**: dry-run execution records — `{action_id, mode: "dry_run",
    rollback_token: "hmac-demo:" + sha256 hex prefix, status: "executed"}`
  - **learn**: predicted vs simulated-actual deltas + one learning note
- `run_streaming(scenario_id, seed=42) -> Iterator[dict]` yielding the same
  content as ordered SSE-ready frames:
  `{"type": "raw_event"|"canonical_event"|"signal_gate"|"stage"|"decision_card"|"done", "data": {...}}`
  with a small `delay_hint_ms` field the Flask layer uses for pacing
  (total stream ≤ 60s; use `time.sleep(delay_hint_ms/1000)` in the Flask
  generator, not in the engine, so tests can consume frames instantly).
- Final frame `decision_card`: executed action, full provenance chain (raw →
  canonical → signal → gate → guardrails → decision), funnel counters
  (`events_sensed, signals_formed, passed_gate, validated, executed`), and
  `trace_id`.

## PART 2 — Counsel Room engine: `mizoki_runtime/demo_counsel.py`

### 2.1 `ScenarioLibrary`

Three scripted scenarios with ids, titles, and a `keywords` list used for
free-text matching:

1. `trust_modification_gst` — "Modify an irrevocable CT trust by beneficiary
   consent — trust has grandfathered GST status." **Must trigger the
   cross-domain conflict.**
2. `ct_probate_opening` — "Open probate for a CT decedent — executor duties
   and statutory deadlines." (Timeline-focused: 30/60/150/183/270-day
   deadlines; elective share 150-day warning.)
3. `crummey_annual_gift` — "Make annual exclusion gifts to an irrevocable
   trust with Crummey powers." (Forms 709 + CT-709; withdrawal-notice
   mechanics.)

`match_free_text(text) -> (scenario_id, match_score)` via token overlap with
each scenario's keywords; always returns the best scenario (never errors).

### 2.2 `MixtureRouter`

`route(scenario) -> list[{expert, relevance, rationale}]` for the 4 experts
`ct_law`, `trust_law`, `estate_law`, `tax_law`. Relevance scores are scripted
per scenario (e.g. `trust_modification_gst`: CT 0.94, Trust 0.91, Tax 0.88,
Estate 0.42) with a one-line rationale each. `top_k` defaults to 3; experts
below 0.5 are marked `"consulted": false` but still listed.

### 2.3 Expert analyzers

Each expert returns an IRAC dict:

```json
{
  "expert": "ct_law",
  "irac": {
    "issue": "...",
    "rule": "...",
    "application": "...",
    "conclusion": "..."
  },
  "authorities": [
    {"citation": "CGS § 45a-499n", "note": "modification by consent (CTUTC)"}
  ],
  "confidence": 0.9
}
```

Authorities must be drawn from this corpus (hardcode as module data —
these mirror the production `legal_expertise_integration.py` corpus):
CGS §§ 45a-499n, 45a-499o, 45a-487a, 45a-251, 45a-436, 12-391, 12-642,
12-701; UTC §§ 411, 801, 802; Restatement (Third) of Trusts; IRC §§ 2001,
2010, 2503(b), 2601, 2036–2038, 1014; Treas. Reg. § 26.2601-1(b)(4);
Crummey v. Commissioner; North Carolina Dept. of Revenue v. Kaestner.
Write substantive, accurate IRAC text per scenario/expert (2–4 sentences per
IRAC element) — this is the centerpiece of the demo, do not stub it.

### 2.4 `ConflictDetector`

Implements the 4 locked conflict patterns; for `trust_modification_gst` it
MUST return:

```json
{
  "conflict_id": "gst_grandfather_termination",
  "severity": "critical",
  "domains": ["trust_law", "tax_law"],
  "summary": "Modification valid under CGS § 45a-499n may terminate grandfathered GST-exempt status under Treas. Reg. § 26.2601-1(b)(4).",
  "recommendation": "Obtain GST analysis before executing the modification; consider a nonjudicial settlement limited to administrative terms."
}
```

Other patterns (holographic-will-in-CT, IRC 2036 retained powers, Kaestner
resident-trust) fire only if their trigger keywords appear.

### 2.5 `LegalSynthesizer`

`synthesize(scenario_id | free_text) -> dict` returning:
`scenario`, `routing`, `expert_analyses`, `conflicts`, `synthesis` (a merged
IRAC-style summary), `compliance_checklist` (scenario-appropriate ordered
steps with statutory deadlines — for `trust_modification_gst`, 7 steps of the
CT trust-modification playbook), `flagged_for_review: true`, and
`unauthorized_practice_warning` (exact text: "This is AI-augmented legal
research, not legal advice. Engage a Connecticut-licensed attorney before
acting on any output.").

## PART 3 — Flask integration (`app.py`)

Add inside `create_app` following existing patterns:

### Pages
- `GET /demo` and `/demo.html` → `demo.html` (hub)
- `GET /demo/signal` and `/demo-signal.html` → `demo-signal.html`
- `GET /demo/counsel` and `/demo-counsel.html` → `demo-counsel.html`

### JSON APIs (public, JSON errors via `json_error`)
- `POST /api/demo/signal/run` — body `{scenario, seed?}` → full `PipelineRun`
  as JSON. Validate `scenario` against known ids (400 otherwise).
- `GET /api/demo/signal/scenarios` — list scenarios with names/descriptions.
- `GET /api/demo/signal/stream?scenario=ecommerce_roas&seed=42` — SSE
  (`text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`).
  Each frame: `event: <type>\ndata: <json>\n\n`. Flask generator applies
  `delay_hint_ms` pacing; ends with `event: done`.
- `GET /api/demo/counsel/scenarios` — scenario list.
- `POST /api/demo/counsel/query` — body `{scenario_id}` OR `{query}`
  (free text, max 500 chars) → full synthesis JSON.

### MCP tool registration
Register on the `BossRuntime` (same mechanism as existing tools):
- `demo.signal.run` (params: `scenario` string required, `seed` integer
  optional) → returns the PipelineRun dict
- `demo.signal.list_scenarios` (no params)
- `demo.counsel.query` (params: `scenario_id` string optional, `query` string
  optional — at least one required) → returns the synthesis dict
- `demo.counsel.list_scenarios` (no params)

Give them descriptions, categories (`demo`), and tags so Boss discovery
(`/api/boss/discover`) can find them via phrases like "run the signal demo".

## PART 4 — Frontend

### 4.1 `demo.html` (hub)
Dark-theme page matching `index.html` styling: hero ("See MIZ OKI run — live,
on the same runtime that powers production"), two large cards linking to the
Signal Factory and Counsel Room demos with one-paragraph explanations, and a
footer CTA to `walkthrough.html`.

### 4.2 `demo-signal.html` + `assets/js/demo-signal.js`
- Layout top→bottom: scenario picker + Start/Reset controls; **event rail**
  (horizontal scroller where raw-event chips appear with source badges and
  morph/link to canonical-event cards); **ReLU gate widget** (SVG: signals
  enter left with score bars; failing signals drop to a "filtered" tray with
  their reason string; passing ones glow cyan and exit right); **SRPVDAL
  stage strip** (7 nodes that light up in sequence, each expanding a trace
  panel with that stage's items — the Validate stage shows the guardrail
  checklist with the deliberate red block); **Decision Card** (final
  provenance chain + funnel counters animating up); CTA.
- JS: consume the SSE endpoint with `EventSource`; keyed handlers per frame
  type; graceful fallback — if `EventSource` errors, call
  `POST /api/demo/signal/run` and replay frames locally with `setTimeout`.
  Vanilla JS only, no frameworks. Respect `prefers-reduced-motion`.

### 4.3 `demo-counsel.html` + `assets/js/demo-counsel.js`
- Layout: scenario cards + free-text input ("Describe your situation…");
  **router panel** (4 expert tiles with animated relevance-score bars, dimmed
  when not consulted); **expert grid** (IRAC cards revealed staggered ~600ms
  apart, each collapsible, authorities rendered as monospace citation chips);
  **conflict banner** (red, prominent, only when conflicts exist — slides in
  after the last expert card); **synthesis panel** + numbered compliance
  checklist with deadline badges; **persistent disclaimer footer** (always
  visible, orange border, renders `unauthorized_practice_warning`).
- JS: `POST /api/demo/counsel/query`, then orchestrate the staggered reveal
  client-side from the single response. Sanitize any echoed free text with
  `textContent` (never `innerHTML`) — XSS matters here.

### 4.4 Site wiring
- Add a "Live Demos" link to the nav of `demo*.html` pages themselves and add
  prominent "See it live" buttons on `signal.html` (→ `/demo/signal`) and
  `counsel.html` (→ `/demo/counsel`). Do not restructure those pages
  otherwise.

## PART 5 — Tests

`tests/test_demo_signal.py` (unittest):
- same seed ⇒ identical `PipelineRun` (deep-compare minus timestamps)
- gate math: hand-computed score for a known signal matches; each failure
  reason string is produced by a crafted signal
- exactly one guardrail block per scenario; blocked action absent from `act`
- streaming frames: correct ordering (`raw_event`* → … → `done`), and the
  set of frame types matches the non-streaming run
- Flask: `POST /api/demo/signal/run` 200 + funnel counters consistent;
  unknown scenario → 400; SSE endpoint returns `text/event-stream` and the
  first frame parses
- MCP: `demo.signal.run` appears in `GET /api/mcp/tools` and works via
  `POST /api/mcp/call`

`tests/test_demo_counsel.py`:
- `trust_modification_gst` ⇒ conflict `gst_grandfather_termination` present,
  severity `critical`
- every response has `flagged_for_review == True` and a non-empty
  `unauthorized_practice_warning` (test ALL scenarios + a free-text query)
- routing scores match spec for scenario 1; experts < 0.5 marked not consulted
- free-text "can I change my irrevocable trust in connecticut" routes to
  `trust_modification_gst`
- authorities in responses are all drawn from the allowed corpus list
- Flask: query by `scenario_id` and by `query` both 200; missing both → 400;
  free text > 500 chars → 400; XSS probe string is returned JSON-encoded, not
  reflected into any HTML
- MCP: `demo.counsel.query` callable via `/api/mcp/call`

## PART 6 — Verification & delivery (run all of these; all must pass)

```bash
cd "# MIZ OKI 3.5"
python3 -m py_compile app.py mizoki_runtime/runtime.py mizoki_runtime/demo_signal.py mizoki_runtime/demo_counsel.py
python3 -m unittest discover tests
# Manual smoke:
python3 - <<'EOF'
from mizoki_runtime.runtime import create_runtime
from app import create_app
app = create_app()
c = app.test_client()
print(c.get("/demo").status_code)
print(c.post("/api/demo/signal/run", json={"scenario": "ecommerce_roas"}).status_code)
print(c.post("/api/demo/counsel/query", json={"scenario_id": "trust_modification_gst"}).status_code)
EOF
```

Then also verify the pre-existing suites still pass unchanged
(`tests.test_app`, `tests.test_runtime` — 25 tests baseline).

Finish with a summary of: files added/modified, endpoint list, MCP tools
registered, test counts (before/after), and the exact demo script a sales
engineer would follow on each page (numbered steps, ≤ 10 per demo).

Do NOT deploy. Deployment happens through the existing
`deploy-homepage.yml` workflow after human review.
