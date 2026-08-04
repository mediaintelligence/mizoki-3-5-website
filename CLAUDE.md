# CLAUDE.md - AI Assistant Context

## Project Overview

**MIZ OKI 3.5** is a Verifiable Autonomous Decision Intelligence Platform. This repository contains the marketing website deployed on Google Cloud Run.

## 🔒 DESIGN CANON & DEPLOY GOVERNANCE — READ FIRST (2026-07-30)

**The v1.5 "night dossier" look and feel is the LOCKED source of truth**, and
`/demo` + the Executive Briefing are the core of the operation. The canon is
pinned in [`canon.lock.json`](canon.lock.json) (19 core surfaces, sha256) and
documented in [`docs/DESIGN_CANON.md`](docs/DESIGN_CANON.md).

**Every production upload requires specific human approval.** The deploy
workflow (`.github/workflows/deploy-homepage.yml`) is manual-dispatch-ONLY and
demands a typed `APPROVED` token plus a passing canon check
(`python3 scripts/check_design_canon.py`). There is no push-triggered deploy
and the Deploy Router no longer matches this workflow.

Rules for any agent or human working here:

1. Do NOT modify the files listed in `canon.lock.json` without an explicit,
   specific human instruction for that change.
2. If a change is human-approved, re-pin with
   `python3 scripts/check_design_canon.py --update` and commit the lockfile
   together with the change.
3. Never dispatch the deploy workflow yourself — a human runs it from the
   Actions UI and types `APPROVED`.
4. Homepage content is additionally fingerprint-governed (16-item suite;
   sha256 `35a7e5d3…66ac08ac`).

---

## Architecture

- **Deployment**: Docker container on Google Cloud Run
- **Web Server**: Python Flask application served via Gunicorn
- **Domain**: mizoki3.com (Cloud Run custom domain)
- **Routing**: Client and API routes managed natively in Flask (`app.py`)

## Core Technology (7-Stage SRPVDAL Pipeline)

```
SENSE → REASON → PLAN → VALIDATE → DECIDE → ACT → LEARN
```

Key innovations:
- Decision Control Plane (DCP)
- Validation & Arbitration Layer
- Counterfactual Simulation Engine
- Temporal-Causal Knowledge Graph (TCO-KG)

---

## Repository Structure

```
mizoki-website/
├── index.html                    # Homepage
├── how-it-works.html             # Technical deep dive
├── platform.html                 # Architecture overview
├── security.html                 # Security & compliance
├── industries.html               # Industry templates
├── pricing.html                  # Pricing tiers
├── case-studies.html             # Customer success stories
├── resources.html                # Documentation hub
├── roi.html                      # ROI calculator
├── walkthrough.html              # Demo request
├── investor.html                 # Investor overview
├── sales-one-pager.html          # Sales summary
│
├── blog/                         # Thought leadership content
│   ├── index.html                # Blog listing
│   ├── decision-control-plane.html
│   └── relu-lens-meta-algorithm.html  # ReLU Lens article
│
├── assets/
│   ├── css/                      # Stylesheets
│   ├── img/
│   │   ├── relu-article/         # LinkedIn article images (5 SVGs)
│   │   ├── relu-carousel/        # LinkedIn carousel slides (8 SVGs)
│   │   ├── preview.html          # Image preview page
│   │   └── README.md             # Image kit documentation
│   └── pdf/                      # Downloadable resources
│
├── app.py                        # Python/Flask routing engine
├── mizoki_runtime/
│   ├── __init__.py
│   └── runtime.py                # Boss runtime, MCP registry, GraphRAG, KG, and graph-native SRPVDAL loop
├── tests/
│   ├── test_app.py               # Flask API coverage
│   └── test_runtime.py           # Boss/MCP runtime coverage
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition (Gunicorn)
├── nginx.conf                    # Legacy Nginx config (deprecated)
├── cloudbuild.yaml               # Cloud Build config
├── deploy.sh                     # One-click deploy to Cloud Run
├── master-deploy.sh              # Full deployment (Cloud Run + GitHub)
├── github-push.sh                # GitHub sync script
└── README.md                     # Project documentation
```

---

## Deployment Commands

### One-Click Master Deploy
```bash
./master-deploy.sh YOUR_GCP_PROJECT_ID https://github.com/YOUR_USERNAME/mizoki-website.git
```

### Deploy to Cloud Run Only
```bash
./deploy.sh
```

### Push to GitHub Only
```bash
./github-push.sh
```

## Production secrets

`cloudbuild.yaml` deploys with `--set-secrets` so two values are read from Secret Manager at runtime:

| Secret | Env var | Purpose |
|:-------|:--------|:--------|
| `mizoki-website-secret-key` | `SECRET_KEY` | Flask session signing key (pinned → sessions survive restarts) |
| `mizoki-website-demo-users` | `MIZOKI_DEMO_USERS_JSON` | `{email: password}` map for `/admin/login` |

One-time setup is documented in `docs/PRODUCTION_SECRETS_SETUP.md`. The deploy also sets `ENVIRONMENT=production` (flips session cookies to `Secure`) and `MIZOKI_REQUIRE_AUTH_FOR_APIS=false` (public API surface; set to `true` to gate `/api/mcp/*` and `/api/boss/*` behind admin sign-in).

## Backend admin

A real admin dashboard lives at `/admin` (auth-gated by Flask session):

- `GET /admin/login` — sign-in form
- `POST /admin/login` — validates against `MIZOKI_DEMO_USERS_JSON`
- `GET /admin` — runtime health, MCP tool grid, in-browser tool runner, recent decision traces
- `GET /admin/logout` — clear session

`/api/health` is always public. `/api/mcp/*` and `/api/boss/*` are public **by default** so the on-page chat demo keeps working; flip `MIZOKI_REQUIRE_AUTH_FOR_APIS=true` to require an admin session.

## Blog feeds

- `GET /blog/feed.xml` — RSS 2.0
- `GET /blog/feed.json` — JSON Feed 1.1
- `GET /blog/posts.json` — raw manifest

All three are rendered from `blog/posts.json`; add a new post by dropping `blog/<slug>.html` and appending an entry to the manifest.

## Site-wide mobile / iPad nav

`assets/js/nav-mobile.js` is a single shared script wired into every page with `<script src="/assets/js/nav-mobile.js" defer></script>`. It auto-detects `.nav-links`, injects a 44×44 hamburger + slide-down sheet, and is theme-aware (works on both dark `index.html` and light `theme-light` pages).

---

## Live demo platform (July 2026)

Five-division + Nexus demos are first-class Flask routes (not static-only). `/api/demo/*` is **public** (not gated by `MIZOKI_REQUIRE_AUTH_FOR_APIS`).

