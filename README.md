# MIZOKI3 — Website

Marketing site for **MIZOKI3 — a Verifiable Autonomous Decision Intelligence Platform**.
Canonical hero line: **"A nervous system for your business."**

Live at **[mizoki3.com](https://mizoki3.com)** on Google Cloud Run — with the
**marketing parallel site** live beside it at
**[mizoki3.com/marketing](https://mizoki3.com/marketing)** (launched 2026-08-03,
see below).

## 🔒 SOURCE OF TRUTH & DEPLOY GOVERNANCE (LOCKED 2026-07-30)

**This repo is a source MIRROR.** The production source of truth lives in
`mediaintelligence/MIZOKICloudRun` under `# MIZ OKI 3.5/` — its `README.md` +
`CLAUDE.md` are the only authoritative docs, and the v1.5 "night dossier" look
and feel is LOCKED (`canon.lock.json`, 19 sha256-pinned surfaces;
`docs/DESIGN_CANON.md`). `/demo` + the Executive Briefing are the core of the
operation.

**Nothing ships to production without specific human approval:**

- Production deploys happen ONLY via MIZOKICloudRun's `deploy-homepage.yml` —
  manual-dispatch with a typed `APPROVED` token + a passing canon check.
- This repo's `deploy-cloudrun.yml` is manual-dispatch-only (push trigger
  removed 2026-07-30) and must not be run except as a deliberate, human-
  approved exception.
- `deploy.sh` / `master-deploy.sh` here carry the same approval gate.
- Agents: never deploy from this repo, and never edit canon-pinned files
  without an explicit human instruction. Parity commits use `[skip ci]`.


## /marketing — the parallel marketing site (LAUNCHED 2026-08-03)

Owner directive: *"launch this entire site under a /marketing so i can compare
them online before taking anything offline."* The proposed media-buyer /
enterprise-operational experience runs as a **complete parallel site** under
the `/marketing` prefix. The classic canon site at root is untouched; the two
run side by side in production until the owner retires one. Launched via
canonical deploy run **#47** (`deploy-homepage.yml`, typed `APPROVED`,
owner-instructed) on 2026-08-03; production verified: root clean of any
`/marketing` reference, all 12 marketing pages serving, seeded demo deep-links
embedding, `/media-buying` 301 → `/marketing`.

### Pages (12, all under `marketing/`)

| Page | What it is |
|------|------------|
| `/marketing` | Platform-first homepage: mandated hero ("Stop Managing Dashboards. Start Governing Ad Growth."), full-stack signal grid, vocabulary translation ledger, 7-stage accordion, divisions-as-initial-MVPs grid, live decision simulator, 90-sec storyboard |
| `/marketing/engine` | The 7-Stage Governed Decision System, stage by stage, in media-buyer terms |
| `/marketing/modules` | Channel Intelligence Modules: Google Ads · Meta & Paid Social · E-Commerce & Inventory · ESP & Retention |
| `/marketing/simulator` | Command Center: dual-panel simulator — 3 failure scenarios, live sliders, safety toggles, 7-phase execution terminal, Approve Strategy gate, veto path |
| `/marketing/walkthrough` | 90-second, 5-scene storyboard player with transcript drawer and timestamp seeking |
| `/marketing/governance` | Observe / Bounded / Full autonomy modes + Enterprise Privacy & Security Shield |
| `/marketing/{counsel,estate,capital,signal,risk}` | Redesigned division pages: plain-English hero, "What we say / What we never say" strip, Watches/Decides/Never-does grid, a worked decision from the real live desk |
| `/marketing/pricing` | Three tiers mapped to the three autonomy modes, jargon-free |
| `/marketing/demo` + `/marketing/demo/<desk>` | The six live demo desks, mirrored from canon files via `_marketize()` — the desks ARE the product, identical in both sites |

### Key elements

