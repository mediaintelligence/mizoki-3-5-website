# Claude Code Build Prompt — MIZ OKI Demo Fixes + Full Division Coverage (v2)

> Copy everything below the line into Claude Code, run from the repo root
> (`/Users/mizoki3.0/MIZOKICloudRun`). The working directory for all changes is
> the marketing site folder `# MIZ OKI 3.5/` (quote the path in every shell
> command: `"# MIZ OKI 3.5"`). Branch off `origin/main` (which already contains
> the Signal Factory + Counsel Room demos, commit lineage `532895f6`).

---

## ROLE

You are fixing and completing the **MIZ OKI 3.5 live demo experience** at
mizoki3.com. Two demos (Signal Factory at `/demo/signal`, Counsel Room at
`/demo/counsel`) are deployed and their engines/APIs/MCP tools work. A live
audit of mizoki3.com found the defects below. Your job: fix every defect,
wire the demos into the rest of the site, and build the three missing
division demos so all five divisions (Signal, Counsel, Estate, Capital,
Risk) have a working "See it live" experience.

## LIVE AUDIT FINDINGS (verified against production on 2026-07-17)

### A. CRITICAL — relative-URL base bug on pretty routes
`demo-signal.html` and `demo-counsel.html` use *relative* hrefs
(`assets/css/styles.css`, `index.html`, `counsel.html`, `walkthrough.html`).
When served at `/demo/signal` and `/demo/counsel`, browsers resolve them
against `/demo/`, so:
- `https://mizoki3.com/demo/assets/css/styles.css` → **404** — the shared
  design system never loads; the header/nav/buttons render unstyled on both
  demo pages.
- Every nav/footer link 404s: `/demo/index.html`, `/demo/counsel.html`,
  `/demo/estate.html`, `/demo/capital.html`, `/demo/signal.html`,
  `/demo/risk.html`, `/demo/walkthrough.html`.
The `<script src="/assets/js/...">` tags were already absolute, which is why
the demos "work" while looking broken. `demo.html` at `/demo` happens to
resolve correctly today but uses the same fragile relative links.

### B. `walkthrough.html` dead-ends at the homepage
The file `# MIZ OKI 3.5/walkthrough.html` exists (34 KB) but `app.py` lists
it in the `legacy_marketing_page` 301 block, so it redirects to `/`. The
demo hub footer CTA ("Read the full walkthrough →") and both demo pages'
"Platform walkthrough" CTAs silently dump visitors on the homepage.

### C. Sign In is a redirect loop
`/login` redirects to `EXTERNAL_LOGIN_URL = https://mizoki.mizoki3.com/login`,
which currently loops (`Too many redirects`). Anyone clicking Sign In from
the homepage hits a browser error.

### D. The demos are undiscoverable from the homepage
`index.html` (the big one-page site with its own nav: Platform / Nexus /
Divisions / Architecture / Resources / …) contains **no link to `/demo`**
anywhere — nav, dropdowns, footer, or the "See MIZOKI3 in Action" section.
The only entry points are the hero buttons on `signal.html` / `counsel.html`.

### E. Three divisions have no demo
`estate.html`, `capital.html`, `risk.html` are intact but have no
"See it live" button and no demo behind them. (`/console` — the static
"Risk Arbitration Console" mock — is live and can be linked as supporting
material, but it is not scenario-interactive.)

### F. Minor / hardening
- Demo pages have no favicon link and no OpenGraph/Twitter meta.
- SSE streaming: confirm the gunicorn invocation uses threads
  (e.g. `--threads 8`) so a handful of concurrent `/api/demo/signal/stream`
  connections (~11 s each) cannot starve the worker pool. The JS fallback
  masks this, but fix the root cause.

## EXISTING CODE TO REUSE (read first, follow patterns exactly)

- `# MIZ OKI 3.5/mizoki_runtime/demo_signal.py` — deterministic pipeline
  engine (scenario tables, seeded RNG, `run`/`run_streaming`, ReLU gate,
  GuardrailSet). **Template for the Capital demo.**
- `# MIZ OKI 3.5/mizoki_runtime/demo_counsel.py` — scripted expert/IRAC
  engine with routing, conflicts, checklists, compliance flags.
  **Template for the Estate and Risk demos.**
- `# MIZ OKI 3.5/mizoki_runtime/runtime.py` — `_register_demo_tools()` shows
  the MCP registration pattern; extend it, don't fork it.
- `# MIZ OKI 3.5/app.py` — `serve_page`, `json_error`, `require_json_payload`,
  `run_runtime_call`, demo API block. `/api/demo/*` stays public.
- `# MIZ OKI 3.5/assets/js/demo-signal.js`, `demo-counsel.js` — vanilla-JS
  patterns: keyed SSE handlers, staggered reveal, `textContent`-only
  rendering, `prefers-reduced-motion`.
- Tests: `tests/test_demo_signal.py`, `tests/test_demo_counsel.py` (stdlib
  unittest; current suite total is 122 — do not break it).