| Page | Player / engine |
|:-----|:----------------|
| `/demo` | Hub |
| `/demo/signal` | `demo-signal.js` + Signal engine |
| `/demo/counsel` | Counsel Room |
| `/demo/estate` | `demo-estate.js` |
| `/demo/capital` | `demo-pipeline.js` + **`demo-capital.js`** + SSE `/api/demo/capital/stream` |
| `/demo/risk` | `demo-risk.js` |
| `/demo/nexus` | `demo-nexus.js` |
| `/walkthrough` | Guided walkthrough — **root-absolute** CSS/nav only |
| `/login` | Redirects to `/admin/login` |

Engines live under `mizoki_runtime/demo_*.py`. MCP tools: `demo.*.list_scenarios` / `demo.*.run`. Gunicorn: `2` workers × `8` threads, **`--timeout 120`**.

**Hygiene (PR `#580`, July 22):** division/walkthrough absolute asset URLs; Sign-In links use `/login` (never hardcode `mizoki.mizoki3.com`); named Capital JS entrypoint. Notes: `docs/DEMO_V4_BUILD_NOTES.md`.

```bash
python -m unittest discover tests   # includes test_demo_platform, test_demo_capital, …
```

---

## Recent Work (August 2026)

### MIZ OKI Media standalone site LAUNCHED — /media Parts 2–4 (2026-08-04)

Owner four-part deployment prompt executed in full and deployed on explicit
owner approval ("Approved deployment" in-session; dispatch per the workflow's
own governance clause — explicit human instruction). Deploy: this repo PR
`#28` (main `00cd7ea`) → parity PR `#591` in MIZOKICloudRun (`bc154c0`, base
surfaces byte-verified before copy) → canonical `deploy-homepage.yml` run
**#53** (`approve=APPROVED`, all gates green, success in ~110s). Production
verified from the live domain: all 9 pages 200, film `video/mp4` with Range
206, classic root 200 with ZERO `/media` references, `/media-buying` 301
intact.

- **/media is a complete standalone product site**: 12-section homepage in
  the owner's required order (customer-problem wall → 5×11 capability table →
  interactive Decision Graph + four memory layers → expandable SENSE→LEARN
  flow → reworked scenario (landing-page + inventory diagnosis, approval
  routed to Operations) → film + verbatim transcript → decision jobs →
  architecture → pilot → governance → CTA) plus 8 sub-pages:
  `/media/{platform, decision-graph, how-it-works, use-cases, pilot, trust,
  resources, contact}` — served by ONE additive `any()`-converter route in
  `app.py` (the `/marketing` convention).
- **Route-local design system** `media/assets/media.css` (sub-pages only;
  the homepage stays fully inline/self-contained, test-pinned). Downloadables:
  product overview, Decision Graph overview, pilot guide, executive summary
  (print-friendly single-file HTML), architecture SVG, film transcript.
- **Interactive walkthrough** on `/media/how-it-works`: CPA slider →
  hypothesis weights rebalance → policy checks → routing/escalation. STRICTLY
  deterministic (no randomness, no clock reads — test-enforced across every
  /media page), aria-live verdicts, noscript fallback, all values labeled
  illustrative.
- **Truth discipline held against the prompt**: the mandated "two-minute
  film" caption was NOT adopted — the real asset is a 32s silent placeholder
  (its own footer: "final narrated film pending"), so the page says "silent
  preview render" and the transcript quotes the actual on-screen text
  (frames extracted and read). Zero buzzwords (swept), no compliance-cert
  claims, every number labeled.
- **Tests**: `tests/test_media_page.py` 20 → **49** (required section order,
  question wall, comparison grid, node/flow contracts, scenario story,
  per-page SEO/a11y/isolation, internal-link crawl, deterministic-JS guard,
  content_qa over every /media page, classic-site-untouched). Suite **415**
  with only the 2 pre-existing homepage failures; canon 20/20.
- **Deferred deliberately**: `/media` not yet in the sitemap (one line in
  `app.py` when ready to index); drift guard not yet extended to the 8
  sub-pages (extend in BOTH repos together); final narrated film + `.vtt`
  captions pending; Part 4's "beyond the website" items (product tour, ROI
  calculator, industry selector, sandbox, docs portal, …) recorded as
  roadmap, not built.

### /media go-live + parity route-loss repair + media-aware drift guard (2026-08-04)

Owner instruction: "Approved to go live in production mizoki3.com/media."
Deployed via canonical `deploy-homepage.yml` run **#52** (typed `APPROVED`,
sha `1577206`, green in ~110s). Production verified from the live domain:
`/media` 200 with the owner's **MIZ OKI Media — Causal Growth Control** page;
`/media/video/mizoki-signal-explainer.mp4` streams as seekable `video/mp4`
(302 KB, `accept-ranges: bytes`); traversal probes (`..%2f`, unknown files)
404; `/intelligence` + `/vision` 200 (the audit-fix routes for `/contact`'s
dangling links — 404 before this deploy, so their flip proves the revision);
blog clean routes + canonical-https feeds live; root still has ZERO
`/marketing` references; `/media-buying` still 301s; covenant-veto API smoke
`funnel.executed == 0`; `/api/health` healthy with admin login enabled.

- **Defect caused, caught, and fixed pre-deploy (recorded honestly)**: the
  2026-08-03 parity byte-copy (`4e2db84` in MIZOKICloudRun) overwrote
  canonical `app.py` and silently dropped two concurrent commits' routes —
  the owner's `/media` block (`9fb05d7`, which run `#51` had already put in
  production) and the signal-rollout blog article routes + canonical-https
  feed fix (`5ed94c5`). Caught during pre-deploy verification of this
  go-live (a grep for the `/media` route on canonical main returned 0); a
  deploy from main in that window would have taken `/media` DOWN. Nothing
  broken was ever deployed. **Binding lesson: parity is a UNION merge, never
  a byte-copy** — before copying `app.py` across repos, diff against the
  other repo's HEAD for routes that exist only there.
- **Fix**: rebuilt the verified union `app.py` — marketing site + `/media`
  page + traversal-guarded asset route (suffix allowlist, resolved-path
  prefix check) + blog routes + https feeds + `/intelligence` + `/vision` —
  byte-identical in both repos (website PR `#26` = `38a1d65`; canonical
  `1577206` auto-merged from `claude/media-route-restore-union`).
- **Guard extended so this failure mode is structurally impossible**:
  `scripts/check_marketing_surfaces.py` now also asserts `media/index.html`
  (via its "Causal Growth Control" content marker), the explainer film file
  on disk, and the `/media` route marker in `app.py` — gating BOTH deploy
  pipelines (canonical `deploy-homepage.yml` and this repo's
  `deploy-cloudrun.yml`) and running in-suite via `DriftGuardTestCase`.