- **Vocabulary translation key (8 entries, test-enforced):** Canonical Event
  Envelope → *Structured Signal Evidence* · Temporal-Causal Knowledge Base →
  *Cross-Stack Root Cause Engine* · Domain Intelligence Cell → *Channel
  Intelligence Modules* · SRPVDAL Loop → *7-Stage Governed Decision System* ·
  Decision Control Plane / Eligibility Layer → *Safety Guardrail Engine* ·
  Immutable Learning Ledger → *Compounding ROI Memory* · Tenant Isolation &
  Boundary → *Enterprise Privacy & Security Shield* · No-Action Counterfactual
  Baseline → *"Do Nothing" Opportunity Cost Check*. Engineering terms appear
  exactly once each, in the on-page ledger; sub-pages carry zero raw jargon.
- **Deterministic simulator** (`assets/js/media-sim.js`): no `Math.random`, no
  `Date.now`; the replay id is a hash of the inputs; the red veto is
  slider-reachable (latency > ~5.2s under the 2.2× ROAS floor) and vetoes
  still record to memory. Policy values: 2.2× ROAS floor, $5,000 max
  auto-spend limit.
- **Software-fact discipline** (`/marketing/signal#acquisition` +
  `#parameters`): every acquisition number is generated FROM the runtime —
  ReLU gate floors 5% / 0.70 / n = 15 (`demo_signal.GATE_*`), swing caps
  ±20% / ±30% (`GuardrailSet`), seed 42, the +12% campaign_7 / $8,400 / 0.86 /
  n = 48 winner and the deliberate +25% block — and
  `AcquisitionShowcaseTestCase` re-imports the runtime so the page **fails the
  build if it drifts from the code**. Spec-only capabilities carry amber
  "Platform spec" chips (promotion gates: Brier ≤ 0.20 · AUC ≥ 0.72 · stable
  lift ≥ 2 cycles; observe-only default).
- **Divisions are initial MVPs, not limits:** "One decision loop. Any
  division." — five MVP divisions plus the dashed "+ Your division" card; new
  domains onboard as modules on the same governed loop.
- **Transparency devices everywhere:** the amber "Parallel preview — nothing
  on the classic site is replaced" strip on every marketing page (escape
  hatch → `/`), claim strips on every division page, targets labeled as
  targets, never outcome promises.

### Never-lose-the-site guarantee (drift guards, 2026-08-03)

Two pipelines can deploy the `mizoki-website` Cloud Run service. Both now
refuse any tree missing either the locked canon surfaces or the marketing
site:

- `scripts/check_marketing_surfaces.py` — stdlib-only gate: 12 pages present
  and non-stub, engine + stylesheet + tests present with content markers,
  `app.py` still carries the `/marketing` route layer.
- Wired into **both** workflows: MIZOKICloudRun `deploy-homepage.yml` (beside
  the canon check) and this repo's `deploy-cloudrun.yml` (which now also runs
  the canon check). `DriftGuardTestCase` runs the same gate inside the test
  suite.
- Both repos are **byte-identical** on every meaningful surface (verified by
  diff): `app.py`, `CLAUDE.md`, `signal.html`, `canon.lock.json`,
  `marketing/`, `tests/`, marketing assets, `mizoki_runtime/`, the guard.

### Change ledger

Website repo PRs **#20** (parallel site + transparent redesign), **#21**
(media-acquisition showcase), **#22** (drift guard on this pipeline), **#23**
(reverse-parity mirror) — MIZOKICloudRun PR **#588** (port + drift guard on
the canonical pipeline) — deploy run **#47** (launch). Full engineering log:
[`CLAUDE.md`](CLAUDE.md) → *Recent Work (August 2026)*.

## Positioning (read before touching copy)

The metaphor is a **nervous system — never a "brain."** MIZOKI3 gives a business a real-time,
mathematical understanding of every part of itself: a living graph of metrics, relationships, and
**prediction**. It replaces the CRM and the linear, backwards-looking analytics stack with a
forward-looking, predictive system.

The domain **lenses (Counsel · Estate · Capital · Signal · Risk · Manufacturing) are _example
deployments_** — the structures of customers onboarded so far — **not a fixed product.** The platform
is unlimited and adaptive; always frame the lenses as examples, never as a fixed list. See
[`CLAUDE.md`](CLAUDE.md) for the full messaging guide.

