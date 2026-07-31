# Flagship Demo Build — v4 Delivery Notes

Implements `FINAL_DEMO_PROMPT_V4` end-to-end: repairs D1–D8, complete
five-division demo coverage, the Nexus Run flagship, the showcase features
(§5), hardening + measurement (§6), the visual-QA gate (§7), and the grown
test suite (§8). **Tests: 122 → 218, all green.**

## File inventory

### Added — engines & runtime (`mizoki_runtime/`)
| File | Purpose |
|------|---------|
| `demo_estate.py` | Estate Room engine — statutory clocks, GST dynasty graph, IRC § 1014 basis table (Counsel pattern) |
| `demo_capital.py` | Capital Desk engine — Signal pattern + SSE, imports `ReLUGate`/`GuardrailSet`/`DEFAULT_SEED`, adds `covenant_headroom` rule |
| `demo_risk.py` | Risk Sentinel engine — 12–16 events on a 5×5 matrix, exactly two escalations (one auto-mitigated, one vetoed) |
| `demo_nexus.py` | The Nexus Run — chains all five engines under one `nexus_trace_id`, SSE frames trigger→…→done |
| `demo_narrator.py` | Trace Narrator — deterministic template narration, no LLM |
| `demo_telemetry.py` | Cookieless telemetry store (JSONL; `{ts, event, demo, scenario}` only) |

### Added — pages, JS, assets
| File | Purpose |
|------|---------|
| `demo-estate.html`, `demo-capital.html`, `demo-risk.html`, `demo-nexus.html` | The three new division demos + the flagship (Explore + Boardroom) |
| `assets/js/demo-estate.js`, `demo-risk.js`, `demo-nexus.js` | Page engines |
| `assets/js/demo-pipeline.js` | Parameterized Signal-pattern player (used by Capital) |
| `assets/js/demo-extras.js` | Shared showcase widgets: share/replay, narrator, MCP terminal, export, telemetry beacons, Governance Challenge drawer |
| `assets/css/demo-extras.css` | Styles for the shared widgets |
| `assets/img/og/og-*.svg` | 7 × 1200×630 share cards (hub + six demo pages) |
| `scripts/demo_screenshots.py` | Visual-QA gate (Playwright; dev-only) |
| `scripts/screenshots/*-1440.png` | Reviewed 1440 px capture set (attached to PR) |
| `tests/test_demo_{estate,capital,risk,nexus,narrator,platform}.py` | +96 tests |

### Modified
| File | Change |
|------|--------|
| `app.py` | Env-driven login/dashboard URLs (D3), canonical-host 308, demo rate limiter, six demo page routes (+ trailing slashes, share embedding), walkthrough + contact routes, robots/sitemap, estate/capital/risk/nexus APIs, narrate/export/telemetry APIs, lru caching |
| `mizoki_runtime/runtime.py` | `_register_demo_tools` extended with 10 new MCP tools |
| `demo.html` | Hub reworked: Nexus banner + five division cards; absolute URLs; meta |
| `demo-signal.html`, `demo-counsel.html` | Absolute URLs (D1), meta (D7), seed input, extras widgets, lead CTAs |
| `assets/js/demo-signal.js`, `demo-counsel.js` | Additive: seed input, autorun events, telemetry lifecycle events |
| `index.html` | Nav **Live Demos** → `/demo`; CTA in "See MIZOKI3 in Action"; footer link; `#demo` → `#action-flow` (D8); Sign In → `/login` |
| `counsel/estate/capital/signal/risk.html` | Live Demos nav item; estate/capital/risk hero "See it live" buttons |
| `walkthrough.html` | Un-301'd; "Try the live demos →" button; meta; Login → `/login` |
| `demo-opener.html` | Root-absolute links (D1 acceptance) |
| `templates/contact.html` | Hidden `source` field |
| `tests/test_runtime.py` | Expected tool set +10 |
| `Dockerfile` | `--threads 4` → `--threads 8` (only change) |
| `.gitignore` | Keep only the 1440 px screenshot set tracked |