## CONSTRAINTS (unchanged from v1, plus one relaxation)

1. Python stdlib + Flask only; no new dependencies; all randomness through
   `random.Random(seed)`; deterministic runs.
2. `/api/demo/*` remains public (never add to `_AUTH_GATED_API_PREFIXES`).
3. Do not rename or move existing files. Only add files and extend `app.py`,
   `runtime.py`'s `_register_demo_tools`, and the HTML pages named below.
4. **Relaxation:** you MAY edit the gunicorn command (Dockerfile or start
   script) solely to add threading for SSE. Nothing else in
   `Dockerfile`/`cloudbuild.yaml`/`.github/` may change.
5. Every legal-adjacent response (Estate demo included) must carry
   `flagged_for_review: true` and the exact unauthorized-practice warning
   already defined in `demo_counsel.py`.
6. All new Python passes `python3 -m py_compile`; full suite passes with
   `python3 -m unittest discover tests`.

---

## PART 1 — URL hygiene (fixes finding A)

1. In `demo.html`, `demo-signal.html`, `demo-counsel.html`: make **every**
   `href`/`src` root-absolute (`/assets/css/styles.css`,
   `/assets/js/nav-mobile.js`, `/counsel.html`, `/index.html`, `/demo`,
   `/demo/signal`, `/demo/counsel`, `/walkthrough.html`, …). No relative
   URLs may remain in any `demo*.html`.
2. Add to the `<head>` of all three demo pages (and the two new demo pages
   from Part 3): `<link rel="icon" href="/assets/svg/favicon.svg" type="image/svg+xml">`
   plus `og:title`, `og:description`, `og:url` meta tags.
3. Regression tests (extend `tests/test_demo_signal.py` or a new
   `tests/test_demo_pages.py`):
   - `GET /demo/signal` and `/demo/counsel` bodies contain
     `href="/assets/css/styles.css"` and contain **no** `href="assets/`
     or `src="assets/` substrings.
   - `GET /demo/assets/css/styles.css` returns 404 (documents the trap).

## PART 2 — Site wiring + dead-end removal (fixes B, C, D)

1. **Walkthrough:** remove `walkthrough.html` from the
   `legacy_marketing_page` redirect list and serve it via `serve_page`
   (routes `/walkthrough` and `/walkthrough.html`). Skim the page; if its
   nav differs from `signal.html`'s, leave the page content alone — only
   ensure it loads and add one prominent "Try the live demos →" button
   (→ `/demo`) near the top. If the file proves unsalvageably outdated,
   instead repoint every demo-page CTA from `/walkthrough.html` to `/#demo`
   — but serving the real page is strongly preferred.
2. **Homepage discoverability:** in `index.html`:
   - Add a `Live Demos` item to the main nav (and to the Resources dropdown
     if present) linking `/demo`.
   - In the "See MIZOKI3 in Action" section, add a primary CTA button
     "Run the live demos — no login" → `/demo`.
   - Add `Live Demos → /demo` to the footer link column.
   Do not restructure anything else on the homepage.
3. **Sign In loop:** make the external URLs configurable:
   `EXTERNAL_LOGIN_URL = os.environ.get("MIZOKI_EXTERNAL_LOGIN_URL", "/admin/login")`
   and `EXTERNAL_DASHBOARD_URL = os.environ.get("MIZOKI_EXTERNAL_DASHBOARD_URL", "/console")`.
   With the env vars unset, Sign In lands on the local `/admin/login` page
   (which renders) instead of the looping subdomain. Update tests that
   assert the old redirect targets.
4. **Division pages:** add the same hero "See it live" button pattern used
   on `signal.html`/`counsel.html` to `estate.html` (→ `/demo/estate`),
   `capital.html` (→ `/demo/capital`), `risk.html` (→ `/demo/risk`), using
   each page's accent color (emerald `--accent-emerald` for Estate, amber
   `--accent-amber` for Capital, rose `--accent-rose` for Risk). Add a
   `Live Demos` nav item (→ `/demo`) to all five division pages' navs.

## PART 3 — Three new division demos (fixes E)

Build three engines + pages + JS following the established patterns. All
deterministic, seeded, stdlib-only. Register MCP tools for each
(`demo.estate.*`, `demo.capital.*`, `demo.risk.*`, category `demo`) and add
public JSON APIs mirroring the existing ones. Update `demo.html` from a
2-card hub to a 5-card hub (one card per division, each with its accent
color).

### 3.1 Estate Room — `mizoki_runtime/demo_estate.py` (+ `demo-estate.html`, `assets/js/demo-estate.js`)
Pattern: Counsel-style scripted engine. Three scenarios:
- `ct_estate_settlement` — settle a CT estate: generates the five statutory
  clocks (30-day filing, 60-day inventory, 150-day creditor bar, 150-day
  elective share, 183-day CT-706/NT) as an interactive timeline with
  deadline badges and dependency arrows.
