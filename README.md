# MIZ OKI 3.5 — Marketing Site + Live Demos

Public marketing site for **MIZ OKI 3.5** (mizoki3.com), served by Flask + Gunicorn on Cloud Run as `mizoki-website`.

This folder is the Cloud Build context for `.github/workflows/deploy-homepage.yml` in the monorepo (`MIZOKICloudRun`). Quote the path in shells: `"# MIZ OKI 3.5"`.

## 🔒 SOURCE OF TRUTH & DEPLOY GOVERNANCE (LOCKED 2026-07-30)

**This document and `CLAUDE.md` are the ONLY sources of truth for this site.**
The v1.5 "night dossier" look and feel is LOCKED (`canon.lock.json`, 19 core
surfaces, sha256-pinned; see `docs/DESIGN_CANON.md`), and `/demo` + the
Executive Briefing are the core of the operation.

**Nothing ships to production without specific human approval:**

- The deploy workflow (`deploy-homepage.yml`) is manual-dispatch-ONLY and
  requires a human to type `APPROVED`; it refuses any tree that fails
  `python3 scripts/check_design_canon.py` — or, since 2026-08-03, any tree
  that fails `python3 scripts/check_marketing_surfaces.py` (the /marketing
  parallel site can never be dropped by a deploy).
- There is NO push-triggered deploy; the Deploy Router no longer matches
  this workflow. `deploy.sh` / `master-deploy.sh` carry the same approval
  gate (`MIZOKI_DEPLOY_APPROVED=APPROVED` or interactive confirmation).
- Canon-pinned files change only on an explicit human instruction, with the
  lockfile re-pinned (`check_design_canon.py --update`) in the same change.
- Agents: never dispatch the deploy workflow, run the deploy scripts, or
  edit canon files without that explicit human instruction.

## Stack

- **Runtime:** Python 3.13, Flask, Gunicorn (`2` workers × `8` threads, **120s** timeout)
- **Pages:** static HTML under `/` with root-absolute `/assets/...` URLs
- **APIs:** `/api/health`, `/api/mcp/*`, `/api/boss/*`, **public** `/api/demo/*`
- **Demos:** five divisions + Nexus (stdlib engines in `mizoki_runtime/`)

```
.
├── index.html                 # Homepage (division See-it-live CTAs → /demo/*)
├── demo.html                  # Demo hub
├── demo-signal.html           # Signal Factory
├── demo-counsel.html          # Counsel Room
├── demo-estate.html           # Estate Desk
├── demo-capital.html          # Capital Desk (SSE)
├── demo-risk.html             # Risk Desk
├── demo-nexus.html            # Nexus boardroom
├── counsel.html … risk.html   # Division landings
├── walkthrough.html           # Guided walkthrough
├── app.py                     # Flask factory + routes
├── mizoki_runtime/            # Boss runtime + demo_* engines
├── assets/js/demo-*.js        # Demo players (incl. demo-capital.js)
├── docs/DEMO_V4_BUILD_NOTES.md
├── Dockerfile
├── cloudbuild.yaml
└── tests/                     # unittest (app, runtime, demos)
```

## Local preview

```bash
python3 -m venv /tmp/mizoki35-venv && /tmp/mizoki35-venv/bin/pip install -r requirements.txt
/tmp/mizoki35-venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 8 --timeout 120 app:app
# open http://localhost:8080/demo
```

## Tests

```bash
python -m unittest discover tests
```

Includes `test_demo_platform` (absolute asset URLs, Capital JS contract), `test_demo_capital`, estate/risk/nexus suites.

## Live demos (July 2026)

| Route | Notes |
|:------|:------|
| `/demo` | Hub |
| `/demo/signal\|counsel\|estate\|capital\|risk` | Division desks |
| `/demo/nexus` | Cross-division Nexus run |
| `/api/demo/*/scenarios` + `/run` | Public JSON APIs |
| `/api/demo/capital/stream` | Capital SSE |
| `/login` | → `/admin/login` (local admin; do not use `mizoki.mizoki3.com`) |

**PR `#580` (July 22):** URL hygiene, Sign-In defaults, named `assets/js/demo-capital.js`. Flagship coverage: PR `#578`.

## Deployment