## Stack

- **Server:** Python **Flask** app served by **Gunicorn**, routed in [`app.py`](app.py).
- **Frontend:** self-contained HTML with **inline CSS + vanilla JS — no build step.**
- **Deploy:** Docker container on **Google Cloud Run** (`mizoki-website`, `us-central1`); custom
  domain `mizoki3.com`.
- **Fonts:** Instrument Serif (display) · DM Sans (body) · JetBrains Mono (labels).
- **Aesthetic:** light "ledger / filing" paper theme with a teal accent — an institutional
  decision-terminal look.

## Structure

```text
.
├── index.html            # Homepage: hero graph + schema inspector, executable SRPVDAL simulation,
│                         #   DEL gauge + authorization scorecard, control-plane sandbox, §04 domains
│                         #   panel, and the 12-connector unified ingress gateway
├── counsel/ estate/ capital/ signal/ risk/ manufacturing/   # Domain lens pages (each an index.html)
├── blog/                 # Journal listing + articles
├── privacy/  terms/  404.html
├── app.py                # Flask routing — lenses, /console, /infrastructure, blog, sitemap, APIs
├── mizoki3-site/         # CANONICAL — standalone /console + /infrastructure (Terraform). Do not rename.
├── schemas/              # Canonical JourneyEvent + CanonicalEventEnvelope JSON schemas
├── mizoki_runtime/       # Boss runtime, SRPVDAL loop, JourneyEvent / envelope / identity cells
├── tests/                # Flask (test_app) + runtime (test_runtime) unit tests
└── sitemap.xml  requirements.txt  Dockerfile  cloudbuild.yaml  deploy.sh
```

## Example domain lenses

Six shown on the site — **example deployments, not a fixed offering:**

| Lens | Focus |
|------|-------|
| Counsel | Legal & Counsel |
| Estate | Estate & Trust |
| Capital | Treasury & Capital |
| Signal | Growth & Signal |
| Risk | Risk & Compliance |
| Manufacturing | Operations & Manufacturing |

## Local development

The site is a Flask app (routes such as `/manufacturing` are resolved server-side), so run it through
Flask — not a plain static file server:

```bash
python3.13 -m pip install -r requirements.txt
python3.13 app.py            # serves http://localhost:8080  (honors $PORT)
```

Run the test suite before shipping:

```bash
python3 -m unittest discover tests   # 351 tests; only the 2 pre-existing homepage failures
```

> **Gotcha:** the machine's default `python3` is Homebrew 3.14 **without Flask**, so `tests.test_app`
> ImportErrors there (only `test_runtime` runs). Use **`python3.13`** (has Flask) for the app tests
> and the local server.

## Deployment

**No push-triggered deploys** (removed 2026-07-30). Two manual-dispatch
pipelines exist, and both are gated by the canon check **and** the marketing
drift guard, so neither can ship a tree missing the proper site:

1. **Canonical:** MIZOKICloudRun → Actions → *"Deploy MIZ OKI 3.5 Homepage"* →
   type `APPROVED` (builds from `# MIZ OKI 3.5/`).
2. **Exception path:** this repo → Actions → *"Build & Deploy to Cloud Run"*
   (Workload Identity Federation — no long-lived keys).

Verify any tree before deploying: `python3 scripts/check_design_canon.py &&
python3 scripts/check_marketing_surfaces.py`.

## Recent updates (2026-07-03)

- **Manufacturing** added as a first-class 6th example-domain lens — new `manufacturing/` page, wired
  into the homepage hero graph, schema inspector, executable simulation, §04 divisions panel, and the
  footer on every page; `/manufacturing` Flask route + sitemap entry.
- **Homepage connector gateway expanded 9 → 12** — added Shopify, Meta Ads, Klaviyo, DV360 (removed
  Stripe); §01 canonical-event copy now names Google Ads · Meta · Shopify.
- Added the **Creative Single Point of Truth v1.0** canonical reference doc.

See [`CLAUDE.md`](CLAUDE.md) → *Recent Work (July 2026)* for the full engineering log.