- `gst_dynasty_review` — three-generation trust map: renders a family/trust
  graph (SVG) with per-node transfer-tax exposure and the GST grandfather
  flag; reuses the authority corpus from `demo_counsel.py` (import it — do
  not duplicate the list).
- `basis_step_up` — asset table showing pre/post-death basis under
  IRC § 1014 with deterministic valuations.
API: `GET /api/demo/estate/scenarios`, `POST /api/demo/estate/run`
(`{scenario_id, seed?}`). Every response carries the compliance flag +
warning (constraint 5). UI: timeline strip, SVG graph panel, asset table,
persistent disclaimer footer — Estate emerald accent.

### 3.2 Capital Desk — `mizoki_runtime/demo_capital.py` (+ `demo-capital.html`, `assets/js/demo-capital.js`)
Pattern: Signal-Factory-style pipeline (reuse `ReLUGate` and `GuardrailSet`
by import; add one new guardrail `covenant_headroom` — block any allocation
that drops modeled covenant headroom below 15%). Three scenarios:
`growth_reallocation`, `debt_paydown_vs_buyback`, `working_capital_stress`.
Each run: candidate capital moves → gate → guardrails (exactly one
deliberate `covenant_headroom` block per scenario — the red moment) →
ranked allocation → dry-run execution with rollback tokens → funnel +
provenance decision card. API mirrors signal (`run`, `scenarios`, plus an
SSE `stream` endpoint reusing the same frame vocabulary). UI mirrors
`demo-signal.html` with amber accent; link `/console` as "see the static
console mock" secondary CTA.

### 3.3 Risk Sentinel — `mizoki_runtime/demo_risk.py` (+ `demo-risk.html`, `assets/js/demo-risk.js`)
Pattern: hybrid. A stream of 12–16 seeded enterprise events (contract
clause change, spend spike, PII access anomaly, covenant drift) flows
through a severity×likelihood matrix; the engine escalates exactly two
events per scenario — one auto-mitigated (green), one vetoed and routed to
a human (red, mirroring the ACT-991 story on `/console`). Scenarios:
`quarterly_close`, `vendor_breach_drill`, `campaign_compliance`. Every
veto record includes rule id, evidence chain, and rollback token. API:
`scenarios` + `run` (+ optional `stream`). UI: event feed, 5×5 risk matrix
(cells light up as events land), veto banner, audit-trail card — rose
accent.

## PART 4 — Serving hardening (fixes F)

1. Locate the gunicorn invocation (Dockerfile `CMD`). Ensure it runs with
   `--workers 2 --threads 8 --timeout 120` (or equivalent gthread setup).
   Change nothing else in the Dockerfile.
2. Confirm all SSE endpoints send `Cache-Control: no-cache` and
   `X-Accel-Buffering: no` (signal already does; new capital stream must).

## PART 5 — Tests

Extend the suite (keep the existing 122 green):
- Part 1 regression tests (absolute-URL assertions, 404 documentation).
- Walkthrough: `GET /walkthrough.html` → 200, contains "Try the live demos".
- Homepage: `GET /` body contains `href="/demo"`.
- Login: `GET /login` redirects to `/admin/login` when env vars unset.
- Per new demo (×3): determinism (same seed ⇒ identical run), scenario
  validation (unknown id → 400), exactly-one-block/veto invariants, MCP
  tool registered + callable via `POST /api/mcp/call`, and — for Estate —
  compliance flag + exact warning text on every response, authorities drawn
  from the shared corpus. Capital stream: frame ordering + `done` terminal.
- Update `tests/test_runtime.py` expected-tool set with the new
  `demo.estate.*` / `demo.capital.*` / `demo.risk.*` names.

## PART 6 — Verification & delivery (all must pass)

```bash
cd "# MIZ OKI 3.5"
python3 -m py_compile app.py mizoki_runtime/runtime.py \
  mizoki_runtime/demo_signal.py mizoki_runtime/demo_counsel.py \
  mizoki_runtime/demo_estate.py mizoki_runtime/demo_capital.py \
  mizoki_runtime/demo_risk.py
python3 -m unittest discover tests
python3 - <<'EOF'
from app import create_app
c = create_app().test_client()
for p in ("/demo", "/demo/signal", "/demo/counsel", "/demo/estate",
          "/demo/capital", "/demo/risk", "/walkthrough.html"):
    print(p, c.get(p).status_code)
body = c.get("/demo/signal").data.decode()
assert 'href="/assets/css/styles.css"' in body and 'href="assets/' not in body
print("URL hygiene OK")
EOF
```

Finish with a summary of files added/modified, endpoint + MCP tool list,
test counts before/after, and a ≤10-step sales script per NEW demo page.

Do NOT deploy directly. Commit on a `claude/demo-fixes-v2` branch, merge to
`main` after review; the existing deploy workflow ships it. After deploy,
manually spot-check on production: `/demo/signal` renders with the styled
nav, all five demo pages load, `/walkthrough.html` serves, homepage nav
shows Live Demos, and Sign In no longer loops.