- Gates on the deployed tree: canon 20/20 · content-QA clean (self-test +
  10 files) · marketing+media guard OK · suite **386** (only the 2
  pre-existing homepage failures).

### Signal v2 capability site + doorman story rollout + truth-discipline CI gate (2026-08-03)

Owner runbook (`drop/claude-code-prompt-signal-page-rollout.md`) executed in
full and LIVE (deploys `#48` sha `98b4184`, `#49` sha `6db204c` — both
`workflow_dispatch` + `APPROVED` on explicit owner instruction). Record:
`docs/reports/SIGNAL_V2_ROLLOUT_PR.md` (repo root).

- **`/signal` is now a six-page media-buying capability site**: the hub (9
  filed §-sections; owner-supplied v2 + Field Notes merged as §04) plus
  `/signal/{thresholds,budget,creative,audiences,measurement}` — ReLU
  threshold discovery, ReLU-gated reallocation + pacing clamps + staged
  rollout rails, creative fatigue/rotation, uplift cohorts, and the
  caused-vs-anticipated measurement ledger. **Every number is a Boss-module
  operating default read from source** (relu_threshold_agents,
  autonomous_budget_reallocation_mvp, uplift_pacing, creative_fatigue,
  uplift_guardrails.yaml, ai_marketing_optimization,
  cross_platform_attribution), framed "operating defaults, not promised
  outcomes". Pre-rollout page preserved at `archive/signal-v1.html.bak`.
- **Doorman story propagated**: one framing sentence each on `/demo` +
  `/demo/signal`; briefing signal pack extended (statusQuo doorman line,
  `9 of 14 (composite)` proof metric, privacy-posture talking point —
  owner-approved diff, canon re-pinned); story bank canonical at
  `docs/marketing/signal-story-bank.md` with governance pointers in both
  CLAUDE.mds; **"The Doorman Problem" published** at `/blog/doorman-problem`
  (manifest, card, clean route + 301 shims, feeds; post-count contract 3→4).