Monorepo workflow builds **this folder only** and deploys `mizoki-website` in `us-central1` / project `spry-bus-425315-p6`. Manual:

```bash
gcloud builds submit "# MIZ OKI 3.5" --config="# MIZ OKI 3.5/cloudbuild.yaml" \
  --project=spry-bus-425315-p6 --region=us-central1
```

Secrets: see `docs/PRODUCTION_SECRETS_SETUP.md`.

## Design language

- Dark, cinematic, technical (homepage) + light theme on secondary pages
- Per-division accents: Counsel cyan · Estate violet · Capital amber/emerald · Signal amber · Risk rose

## /marketing — the parallel marketing site (LAUNCHED 2026-08-03)

Owner directive: run the proposed media-buyer / enterprise-operational
experience as a COMPLETE parallel site under `/marketing`, side by side with
the classic canon site at root, until the owner retires one. Launched via
this repo's `deploy-homepage.yml` run **#47** (typed `APPROVED`,
owner-instructed); production verified — root untouched, all 12 marketing
pages live, `/media-buying` 301 → `/marketing`.

- **Pages** (`marketing/`, 12): platform-first homepage (mandated hero,
  full-stack signal grid, 8-entry vocabulary translation ledger, 7-stage
  accordion, divisions-as-initial-MVPs, live decision simulator, 90-sec
  storyboard); `/marketing/engine`, `/marketing/modules`,
  `/marketing/simulator`, `/marketing/walkthrough`, `/marketing/governance`;
  five redesigned division pages (What-we-say / What-we-never-say strips,
  Watches/Decides/Never-does grids, worked decisions from the live desks);
  jargon-free `/marketing/pricing`. The demo hub + six desks are mirrored
  from the canon files via `_marketize()` in `app.py` — never modified on
  disk, links rewritten to stay in the prefix, `noindex` on mirrors.
- **Vocabulary key (test-enforced, 8 entries)**: Canonical Event Envelope →
  Structured Signal Evidence · Temporal-Causal Knowledge Base → Cross-Stack
  Root Cause Engine · Domain Intelligence Cell → Channel Intelligence
  Modules · SRPVDAL Loop → 7-Stage Governed Decision System · Decision
  Control Plane/Eligibility Layer → Safety Guardrail Engine · Immutable
  Learning Ledger → Compounding ROI Memory · Tenant Isolation & Boundary →
  Enterprise Privacy & Security Shield · No-Action Counterfactual Baseline →
  "Do Nothing" Opportunity Cost Check.
- **Software-fact discipline** (`/marketing/signal#acquisition`): every
  acquisition number is generated FROM the runtime (ReLU floors 5% / 0.70 /
  n = 15; swing caps ±20% / ±30%; seed 42; the +12% campaign_7 / $8,400
  winner and the deliberate +25% block) and `AcquisitionShowcaseTestCase`
  re-imports the runtime so the page fails the build if it drifts from the
  code. Seeded demo deep-links (`?scenario=…&seed=42`) autorun the real
  engine.
- **Drift guards (owner: "never have issues with losing proper site
  online")**: `scripts/check_marketing_surfaces.py` gates BOTH deploy
  pipelines (this workflow and the website repo's `deploy-cloudrun.yml`);
  `DriftGuardTestCase` runs the same gate in the test suite; both repos are
  byte-identical on every meaningful surface (diff-verified).
- **Tests**: `tests/test_marketing_site.py` (64) — suite 386, only the 2
  pre-existing homepage failures.

## /media — media division film page (LIVE 2026-08-04)

Owner-approved go-live (canonical `deploy-homepage.yml` run **#52**, typed
`APPROVED`, sha `1577206`). `/media` serves `media/index.html` ("MIZ OKI
Media — Causal Growth Control") and a traversal-guarded asset route
(`/media/<path>`: suffix allowlist + resolved-path prefix check) streams
`media/video/mizoki-signal-explainer.mp4` as seekable `video/mp4`.

The drift guard (`scripts/check_marketing_surfaces.py`) now asserts the
/media page marker, the film file, and the `app.py` route marker in BOTH
deploy pipelines — added after a cross-repo parity byte-copy briefly dropped
the /media + blog routes from canonical main (caught in pre-deploy
verification, never deployed, restored as the verified union; full account
in `CLAUDE.md`).