## Endpoint table (new/changed)

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/demo`, `/demo/{signal,counsel,estate,capital,risk,nexus}` | GET | Trailing-slash tolerant; embeds sanitized `?scenario=&seed=` as `data-*` |
| `/walkthrough`, `/walkthrough.html` | GET | D2 fix |
| `/contact`, `/contact.html` | GET | Lead path; echoes sanitized `source` |
| `/robots.txt`, `/sitemap.xml` | GET | Sitemap lists all demo pages |
| `/api/demo/{estate,capital,risk,nexus}/scenarios` | GET | |
| `/api/demo/{estate,capital,risk,nexus}/run` | POST | `{scenario, seed?}`; 400 on unknown/malformed |
| `/api/demo/{capital,nexus}/stream` | GET | SSE; `Cache-Control: no-cache`, `X-Accel-Buffering: no` |
| `/api/demo/<demo>/narrate` | GET | `{narration, trace_id}` — all six demos |
| `/api/demo/<demo>/export` | GET | `{trace, integrity:{algo, digest, generated_at}}`; sha256 over canonical trace JSON |
| `/api/demo/telemetry` | POST | Exactly `{event, demo, scenario}`; enum-validated; extra keys → 400; no IP/UA stored |
| **Rate limits** | — | 30/min/IP, burst 10 (SSE ×3, export ×2), telemetry 10/min; 429 + `Retry-After`; env-tunable |
| **Canonical host** | — | `www.*` → 308 apex; `MIZOKI_CANONICAL_REDIRECT=off` kill-switch |
| **Login** | — | `MIZOKI_EXTERNAL_LOGIN_URL` (default `/admin/login`), `MIZOKI_EXTERNAL_DASHBOARD_URL` (default `/console`) |

## MCP tools (new)

`demo.estate.run`, `demo.estate.list_scenarios`, `demo.capital.run`,
`demo.capital.list_scenarios`, `demo.risk.run`, `demo.risk.list_scenarios`,
`demo.nexus.run`, `demo.nexus.list_scenarios`, `demo.narrate`,
`demo.telemetry.summary` — all category `demo`, callable via
`POST /api/mcp/call`.

## Test counts

- Before: **122** · After: **218** · Status: **OK** (plus the §10
  acceptance block prints `V4 ACCEPTANCE OK`).

## Sales scripts (≤10 steps)

### The Nexus Boardroom run
1. Open `mizoki3.com/demo/nexus` on the projector; hit **⛶ Boardroom mode**.
2. Trigger slide: "Overnight, Meta CPMs spiked 38% on our best campaign."
3. Signal slide: "Signal reallocates — but only through the ReLU gate. Uplift, confidence, sample floors. No vibes."
4. Capital slide: "The shifted spend re-enters as a capital move. One variant models covenant headroom at 11% — blocked. The envelope holds."
5. Risk slide: "Risk lights the matrix. One quiet auto-mitigation, one loud veto — with a rollback token minted *before* execution."
6. Counsel slide: "The replacement vendor's paper swaps mutual indemnity for a one-way cap. Flagged for a licensed attorney — the platform never signs."
7. Estate slide: "Nothing fires in Estate — and that restraint is written to the governance ledger. Non-action is auditable too."
8. Finale: "*One intelligence. Many domains. Shared causal memory.* Every verdict hangs off one trace id."
9. Esc → Explore mode → click **Why?** for the plain-English narration; **Download decision trace** for the signed JSON.
10. "Same seed, same run, on your laptop tonight" → **Copy shareable run** → `/contact?source=demo-nexus`.

### Estate Room
1. Open `/demo/estate`, scenario "CT estate settlement", press Start.
2. Watch the five statutory clocks arm in order — day 30, 60, 150, 150, 183 — with dependency arrows.
3. "An executor who respects these clocks is judgment-proof; one who distributes early is a guarantor."
4. Switch to "GST dynasty review": three generations, per-node exposure, and the grandfather flag worth 40% of corpus.
5. Switch to "Basis step-up": appraise once, use twice — inventory and § 1014.
6. Point at the disclaimer bar: every response flagged for attorney review, always.
7. **Why?** for the narration; **remix this run** with a new seed to prove determinism.
8. Close: `/contact?source=demo-estate`.

### Capital Desk
1. Open `/demo/capital`, scenario "Growth reallocation", press Start.
2. Ledger/treasury/market events stream in and normalize — same discipline as marketing signals.
3. The ReLU gate filters the weak units — imported from Signal, not re-implemented.
4. Validate stage: six guardrails; the 18% shift models headroom at 11% — **blocked in red**.
5. Decision card: the surviving move, ranked by EV × confidence, with its rollback token.
6. Open the **Governance Challenge** drawer — drag the floors and watch a blocked move "pass": "You just approved a decision the governor would have blocked."
7. **>_ MCP terminal**: "everything you just clicked is a tool your agents can call" — run it live.
8. Close: `/console` for the operator view, `/contact?source=demo-capital` for the pilot.

### Risk Sentinel
1. Open `/demo/risk`, scenario "Quarterly close watch", press Start.
2. Fourteen events land on the 5×5 matrix, cell by cell — most are noise, logged and left alone.
3. Green glow: covenant drift auto-mitigated under `covenant_drift_watch` — reserve booked, headroom restored.
4. Red glow: a $1.9M accrual release queued inside the close window — **vetoed** under `close_week_spend_freeze`.
5. Walk the veto card: rule id, three-step evidence chain, rollback token minted before anything could execute.
6. "This is the ACT-991 pattern from the operator console — see it live at `/console`."
7. Swap to "Vendor breach drill" for the security story; same two-escalation discipline.
8. Close: **Download decision trace** (signed) → `/contact?source=demo-risk`.

## Rollback

Revert the merge commit — `deploy-cloudrun.yml` redeploys the previous
image on the next push to `main`.