- **Truth discipline is now a CI gate**: `scripts/content_qa.py` runs in
  `deploy-homepage.yml` beside the canon check and in the suite
  (`tests/test_content_qa.py`). Fails on affirmative mind-reading/guaranteed
  or deployed-intent claims, intent copy without "Preview · in development"
  in-section, %/× numbers without illustrative/composite/operating-default
  labels in-section, §-sequence breaks — and **self-tests on seeded
  violations before every scan** (a gate that can't fire fails the build).
  First run found 23 real findings, all fixed (incl. preview framing on the
  demo-signal ORACLE section + one `(composite)` per briefing domain).
  Post-deploy hardening: §-extractor matches multi-class markup and refuses
  vacuous passes (`9d6c5a1`).
- **Blog hygiene (finish-all pass)**: feeds emit canonical https URLs
  (were proxy-scheme http); clean routes + 301 shims added for
  `decision-control-plane` and `adc-decision-framework` (their feed links
  had 404'd since the feeds shipped); index cards use clean URLs.
- **Sitemap**: rollout pages carry `lastmod 2026-08-03`; `/blog` lastmod
  derives from the manifest.
- **Tests**: suite **365** with only the 2 pre-existing homepage failures;
  canon 20/20 (re-pins for demo.html, demo-signal.html, data.js were
  owner-approved); marketing drift guard green; Playwright passes on all six
  signal pages + briefing/demo renders.

### Marketing parallel site under /marketing (2026-08-02)

Owner instruction: "launch this entire site under a /marketing so i can compare
them online before taking anything offline." The proposed media-buyer
experience (the mizoki3.com master implementation prompt, translated from its
React/TSX plan into this repo's static-HTML + Flask architecture) runs as a
complete parallel site — the classic canon site at root is UNTOUCHED and the
canon check still passes on all 20 surfaces. Purely additive; nothing redirects
away from the classic site, and the homepage does not link into /marketing
(comparison is one-way by design, test-enforced).

- **Pages** (`marketing/`): `/marketing` — full landing (mandated hero verbatim,
  problem-vs-solution matrix, vocabulary translation ledger, 7-stage Decision
  Control System accordion, Interactive Scenario Simulator, 90-sec storyboard);
  `/marketing/simulator` and `/marketing/walkthrough` — dedicated deep-link
  pages sliced from the same markup (shared element IDs). All three carry a
  fixed-height amber "Parallel preview — nothing on the classic site is
  replaced" strip linking back to `/`.
- **Vocabulary key is binding on this surface** (test-enforced): Canonical
  Event Envelope → Structured Signal Evidence · Temporal-Causal Knowledge Base
  → Cross-Stack Root Cause Engine · Domain Intelligence Cell → Channel
  Intelligence Modules · SRPVDAL Loop → 7-Stage Decision Control System ·
  Immutable Learning Ledger → Compounding ROI Memory. Engineering terms appear
  exactly once each, in the on-page translation ledger; sub-pages carry zero
  raw jargon.
- **Shared assets**: `assets/css/marketing.css` (one stylesheet, three pages —
  no drift) + `assets/js/media-sim.js` (accordion + simulator + storyboard
  player; init is element-presence-gated so subset pages just work). The
  simulator is DETERMINISTIC — no `Math.random`, no `Date.now`; the replay id
  is a hash of the inputs; the red veto is slider-reachable (latency > ~5.2s
  under the 2.2× ROAS floor) and vetoes still record to memory. Claims-linted
  against the house banned list on every surface.
- **Routing**: `/marketing[/…]` with `strict_slashes=False`;
  `/media-buying(.html)` 301s to `/marketing` (interim path from the first
  build, never deployed); sitemap lists the three pages, not the redirect.
- **FULL-SITE MIRROR (owner follow-up: "it only shows me signals page and does
  not currently replace the whole site")**: the ENTIRE site is browsable inside
  the prefix. `/marketing` home gained a five-division grid + live-demos band;
  `_marketize()` in `app.py` serves `/marketing/{counsel,estate,capital,signal,
  risk,pricing,demo}` + `/marketing/demo/<desk>` (all six) by reading the SAME
  canon files off disk (never modified — canon check stays green), rewriting
  whitelisted internal links (incl. `.html` variants — pricing self-links as
  `/pricing.html`) to stay under the prefix, and injecting the compare strip +
  `noindex` (mirrors must not compete with canonical pages in search). The
  Executive Briefing passes through chrome-less at
  `/marketing/executive-briefing/` (relative assets just work). Strip escape
  hatch (`href="/"`) is injected AFTER rewriting so it keeps pointing at the
  classic site. Mirrored demo desks run the real engines/APIs.
- **Full-site prompt v2 integrated (owner, 2026-08-03)**: vocabulary key now
  8 entries — adds Decision Control Plane/Eligibility Layer → **Safety
  Guardrail Engine**, Tenant Isolation & Boundary → **Enterprise Privacy &
  Security Shield**, No-Action Counterfactual Baseline → **"Do Nothing"
  Opportunity Cost Check**, and renames the loop **7-Stage Governed Decision
  System** (was "Decision Control System"). Three new real pages:
  `/marketing/engine` (7-stage walkthrough), `/marketing/modules` (Google Ads /
  Meta & Paid Social / E-Commerce & Inventory / ESP & Retention Channel
  Intelligence Modules), `/marketing/governance` (Observe / Bounded / Full
  autonomy modes + the security shield). Homepage adds the **Full-Stack Signal
  Grid** (ad networks / infrastructure / inventory / finance guardrails →
  Structured Signal Evidence bus); CTA is "Launch Live Decision Simulator";
  proof strip reads Monitored / <100ms / Policy Protection; storyboard scenes
  retitled (Nightmare / Redefining Cross-Stack Signals / Finding the True Root
  Cause / 1-Click Governed Approvals / Compounding Organizational Memory).
  **Divisions reframed as initial MVPs** per owner ("not just 5"): heading
  "One decision loop. Any division.", MVP lede, sixth dashed "+ Your division"
  card → `/marketing/modules`. The prompt's `#090D16`/indigo/emerald theme was
  deliberately NOT adopted — the locked night-dossier tokens remain the design
  system unless the owner asks to re-skin.
- **COMPLETE-SITE TRANSPARENT REDESIGN (owner, 2026-08-03: "This page still
  only reflects the signals page and not complete web site redesigned in a
  more transparent way")**: the five division pages + pricing are no longer
  mirrors — they are REAL redesigned pages in `marketing/` written in the
  translated vocabulary: each division carries a plain-English hero, the
  house "What we say / What we never say" claim strip, a Watches / Decides /
  Never-does contract grid, and a worked decision from its real live desk
  (capital = the covenant veto; signal = the pixel-drift refusal; counsel =
  the conflict banner; risk = the veto that held; estate = operational
  triage), wired to `/marketing/demo/<desk>`. `marketing/pricing.html` maps
  the three tiers onto the three autonomy modes, jargon-free. The homepage is
  platform-first: a hero addendum names Capital/Risk/Counsel/Estate
  explicitly and `#divisions` moved above the media-buying matrix
  (order test-enforced). Only the demo hub + six desks remain mirrored — the
  desks ARE the product, identical in both sites.
- **Tests**: `tests/test_marketing_site.py` (57) — suite **345**, only the 2
  pre-existing homepage failures. Playwright: 27/27 core + 9/9 mirror,
  zero page errors on the redesigned pages.
- **Media-acquisition showcase — software facts only (owner, 2026-08-03)**:
  `marketing/signal.html` gained `#acquisition` (8 capability cards: ReLU
  threshold intelligence, ReLU-gated budget reallocation, value-based bidding,
  creative fatigue, uplift pacing, uplift audiences, attribution &
  measurement, promotion gates & consent) + `#parameters` (source-of-truth
  table). Owner mandate: "every number on these pages is a software fact, not
  marketing memory" — the sections are GENERATED from the runtime
  (`demo_signal.GATE_UPLIFT_FLOOR` 5% · `GATE_CONFIDENCE_FLOOR` 0.70 ·
  `GATE_SAMPLE_FLOOR` n=15 · `GuardrailSet` ±20%/±30% swing caps · seed 42 ·
  the +12% campaign_7 $8,400/0.86/n=48 winner and the deliberate +25% block ·
  media-sim.js 2.2×/$5,000/35%/3.1×), each row cites its module constant, and
  `AcquisitionShowcaseTestCase` re-imports the runtime so the page FAILS THE
  BUILD if it drifts from the code. Live-vs-spec chips keep honesty (spec
  items: uplift pacing/audiences, promotion gates Brier ≤ 0.20 · AUC ≥ 0.72 ·
  lift ≥ 2 cycles, observe-only default). Capability cards deep-link seeded
  demo runs (`/marketing/demo/signal?scenario=…&seed=42` — embedding
  verified). Suite **350**; Playwright acquisition pass 5/5 (deep link
  autoruns the real engine).
- **DUAL-PIPELINE PARITY + DRIFT GUARDS (owner, 2026-08-03: "ensure that we
  never have issues with losing proper site online")**: the complete
  /marketing site was PORTED into MIZOKICloudRun's `# MIZ OKI 3.5/`
  (PR `#588` there — base files verified byte-identical to the last parity
  point before copying; their newer 2026-08-02 self-contained `signal.html` +
  updated `test_demo_platform.py` were preserved and mirrored BACK here in
  PR `#23`). New `scripts/check_marketing_surfaces.py` (stdlib-only: 12 pages
  non-stub, engine/stylesheet/tests present with content markers, `app.py`
  route markers) is wired into BOTH deploy workflows — MIZOKICloudRun
  `deploy-homepage.yml` beside the canon check, and this repo's
  `deploy-cloudrun.yml` (which previously ran no canon check at all; PR
  `#22`) — plus `DriftGuardTestCase` runs the same gate inside the suite.
  Neither pipeline can ship a tree missing the canon surfaces or the
  marketing site; every meaningful surface is byte-identical across the two
  repos (diff-verified).
- **LAUNCHED 2026-08-03** — owner quoted the canonical launch step verbatim
  and approved; per the workflow's own governance ("unless a human has
  explicitly instructed the deploy") the canonical `deploy-homepage.yml` was
  dispatched with `approve=APPROVED` (run `#47`, sha `cd6e3c2`, green in
  ~2 min: token + canon check + marketing drift guard + Cloud Build).
  Production verified from the live domain: root 200 with ZERO `/marketing`
  references (classic untouched), `/marketing` 200 with hero + compare strip,
  `/marketing/signal#acquisition` live, seeded deep link embeds
  `data-scenario="ecommerce_roas" data-seed="42"`, `/media-buying` 301 →
  `/marketing`, `/marketing/governance` 200. Root and `/marketing` now run
  side by side in production for the owner's online comparison; nothing went
  offline.

Owner defect report, verbatim: "the demo does not have any voice at all and the
chat is very limited and also does not have voice conversation options." Root
cause: the docent only activated on `/demo/signal` (`startBtn`+`stageStrip`
gate), and the only chat anywhere was the concierge's narrow briefing box.
Closed platform-wide:

- **`assets/js/boss-docent.js` rewritten as a multi-desk engine** with
  per-page profiles (`MizokiBossDocent.init({page})`, wired on all 7 pages
  with `?v=20260802` cache-busting):
  - `hub` — welcome/orientation tour on `/demo` (no run to drive);
  - `signal` + `capital` — the full **pipeline tour** (they share the SRPVDAL
    pipeline DOM: eventRail → ReLU gate → red validate → decision card);
    capital's beats narrate the covenant-headroom veto;
  - `estate` + `risk` — **watch tours**: docent presses Start, narrates the
    desk's mid-run beats, then reads `#finaleHead`/`#finaleSummary` off the
    run's own DOM; `nexus` reads `#triggerCard` when `#provenancePanel` lands;
  - `counsel` — **consult tour**: docent clicks a scripted scenario card,
    waits for `#synthPanel.on`, reads `#conflictBanner` verbatim if raised.
- **Launcher is a fixed bottom-right pill on EVERY viewport** — the voice must
  be discoverable without scrolling (that was the real "no voice" experience).
- **ASK THE BOSS on every demo page** — typed in, answered ALOUD (TTS) and
  always captioned. Answers come from the same allowlisted fact pack as the
  concierge (`POST /api/briefing/guide/ask`, tagged `stage="demo"`,
  `domain=<desk>` so ledger analytics segment demo traffic). No generative
  path, unknowns logged for human follow-up.
- **Fact pack +6 demo-facing topics** (`mizoki_runtime/briefing_guide.py`):
  `desks`, `oracle_intent`, `replay_seed`, `pilot_path`, `boss_agent`,
  `voice_output_only` — the "chat is very limited" half of the report.
- **Decision Concierge voice replies** (`executive-briefing/js/guide.js`):
  🔊/🔇 toggle in the rail header (off by default — the toggle tap is the TTS
  user gesture), speaks coach lines, resolved/handoff lines, and answers;
  `cancel()` only ever BEFORE queueing (the 2026-07-31 wedge rule).
- **Voice stays OUTPUT-ONLY everywhere** — no microphone, no speech
  recognition, no audio capture, test-enforced in BOTH JS layers. "Voice
  conversation" is deliberately typed-in → spoken-out; enabling audio capture
  would reverse the ORACLE bright line and needs an explicit owner decision.
- **Engine hardening**: a throwing `u.voice` assignment (stale voice object)
  could escape `sentence()` before the safety timer armed and wedge the tour
  forever — now contained; the tour survives with the engine-default voice
  (proven in Playwright with the native utterance class rejecting a foreign
  voice object).
- **Soft-sell discipline generalized**: the pilot CTA is BUILT exactly once
  (`"/contact?source=demo-" + desk + "-docent"`, count test == 1) and the
  shared "No pressure" close appears exactly once in source.
- **Tests**: suite **288** with only the 2 pre-existing homepage failures;
  9-surface Playwright pass (hub desktop+mobile, capital/estate/counsel
  end-to-end, risk/nexus/signal spoken intros, briefing voice toggle) with
  zero speak→cancel adjacency in the instrumented speech log.
- Canon re-pinned in the same commit: 7 demo pages + `executive-briefing/
  index.html` + `guide.js` (boss-docent.js and briefing_guide.py are not
  canon-pinned but ship in the same commit).

## Recent Work (July 2026)

### Decision Concierge — guided-by-default Guide Agent on /executive-briefing/ (2026-07-31)

Executive Briefing v1.1 per owner spec (full spec: `docs/GUIDE_AGENT_SPEC.md`).
The guide IS the product story — live DCP-style control: suggest + highlight +
unlock; the executive commits every critical action.

- **`executive-briefing/js/guide.js`** (NEW, canon-pinned — canon is now 20
  surfaces): docked concierge rail, guided by default
  (`MIZOKI_CONFIG.guideMode`, sessionStorage persistence), stage×domain×role
  scripts driven by `MIZOKI.DOMAINS`/`MIZOKI.ROLES`, objection chips, Q&A box,
  role-recommended close default (pilot/board/deep-dive). **Zero click()
  calls** (test-enforced) — it pulses/scrolls targets, never presses them; the
  critical red-signal gate is coached by name, never bypassed. While open the
  page reserves the rail's space (`html.mzg-docked`) so the panel can never
  intercept a briefing control (Playwright caught that exact overlap pre-ship).
- **`app.js`** gained the `mizoki:briefing` CustomEvent bridge inside
  `notifyParent` (state-enriched); **`index.html`** loads guide.js — both
  re-pinned.
- **Server**: `mizoki_runtime/briefing_guide.py` — allowlisted PRODUCT_FACTS +
  6-entry objection bank (integration_risk / existing_bi / security / not_now /
  budget_owner / pricing), keyword retrieval (NO generative path — cannot
  invent pricing, certifications, or logos), and the interaction memory ledger
  (`data/guide_interactions.jsonl`). Flask: `/api/briefing/guide/event|ask|
  summary`. Boss runtime registers `guide.answer` + `guide.memory_summary` MCP
  tools — the guide runs as a sub-agent under the Boss, and its memory
  (objections ranked, drop-off stage, suggestion acceptance, decision intents)
  is queryable for continuous improvement.
- **Tests**: `tests/test_briefing_guide.py` (13) — endpoints, objection bank,
  claims lint over both layers (no guarantee/cert/dollar-figure/pressure
  vocabulary; required stance "I'll suggest; you commit"), and the no-click
  rule. `test_runtime.py` tool contract extended (+2). Suite **279**, only the
  2 pre-existing homepage failures. NOT deployed — human `APPROVED` dispatch.

### Boss voice docent — guided salesman tour on /demo/signal (2026-07-31)

Owner instruction: add the Boss's voice to the demo so it can walk viewers
through every action and why, as a salesman who never pushes. Shipped as
`assets/js/boss-docent.js` (zero-dependency, self-injecting) wired into
canon-pinned `demo-signal.html` (canon re-pinned in the same commit).

Design decisions (binding for future desks):

- **Voice is OUTPUT-ONLY** — Web Speech synthesis; no microphone, no
  SpeechRecognition, no getUserMedia (test-enforced). Mirrors the ORACLE
  bright line: "I speak — I never listen."
- **Scripted, not LLM** — narration is pre-vetted copy plus dynamic slots read
  from the run's own DOM (gate rows, the verbatim guardrail veto, `causal_truth`,
  decision title). The Boss never invents a number, so it cannot violate claim
  discipline out loud. `tests/test_boss_docent.py` claims-lints every JS string
  literal (banned: mind-reading / will buy / guarantee / act-now vocabulary;
  required: output-only disclosure, "Illustrative scenario", replayability).
- **Not pushy, structurally** — exactly ONE pilot CTA
  (`/contact?source=demo-signal-docent`, test-enforced count == 1), "No
  pressure" framing, and the sales pitch is the deliberate red veto ("the part
  most demos hide").
- **Cooperative** — the docent presses Start itself and yields the moment the
  visitor touches Start/Reset/scenario ("Taking my hands off the controls");
  closing chips offer replay-remixed / executive briefing / pilot. DOM-driven
  sync (no changes to `demo-signal.js`); tour epochs prevent stopped tours
  leaking into restarts; minimum per-caption reading time keeps captions
  readable even when a browser exposes speechSynthesis with no working voice
  (headless behavior, verified).

Verified: 3 Playwright end-to-end runs (full tour incl. captions-only mode,
take-over courtesy, restart), suite 266 w/ only the 2 pre-existing homepage
failures. Rollout to the other desks is a per-desk beat map away — the engine
is generic. NOT deployed — ships via human `APPROVED` dispatch.

### Signal Intelligence / ORACLE incorporated (2026-07-30)

Owner-supplied "Signal Intelligence Division — Marketing Capabilities" documentation
(ORACLE / Latent Intent Inference) incorporated into the public site, per explicit
owner instruction ("incorporate this into the single intelligence marketing page and
demo"):

- **`signal.html` rewritten** as the full Signal Intelligence Division page in the
  locked v1.5 night-dossier vocabulary: crystal-ball-plus-proof positioning, the four
  intent stages (awareness → consideration → in-market → purchase-imminent), ORACLE
  capability cards (Cells 33/28/34 — consent-gated micro-signals, sub-100ms Intent
  Scoring API, Neo4j intent graph with SHOWED_INTEREST/PRECEDES edges), the proof
  half (X-Learner/DR-Learner, DoWhy refutation, holdout/ghost-bid/geo experiments,
  the caused-vs-anticipated credit ledger, iROAS vs platform ROAS), consumes/produces
  anatomy, claim-labeled targets, five playbooks, governance plate, and a cell map.
  `signal.html` is NOT canon-pinned; the `/signal` test contract
  (`test_division_pages_wired_to_demos`: `/demo/signal` + `/demo` links, root-absolute
  assets) is preserved.
- **`demo-signal.html` gained section "5 · ORACLE — anticipatory intent"** (static:
  stage strip, SERVE/PROVE/GOVERN facts, promotion gates, `/signal` link). This file
  IS canon-pinned — the owner instruction is the specific human approval, and
  `canon.lock.json` was re-pinned in the same commit. Demo runtime/JS untouched
  (interactive run re-verified).
- **Claim discipline is binding on both pages**: "anticipatory intent with proof of
  causal lift", never "mind-reading"; calibrated probabilities, never "will buy";
  "proven-incremental" only after refutation passes; 40% CAC / 35% ROAS / 67% ROI are
  labeled design targets, never guaranteed; no audio ever; consent-first; observe-only
  default with promotion gates Brier ≤ 0.20 · AUC ≥ 0.72 · stable lift ≥ 2 cycles.
- **Source doc archived** at `docs/SIGNAL_INTELLIGENCE_ORACLE_CAPABILITIES.md`.
- Suite: 260 tests, only the 2 pre-existing dossier-swap homepage assertions fail
  (they request `/`, untouched). **Not deployed** — ships only when a human runs
  Actions → "Deploy MIZ OKI 3.5 Homepage" and types `APPROVED`.

### Site-wide favicon (2026-07-27)

`/favicon.ico` 404'd site-wide. Fixed, and the icon set is now consistent across
**every** served surface.

- **Canonical assets live in `assets/img/`**: `favicon.svg` (brand mark — the nav
  logo "M", `#04060f` plate, ink→`#4cc9ff` gradient), `favicon.ico` (real 3-frame
  16/32/48 ICO), `apple-touch-icon.png` (180px).
- **Path moved** `assets/svg/favicon.svg` → `assets/img/favicon.svg`. 14 pages had
  pointed at the old path (an off-brand cyan zigzag); 18 pages + all 6 Flask
  templates had no favicon at all. All 38 surfaces now carry the same three links.
  The old file is left in place but is **unreferenced by the live site** — only
  `archive/` still mentions it.
- **`app.py`** serves `/favicon.ico`, `/apple-touch-icon.png` and
  `/apple-touch-icon-precomposed.png` at the root, since clients request those
  regardless of `<link>` tags.
- **Regenerate with `scripts/generate_favicon.py`** (pure stdlib — no Pillow). The
  "M" is drawn as geometry, not text: favicons never load a webfont, so a
  text-based mark would render inconsistently.

⚠️ **Two traps, both now test-enforced** (`tests/test_demo_platform.py`, 251 tests):
`test_demo_platform` already asserted the favicon path, so moving it broke two
tests — the path is a contract, update the assertions deliberately. And a `--`
inside an XML comment (e.g. writing `--nexus` in a note) makes the whole SVG
unparseable and the browser renders **nothing**; `test_favicon_assets_exist_on_disk`
now parses the SVG to catch it.

### Homepage presentation pass — demo elevated, omnichannel + pricing added (2026-07-27)

**Round 3** of the landing-remix review (`docs/LANDING_REMIX_ADOPTION_NOTES.md`). Rounds
1–2 built the live teaser but left it at section 12 of 14; this closes the *presentation*
findings the earlier rounds never addressed.

- **`#live` is now section 2** — the `#liveTeaser` block moved out of `#action-flow` to
  sit directly after the hero. Every `lt*` element ID was preserved, so
  `assets/js/home-demo.js` binds unchanged and still drives the real `/api/demo/*`
  runtime. **Invariant: keep it there.** It is the page's primary proof.
- **Animated SRPVDAL rail** on the static `#orchestration` loop (`.srp-rail` +
  `.srp-stage.lit/.done`), reusing the `.lt-stage` visual language and
  `--nexus`/`--estate` tokens. `IntersectionObserver`, fires once, snaps complete under
  `prefers-reduced-motion`.
- **New `#omnichannel`** (Meta / Google Ads / lifecycle email / programmatic) accented
  `var(--signal)` — capability description only, **zero performance numbers** (the
  source's "31% CPA drop" style metrics are fabricated and were rejected).
- **New `#pricing` preview** mapped to the autonomy ladder, consistent with
  `pricing.html`. No dollar figures.
- **Density:** nav 11 → 6 items, hero lede 6 lines → 4, "Run a Live Decision" promoted to
  primary CTA, long section sub-copy trimmed.

Tests: 248 passing. Deployed via the Deploy Router (bot merge → router → `deploy-homepage`
`workflow_dispatch`, no manual sweep). Production verified: same seed-42 trace id as local.

Plan + reusable prompt: `docs/HOMEPAGE_MERGE_PLAN_2026-07.md`.

### Homepage live teaser + Causal Truth + pricing rebuild (2026-07-23)

Three adoptions distilled from an external landing-page review — the UX ideas were kept,
the mocked implementation was not:

1. **Homepage live teaser (`index.html` + `assets/js/home-demo.js`)** — an interactive
   widget inside `#action-flow`: three scenario cards (Capital covenant veto — default,
   Capital growth reallocation, Signal ROAS), a 7-stage SRPVDAL strip, a timestamped
   execution log, and an outcome panel (real confidence, causal truth, trace id).
   It POSTs to the real `/api/demo/{capital,signal}/run` with **seed 42** and replays the
   returned trace — no mocked numbers, no `Math.random` (a test enforces this). Honors
   `prefers-reduced-motion`; degrades to a `/demo` link if the backend is unreachable.
2. **`causal_truth` on decision cards** — `demo_signal.build_causal_truth()` (reused by
   `demo_capital` with `constraint_noun="the covenant"`) composes a plain-English "why"
   from run data only: winner's gate numbers + ranking arithmetic, then the vetoed move
   quoting the failing guardrail check's own detail ("The veto is not an opinion — it is
   arithmetic against …"). Rendered by both `demo-pipeline.js` and `demo-signal.js` into a
   `#dcTruthWrap` slot on `/demo/capital` and `/demo/signal` (graceful when absent).
3. **`pricing.html` rebuilt** in the modern MIZOKI3 design system (was a stale legacy
   "MIZ OKI" page that `app.py` 301-redirected to `/`). Now served at `/pricing` +
   `/pricing.html`, listed in the sitemap, and linked from the homepage nav. Tiers map to
   the autonomy ladder — Starter "Core Intelligence" (L0–L1 approval-first), Scale
   "Operational Autonomy" (L2–L3 bounded thresholds, featured), Enterprise "Full
   Governance Suite" (L0–L5 per-scope grants). CTAs are live (`hello@mizoki3.com`,
   `/demo`); no performance claims anywhere on the page (claims-governance safe).

**Round 2 (same day):** a detailed re-comparison against the source remix surfaced four
remaining gaps, all closed:

- **`dividend_covenant_veto`** — a new capital scenario where the ONE planned move
  (`special_distribution +16% → holdco_dividend`) models covenant headroom 7% vs the
  15% floor and is blocked, so **nothing executes** (`funnel.executed == 0`,
  `executed_action is None`). The pure-veto flagship, echoing ACT-991. Default card in
  the homepage teaser; selectable on `/demo/capital`.
- **VETOED as a hero outcome state** — pure-veto runs render a red
  "VETOED — nothing executed · human override required" status and hide the confidence
  block; both demo players title a null action "No action executed — the veto held".
  `build_causal_truth` prepends "No move earned execution this run — the desk held."
- **Pipeline progress line + ✓ stage marks** in the teaser.
- **Hero ghost CTA** now "Run a Live Decision" → `#action-flow`.

Full adopted/adapted/rejected ledger: `docs/LANDING_REMIX_ADOPTION_NOTES.md`.

Tests: 248 passing (`python -m unittest discover tests`), including
`HomepageLiveTeaserTestCase`, `CausalTruthMarkupTestCase`, `PricingPageTestCase`,
engine-level `causal_truth` assertions, and the pure-veto scenario test.

### Homepage demo hygiene + Capital Desk JS (2026-07-22)

Merged via monorepo PR `#580` (`claude/demo-fixes-v2`): gunicorn timeout 120s; walkthrough + division landings root-absolute; stale external Sign-In fixed; `assets/js/demo-capital.js` added and wired from `demo-capital.html`. Preceded by flagship demo v4 (PR `#578`) and Signal/Counsel demos.

## Previous Work (June 2026)

### Google Ads API Version + GAQL Compatibility Pre-Flight (2026-06-30)

Closed a latent operational risk around the Google Ads API: it churns ~3 versions/year and
**sunsets** old ones on a published schedule (e.g. v19 sunset early 2026), so requests against a
removed version hard-fail, and a GAQL query selecting/filtering/sorting a field that is invalid for
the targeted **version + resource** combination hard-fails too. Added a deterministic,
dependency-free pre-flight that embodies the official guidance (check field availability with
`GoogleAdsFieldService` + the Query Validator before constructing complex queries) — no Google Ads
client, no network, fully unit-testable.

**New file `mizoki_runtime/google_ads_gaql.py`:**
- **Version deprecation schedule** (`GOOGLE_ADS_API_VERSIONS`, v16–v21 with release/sunset dates).
  `version_status(version, as_of)` *computes* `supported` / `deprecated` / `sunset` / `unreleased`
  / `unknown` relative to a date (never hard-coded) — `deprecated` once within
  `DEPRECATION_WARNING_WINDOW_DAYS` (120) of sunset; `usable` flips false on sunset. Bump the table
  as Google publishes versions.
- **GoogleAdsFieldService-style field registry** keyed by resource (campaign, ad_group,
  ad_group_ad, ad_group_criterion, search_term_view, keyword_view, customer) carrying
  `selectable`/`filterable`/`sortable` flags + version windows (`available_since`/`deprecated_in`/
  `removed_in`). Shared SEGMENT + METRIC field sets (metrics are not filterable in WHERE; the legacy
  `metrics.average_position` is modeled removed → a hard error on modern versions).
- **Dependency-free GAQL parser** (`parse_gaql`) extracting SELECT / FROM / WHERE / ORDER BY / LIMIT
  field references.
- **`GaqlValidator`** — pre-flights a query: version gate (sunset/unreleased → error, deprecated →
  warning), unknown-resource, per-field unknown/unavailable/not-selectable/not-filterable/
  not-sortable errors, deprecated-field warnings. Returns a structured
  `{valid, errors[], warnings[], fields[], version_status, cache_key}` report.
- **`GaqlValidationCache`** — keys on (normalized query, version, **day**) so a template reused
  across thousands of MCC accounts validates once, and a verdict that flips when a version sunsets is
  not served stale across day boundaries.
- **`GoogleAdsCompatibilityCell`** (`cell.31`) — `validate_query` / `validate_batch` (the MCC sweep)
  / `version_status` / `field_metadata` / `recent_validations`, persisting traces to
  `data/google_ads_validations.jsonl`.

**Wiring (`runtime.py`, `app.py`):** MCP tools `google_ads.validate_gaql`,
`google_ads.validate_gaql_batch`, `google_ads.version_status`, `google_ads.field_metadata` (new
`google_ads` category). `BossRuntime` methods + Flask `POST /api/boss/google-ads/validate`,
`POST /api/boss/google-ads/validate-batch`, `GET /api/boss/google-ads/versions`,
`GET /api/boss/google-ads/fields`, `GET /api/boss/google-ads/validations`. `discover()` gains a
`google_ads` block (default/latest/supported versions, resources, tools, cache stats);
`health_snapshot()` adds `gaql_validation_count`. Purely additive — no site copy, no existing
endpoint touched.

**Verification:** `python3 -m py_compile mizoki_runtime/google_ads_gaql.py mizoki_runtime/runtime.py
app.py` clean; `python3 -m unittest discover -s tests` → **77 passing** (+41: a new
`tests/test_google_ads_gaql.py` covering version lifecycle, parser, validator error/warning codes,
the (query, version, day) cache, field metadata, and the cell; plus runtime + app integration
tests). Smoked via `app.test_client()` with a fixed `as_of=2026-06-30`: v19 fails
(`api_version_sunset`), v21 passes clean, batch validation hits the cache, `/api/boss/discover`
carries the `google_ads` block. (Note: the JSONL trace store is per-instance ephemeral on Cloud Run;
the cache is in-process per revision — both fine for stateless pre-flight. Version dates are
representative-but-approximate; true them up against Google's published schedule as needed.)

## Previous Work (March 2026)

### Boss Agent & MCP Integration
- Added a concrete Boss Agent runtime with MCP-style tool registration, skill memory, and decision traces in `mizoki_runtime/runtime.py`.
- Exposed discovery and execution endpoints through Flask (`/api/mcp/*`, `/api/boss/*`).
- Added a graph-native decision intelligence layer in `mizoki_runtime/runtime.py` that runs SRPVDAL with GraphRAG retrieval, KG grounding, counterfactual simulation, and subagent recommendations.
- Added direct graph-native APIs at `/api/boss/graph/subagents`, `/api/boss/graph/context`, `/api/boss/graph/simulate`, and `/api/boss/graph/loop`.
- Added loop-to-skill promotion through `skills.learn_from_loop` and `/api/boss/skills/learn-from-loop`.
- Synchronized deployment and control planes across Cells 1-34.
- Handled merging of sub-PRs for pipeline correction and UI optimization.
- Addressed Google Cloud networking by repointing the Global External HTTPS Load Balancer (`mizoki-lb`) to a new Serverless Network Endpoint Group (NEG) hooked to the canonical `mizoki-website` Cloud Run deployment, securing a single source of truth.

### Integration Note
- Prior planning referenced `boss_agent_core.py` and external MCP registration blocks from a different repository shape.
- In this repo, the actual Boss/KG/GraphRAG integration point is the Flask runtime in `mizoki_runtime/runtime.py` plus the API layer in `app.py`.
- Any future graph-native or Boss-agent work should land there unless this repository gains the separate agent-service layout.

### Review-Driven Corrections
- Fixed routing bugs caused by substring matching so `decision control plane` no longer incorrectly maps to the `plan` stage.
- Constrained skill and alias learning inference so the Boss Agent does not accidentally route normal explanation requests into `skills.learn` or `tools.register_alias`.
- Added bounded integer validation for `top_k` and trace limits.
- Hardened trace and alias loading so malformed JSONL or alias records do not break startup or trace inspection.
- Added discovery metadata describing learning tools, tool-learning tools, and routing behaviors so the Boss Agent is more explicit about its capabilities.
- Added loop-aware learning behavior:
  - `skills.learn_from_loop` promotes graph-native loop traces into reusable skills.
  - If a user asks to learn from a loop before any loop exists, the Boss Agent should prefer generating a loop first.

### Why These Changes Were Made
- The initial task history mixed this website repository with a different multi-agent Python service layout.
- The real goal here was not to document graph-native decision intelligence conceptually, but to make the local Boss runtime actually usable, discoverable, and safe.
- The review phase therefore focused on closing the gap between “tools exist” and “the Boss Agent uses them correctly with the right parameters and the right sequencing.”

### Current Verification Standard
- `python3 -m py_compile mizoki_runtime/runtime.py app.py`
- `python3 -m unittest tests.test_runtime tests.test_app`
- Current regression coverage for this implementation path: 25 passing tests

### Canonical Blog Routing via Flask
Migrated legacy subdomain-dependent blogs to canonical main-domain paths internally using Python/Flask (`app.py`):
- Stripped all meta-refresh `blogs.html` redirections to external domains, pointing them 301 to `/blog/`.
- Configured dynamic, extensionless URL resolving for `relu-lens-meta-algorithm`.
- Added legacy redirect fallbacks for slugs like `meta-relu-gate-go-deep-before-wide`.
- Consolidated article static paths and structure exclusively under `/blog`.

## Previous Work (January 2026)

### ReLU Lens LinkedIn Content Kit

Created complete visual assets for the "Unlocking Meta's Ad Algorithm With the ReLU Lens" thought leadership content:

**Article Images** (`assets/img/relu-article/`):
| File | Purpose |
|------|---------|
| `01_relu_gate.svg` | ReLU gate concept - weak signals filtered, strong amplified |
| `02_nonlinear_activation_curve.svg` | Threshold effect visualization |
| `03_learning_50_events.svg` | 50 events/week learning phase target |
| `04_compounding_feedback_loop.svg` | Flywheel momentum diagram |
| `05_budget_dilution_vs_concentration.svg` | Budget strategy comparison |

**Carousel Slides** (`assets/img/relu-carousel/`):
| Slide | Content |
|-------|---------|
| `slide_01_cover.svg` | Title card |
| `slide_02_problem.svg` | The problem - flatline then breakout |
| `slide_03_relu_explained.svg` | What is ReLU? The gate concept |
| `slide_04_50_events.svg` | The magic number: 50 events/week |
| `slide_05_consolidate.svg` | Budget dilution vs concentration |
| `slide_06_flywheel.svg` | Compounding feedback loop |
| `slide_07_checklist.svg` | The 6-move ReLU Playbook |
| `slide_08_cta.svg` | Closing CTA |

**Supporting Files**:
- `assets/img/preview.html` - Visual preview page for all images
- `assets/img/README.md` - Comprehensive documentation for the image kit
- `blog/relu-lens-meta-algorithm.html` - Full blog article with embedded images

### Design System

Brand colors used throughout:
- Cyan: `#00d4ff`
- Blue: `#4f8fff`
- Purple: `#a855f7`
- Green: `#10b981`
- Orange: `#f59e0b`
- Red: `#ef4444`
- Background: `#0a0a0f` to `#12121a`

---

## Coding Guidelines

1. **HTML**: Self-contained pages with inline CSS (no build step required)
2. **Fonts**: JetBrains Mono (code), Instrument Serif (headings), DM Sans (body)
3. **Images**: SVG preferred for scalability; include alt text for accessibility
4. **Deployment**: HUMAN-APPROVED ONLY — Actions → "Deploy MIZ OKI 3.5 Homepage" with the `APPROVED` token (see Design Canon governance above). `./deploy.sh` / `./master-deploy.sh` are legacy and must not be run without the same approval
5. **Story copy**: `docs/marketing/signal-story-bank.md` governs all customer-story copy — obey its five rules (composite/illustrative labeling, ledger grammar, translate-don't-define, preview stays preview, never a guaranteed outcome)

---

## Contact

- Website: mizoki3.com
- Sales: sales@mizoki.com
