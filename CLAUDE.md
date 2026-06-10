# CLAUDE.md - AI Assistant Context

## Project Overview

**MIZ OKI 3.5** is a Verifiable Autonomous Decision Intelligence Platform. This repository contains the marketing website deployed on Google Cloud Run.

## Architecture

- **Deployment**: Docker container on Google Cloud Run
- **Web Server**: Python Flask application served via Gunicorn
- **Domain**: mizoki3.com (Cloud Run custom domain)
- **Routing**: Client and API routes managed natively in Flask (`app.py`)

## Core Technology (7-Stage SRDPV-DAL Pipeline)

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
├── index.html                    # Homepage — MIZOKI3.com five-division design
│                                 # (Flywheel, bento cards, Live Nexus Snapshot,
│                                 # Counterfactual Sim Engine, DEL gauge, CTA)
├── how-it-works.html             # Legacy — 301s to / via app.py
├── platform.html                 # Legacy — 301s to / via app.py
├── security.html                 # Legacy — 301s to / via app.py
├── industries.html               # Legacy — 301s to / via app.py
├── pricing.html                  # Legacy — 301s to / via app.py
├── case-studies.html             # Legacy — 301s to / via app.py
├── resources.html                # Legacy — 301s to / via app.py
├── roi.html                      # Legacy — 301s to / via app.py
├── walkthrough.html              # Legacy — 301s to / via app.py
├── investor.html                 # Legacy — 301s to / via app.py
├── sales-one-pager.html          # Legacy — 301s to / via app.py
│
├── counsel.html                  # Domain lens — Counsel (legal)
├── estate.html                   # Domain lens — Estate
├── capital.html                  # Domain lens — Capital
├── signal.html                   # Domain lens — Signal (renamed from Media Acquisition)
├── risk.html                     # Domain lens — Risk
│
├── mizoki3-site/                 # CANONICAL — Flask /console + /infrastructure
│   │                             # routes hard-code this path. Do not rename.
│   ├── README.md                 # Package documentation (4 deploy options)
│   ├── console/index.html        # Standalone Decision Control Plane
│   │                             # (Risk Arbitration Console UI)
│   └── infrastructure/main.tf    # Google Cloud Terraform — VPC, Spanner +
│                                 # Neo4j TCKG, Pub/Sub, Cloud Run orchestrator,
│                                 # Vertex AI (Claude) reasoning isolation, KMS
│
├── MIZOKI3-Site (1)/             # Sibling React/Vite/Tailwind build of the
│   │                             # same site. Standalone — own Dockerfile,
│   │                             # nginx.conf, cloudbuild.yaml, infrastructure/
│   ├── src/components/           # 15 React components
│   ├── public/console/index.html
│   └── infrastructure/main.tf
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
├── requirements.txt              # Python dependencies (Flask 3.1.3 + gunicorn)
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

---

## Recent Work (June 2026)

### Cell 27 — Programmatic Intelligence: OpenRTB Bidstream → SRPVDAL Alignment (2026-06-09)

Added a **graph-native programmatic intelligence cell (Cell 27)** so OpenRTB bidstream signals enter the platform at the SENSE stage and flow through the *entire* SRPVDAL spiral instead of being routed straight into decisioning. The **VALIDATE stage is the hard safety gate** — no optimization reaches ACT without clearing it.

**Where it lives:** `mizoki_runtime/runtime.py`, class `ProgrammaticIntelligenceCell` (deterministic, no external services — the bidstream "sinks", DSP/budget APIs, and backtests are modeled in-process so the pipeline is reproducible and unit-testable).

**Per-stage behavior:**
- **SENSE** — `ingest_bidstream()` normalizes loosely OpenRTB-shaped records (requests, win/loss notices, buyer IDs, exchange/seat metadata, floors, currency, consent) into canonical auction/impression events with full provenance, then fans them out to the `bigquery`, `knowledge_graph`, `event_store`, and `audit_log` sinks. Consent is evaluated (GDPR/TCF + US-privacy opt-out).
- **REASON** — per-exchange/seat aggregation (win rate, ROAS, CPM, floor pressure), identity resolution, anomaly detection (`consent_gap`, `spend_no_return`, `low_roas`, `low_win_rate`, `floor_pressure`), opportunities, insights, predictions.
- **PLAN** — candidate action objects (`increase_bid`, `decrease_bid`, `adjust_bid_to_floor`, `suppress_seat/exchange`, `reallocate_budget`, `expand_inventory`, `modify_audience`) each carrying `expected_roas_lift` + `confidence`, plus a `hold` baseline.
- **VALIDATE** — policy checks (budget, brand-safety, consent/legal), KG historical-conflict check, and a simulation/backtest check; every plan labeled `pass` / `escalate` / `fail`. Scaling spend on non-consented supply is a hard `fail`.
- **DECIDE** — ranks validated plans by `expected_roas_lift × confidence` net of risk/cost, selects the top N, emits a reasoning chain + `requires_approval` flag. Defaults to **needs_approval** unless `auto_execute=True` and nothing escalated.
- **ACT** — executes approved low-risk actions against the mapped API surface with a rollback token + provenance record; otherwise holds them `pending_approval`. Audit log always written.
- **LEARN** — measures realized vs. expected lift, emits a reward signal, proposes policy/threshold updates, and feeds KG/agent-memory updates (incl. a recommended skill seed).

**Surfaces:**
- MCP tools: `programmatic.ingest_bidstream`, `programmatic.run_pipeline`, `programmatic.recent_runs` (registered in the `programmatic` category; discoverable via `/api/mcp/tools` and `/api/boss/discover`).
- Flask endpoints: `POST /api/boss/programmatic/ingest`, `POST /api/boss/programmatic/run`, `GET /api/boss/programmatic/runs`.
- KG grounding: new entities `programmatic_intelligence` (Cell 27) and `openrtb_bidstream`, wired into `sense`/`srpvdal`/`decision_control_plane`/`validation_arbitration`.
- Discovery + health: `/api/boss/discover` gains a `programmatic` block (cell id, sinks, tools, recent runs); `health_snapshot()` adds `programmatic_run_count`.
- Policy thresholds are overridable per run via the `constraints` channel (e.g. `"min_roas=2"`, `"target_roas=4"`). Optional `budget` cap drives the VALIDATE budget check. `auto_execute` (default off) and `max_actions` (default 3) bound the ACT stage.

**Repository hygiene:** added `data/*.jsonl` and `data/*.json` to `.gitignore` so the Boss runtime's generated artifacts (decision logs, graph-native loop traces, the new `programmatic_runs.jsonl`, learned skills, tool aliases) no longer pollute `git status` — only `data/.gitkeep` stays tracked. Mirrors the May-2026 bytecode-hygiene precedent.

**Verification:** `python3 -m py_compile mizoki_runtime/runtime.py app.py` and `python3 -m unittest tests.test_runtime tests.test_app` — now **32 passing tests** (added 7: full-pipeline + persistence, safety-gate blocks unsafe scaling, auto-execute approves a scale opportunity, ingest-only SENSE, empty/invalid-event rejection, plus the two API tests). Also smoke-tested the live API path end-to-end via `app.test_client()`: a waste signal produced `spend_no_return` anomalies → suppress plans → validated `pass` → DECIDE `approved` → ACT `executed` with rollback tokens + provenance → LEARN reward signal. Shipped on branch `claude/openrtb-srpvdal-alignment-607lkw` (commit `65c9b62`). Run traces persist to `data/programmatic_runs.jsonl`.

### Homepage Merge — Provenance Note (2026-06-09)

Bookkeeping addendum to the 2026-05-22 "Decision OS Homepage + React Sibling Project" entry below. Records how the rebuilt `index.html` (the commit referenced there as `6c95d5a`) was actually assembled — source material, merge rules, verification — none of which was captured the first time. No functional change to the live site.

**Source material — three competing drafts that fed the merge**:

1. **React/Lucide draft** (≈225 lines, single React component). Cinematic dark background, knowledge-graph blob backdrop, four-quadrant industry section. Built around five SRPVDAL stages, not seven. No interactivity beyond an auto-cycling loop.
2. **Plain-HTML draft** (≈100 lines, single self-contained file). Tight and declarative. Twelve sections: hero with TCKG visualizer + concentric nodes, status-quo vs paradigm, full 7-stage SRPVDAL loop, Decision Control Plane scorecard, replay timeline, media wedge, divisions grid, demo CTA. Zero JS handlers.
3. **Interactive-HTML draft** (≈900 lines, Tailwind CDN + lucide + JetBrains Mono / Inter). Richest of the three: animated TCO-KG hero, clickable 7-stage SRPVDAL inspector with per-stage JSON payload, tabbed domain cells (four — Counsel/Estate/Risk/Media), execution sandbox terminal with three live-trace scenarios.

**Merge rules applied**:

- Took the visual identity, dependency stack (Tailwind CDN + lucide + Inter + JetBrains Mono), and interactivity scaffold from draft 3.
- Took the section roster, hero structural framing, and replay-timeline content from draft 2.
- Took the multi-tier blur backdrop and divisions framing from draft 1.
- **Renamed draft-3 domain cells from four to five** to match this repo's canonical five-division naming (Counsel / Estate / Capital / Signal / Risk). Draft 3 had "Media Acquisition" — collapsed into Signal per the May 18 consolidation. Added a Capital cell that none of the three drafts had.
- Wired all domain links to existing Flask routes (`/counsel`, `/estate`, `/capital`, `/signal`, `/risk`), the live-console pill to `/console`, and the demo CTA to `mailto:hello@mizoki3.com`.
- Stripped any `pilot@mizoki3.com` / `sales@mizoki.com` slip-throughs in favor of the canonical `hello@mizoki3.com`.

**Verification done before the original push**:

- Python `HTMLParser` structural check on the assembled file — stack balanced, no unclosed tags. (`<br />` / `<meta />` raise XHTML-style warnings only; not actual structural errors.)
- Every JS handler (`selectEngineStage`, `selectDomainCell`, `activateSandboxScenario`, `triggerSandboxSimulation`, `resetSandboxTerminal`, `triggerDemoToast`) was traced against the DOM IDs it touches — all targets present.
- Every lucide icon name used (28 distinct: `globe-lock`, `network`, `scale`, `landmark`, `trending-up`, `radio-tower`, `shield-alert`, `shield-check`, `eye`, `brain-circuit`, `git-merge`, `layers`, `zap`, `activity`, `history`, `database`, `clock`, `gauge`, `bar-chart-3`, `rotate-cw`, `file-check`, `terminal`, `rewind`, `play`, `arrow-right`, `info`, `chevron-right`, `x`, `check`) was checked against the lucide.dev catalog.
- No Flask route, runtime, or test file touched. `tests/test_app.py` and `tests/test_runtime.py` unaffected; the 25-test baseline holds.

**Lifecycle on `claude/add-monitoring-dashboard-ENme0`**:

- Branch first created off `main` at `4efddc2`.
- Commit `6c95d5a` pushed to that branch with the merged `index.html` (88KB / ~1340 lines).
- Branch merged into `main` (post-merge head `487ee4e`) and deleted in a parallel session that wrote the 2026-05-22 entry below.
- Branch re-created off the new `main` for this bookkeeping CLAUDE.md update.

**Branch-name caveat**: the branch is named `claude/add-monitoring-dashboard-ENme0`, prescribed by the session harness. The content has no monitoring-dashboard relevance — it's a homepage rebuild. Rename the branch before any future audit if the mismatch is confusing.

## Recent Work (May 2026)

### Slotted React Apps + Sweep of Redundant Files / Services (2026-05-24)

**Four React/Vite siblings mounted under `mizoki3.com/<N>/`** via three commits (`04c0cae`, `a1f9b7d`, `ec57378`) that landed during this session:

- `/1/` — Vite-built React app (ChatGPT, single-page rebuild of the marketing site)
- `/2/` — Vite single-page MIZOKI3 site (Claude, single-page + standalone `console/`)
- `/3/` — Vite multi-page React+Router app (ChatGPT, the differentiated one: Simulator, Engine, Control Plane, Divisions, Governance, KPIs, Blog, Contact pages with `framer-motion` and `KnowledgeGraphBackground`)
- `/4/` — Vite single-page React + `console/` (Claude, branded /4/)

**Shipped architecture** (chose this over per-slot Cloud Run services):
- Each slot is a flat pre-built `<N>/` directory at the repo root, containing `index.html`, `assets/`, and (for /2, /4) `console/`.
- `app.py` has three routes per slot: `/<N>`, `/<N>/`, `/<N>/<path:filename>`. Catch-all serves `BASE_DIR / "<N>" / filename` if the file exists, else falls back to `BASE_DIR / "<N>" / "index.html"` so React Router can resolve the client-side route.
- Single Cloud Run service (`mizoki-website`) carries every slot via the existing WIF auto-deploy. No LB url-map changes, no per-slot service to monitor, no Node in the runtime Dockerfile.
- The dist/ outputs are **committed directly** — externally built (`npm install && npm run build` with `vite.config.js base: '/<N>/'` and React Router `basename="/<N>"`), then the resulting `dist/` contents land in the flat `<N>/` directory.

**Architecture pivot mid-session:** an earlier attempt this session built per-slot standalone Cloud Run services (`mizoki3-v3`, `mizoki3-v4`) wired by `mizoki-lb` URL maps with prefix-strip rewrites. Tossed for being over-engineered relative to the chosen pattern. The `mizoki3-v3` standalone was retained briefly as backup; `mizoki3-v4` was torn down. By end of day both are deleted — see "Cloud Run cleanup" below.

**Sweep of redundant local files / Cloud Run services:**
- **Deleted folders:** `MIZOKI3-Site (1)/` (orphan Claude React sibling, identical product to the live site), `mizoki-website-all-files/` (13MB stale snapshot of the repo inside the repo — its inner CLAUDE.md only went up to "March 2026"), `legacy_mizoki_site/` (10MB pre-MIZOKI3 backup), `files (19)/` (earlier upload scratch), `Mizoki3_Site_Blog_Meta_ReLU_Deploy_Kit/` (one-time deploy kit).
- **Deleted source zips:** `mizoki3-final-production-pages_chatgpt.zip` (already extracted as `/3/`), `mizoki3-site-deploy_1.zip`, `Mizoki3_Site_Blog_Meta_ReLU_Deploy_Kit.zip`, `files.zip` (timestamp-only churn, content byte-identical to long-since-deployed state).
- **Deleted duplicate HTMLs:** `mizoki3_complete_enterprise_terminal{,(1),(1_gemini)}.html` — three byte-identical copies of the same single-file terminal page, not referenced by the live site.
- **Deleted scratch screenshots:** 17 ChatGPT-generated reference PNGs at the repo root from May 13 / 18 / 19 / 22 (none referenced by served HTML).
- **Deleted misc scratch:** `Claude Final Sitebudget balance sheet` (Pages doc), `MIZOKI Cannonical Lopp.png` (typo'd reference image), `preview.html` (single-file design preview), `01_relu_gate.png` at the repo root (duplicate of `assets/img/relu-article/01_relu_gate.svg`), `README_Captions_AltText.txt`, `LinkedIn_Meta_ReLU_Article.{pages,txt}` (drafts of the now-shipped blog post), `mizoki3-site.textClipping`.
- **Cloud Run cleanup:** deleted `mizoki3-v3` and `mizoki3-v4` standalone services. The flat-dir Flask pattern is the only production serving path now.

**Live route verification (post-cleanup):** `/`, `/1`, `/2`, `/3`, `/4`, `/console`, `/infrastructure/main.tf`, `/blog` — all 200 from `mizoki3.com`.

### Decision OS Homepage + React Sibling Project + Operational Cleanup (2026-05-22)

**Homepage replaced with the "Decision OS" rebuild.** Merged `claude/add-monitoring-dashboard-ENme0` (1 commit, `6c95d5a`) into main. New `index.html`:

- Tailwind via CDN + lucide icons + Inter / JetBrains Mono (no build step — still drop-in to the Flask static server).
- Title: *"MIZOKI3 // The Decision OS for Autonomous Enterprise Cognition"*.
- Hero with animated TCO-KG "Living Brain" visualizer and live telemetry pill.
- Status Quo vs. MIZOKI3 paradigm comparison.
- Interactive **7-stage SRPVDAL inspector** (Sense → Reason → Plan → Validate → Decide → Act → Learn) with per-stage payload and metrics.
- Decision Control Plane authorization scorecard.
- Tabbed Domain Cells (Counsel / Estate / Capital / Signal / Risk) with deep links to `/counsel`, `/estate`, `/capital`, `/signal`, `/risk`.
- Architecture & Trust governance cards, Operational KPIs grid.
- **Decision Replay** flight-recorder timeline.
- **Interactive Execution Sandbox** terminal with three modes (Liquidity / Compliance / ROAS).
- Five-division grid + Demo CTA. Live Console pill in the nav links to `/console`.

Naming + email conventions preserved: Counsel/Estate/Capital/Signal/Risk; `hello@mizoki3.com`; `/console` deep link.

**React sibling project added: `MIZOKI3-Site (1)/`** (40 files, 468K). Vite + Tailwind + React + lucide. Self-contained — its own `Dockerfile`, `nginx.conf`, `cloudbuild.yaml`, `package.json`, `vite.config.js`, `tailwind.config.js`, `src/components/`, and a parallel `infrastructure/main.tf`. Treated as a **sibling deliverable**, not a replacement for the Flask static site. Awkward folder name (literal "MIZOKI3-Site (1)") is the downloaded-zip artifact — rename if you want; nothing depends on the path.

Also committed: `preview.html` (standalone single-file design preview), 2 ChatGPT reference screenshots from 2026-05-19.

**Operational cleanup performed earlier on 2026-05-22:**

- **Branch cleanup on the `MIZOKICloudRun` repo** (sibling repo in the same org — not this repo): deleted 4 stale branches that were 0-files-different vs main — `claude/mizoki3-homepage-Rp13x`, `copilot/sub-pr-524`, `copilot/sub-pr-559`, `copilot/sub-pr-559-again`. Only `main` remains.
- **Restarted the boss agent** on Cloud Run: rolled `boss-agent-adk` from revision `00218-w9m` → `00219-9zh` via `gcloud run services update boss-agent-adk --update-env-vars RESTARTED_AT=…`. The `RESTARTED_AT` env var is the kick mechanism; it doesn't carry meaning. Use the same trick to roll any other service. Of the five boss-related services (`boss-agent`, `boss-agent-adk`, `boss-agent-backend`, `boss-agent-service`, `boss-rewoo-orchestrator`), `boss-agent-adk` is the most active (rev 218+) and the de-facto primary.

#### Operational lore — gotchas worth remembering

- **Watch for accidental `mizoki3-site/` renames.** On 2026-05-22 the folder was renamed by a Finder drag to `mizoki3-site_claude'/` (trailing apostrophe, looks like a typo). The Flask routes `/console`, `/console/<path>`, and `/infrastructure/main.tf` hard-code the canonical path, so a rename breaks the live site instantly. If you see `mizoki3-site/` "deleted" in git status alongside a similar-looking untracked folder, **don't push the deletion** — diff the file SHAs against `origin/main:mizoki3-site/*` first; if they match, it's a recovery, not a content change. Restore with `mv "mizoki3-site_<whatever>" mizoki3-site`.
- **Google Drive sync makes `git add` on directories with many small files extremely slow** (or hangs entirely — process consumes ~0s of CPU but never returns). If `git add` on a directory like `MIZOKI3-Site (1)/` doesn't finish in a few seconds, kill it (`kill <pid>`), `rm -f .git/index.lock`, and stage the files in smaller batches.
- **Sign In wiring** lives in two places that must stay in sync: `app.py` constants `EXTERNAL_LOGIN_URL` + `EXTERNAL_DASHBOARD_URL`, and `index.html` `<a class="nav-signin" href="/login">`. Both should point at the command-center Cloud Run service. As of 2026-05-19 the canonical command center is `https://miz-oki-command-center-ui-ehqxake3ia-uc.a.run.app`. The legacy `https://mizoki.mizoki3.com` subdomain is dead — don't restore it.

### Sign In Routing (2026-05-19)
- Fixed homepage Sign In: `index.html` `nav-signin` now `href="/login"` (was `href="#contact"`, an in-page anchor that scrolled to the contact section — "the weird spot").
- `app.py` constants `EXTERNAL_LOGIN_URL` and `EXTERNAL_DASHBOARD_URL` updated from the dead `https://mizoki.mizoki3.com` to `https://miz-oki-command-center-ui-ehqxake3ia-uc.a.run.app/{login,dashboard}` — the live command-center UI Cloud Run service.
- The legacy marketing HTMLs (`investor.html`, `industries.html`, `roi.html`, `walkthrough.html`, `resources.html`, `how-it-works.html`, `sales-one-pager.html`, `demo-opener.html`, `pricing.html`, and the `11/` and `legacy_mizoki_site/` mirrors) still hardcode `https://mizoki.mizoki3.com` in their Login buttons. They all 301 to `/` via `legacy_marketing_page()` so users never see them — flag if you want them scrubbed.

### Python Bytecode Hygiene (2026-05-19)
Added `__pycache__/`, `*.py[cod]`, `*.pyo` to `.gitignore` and removed 7 previously-tracked `.pyc` files (`app.cpython-313.pyc` and friends). Bytecode no longer pollutes `git status`.

### Homepage Rebuild to Five-Division MIZOKI3 Design (2026-05-18)
Full rebuild of `index.html` to match the official MIZOKI3.com mockups:
- Hero: "One Intelligence. Many Domains. Shared Causal Memory." with a NEXUS "Brain" SVG showing five division nodes orbiting the core.
- MIZOKI3 Flywheel: five-step compounding loop (Signal Enters → Graph Updates → Cross-Domain Impact → Better Decisions → Lasting Memory) with live stats strip.
- SRPVDAL Orchestration: seven-stage iconed loop.
- Decision Control Plane summary panel that deep-links into the standalone `/console`.
- One-Brain-Five-Lenses bento: COUNSEL, ESTATE, CAPITAL, SIGNAL, RISK. Replaces the old per-cell narrative.
- Live Nexus Snapshot: Acme Holdings entity graph + recent-activity feed.
- Governance: Counterfactual Simulation Engine chart + Decision Eligibility Layer score gauge (87 → "Eligible for Autonomous Action").
- Use cases, demo flow, CTA, footer.

Naming consolidation: Legal → **Counsel**, Media Acquisition → **Signal**. The standalone console sidebar was updated to add the Signal lens so the five-division naming is consistent everywhere (homepage, console, Flask routes).

Late-day refinement (2026-05-18, evening):
- New Chapter 06 "Verification & Arbitration" between the Decision Control Plane and Divisions: an animated execution trace of ACT-991 (Capital proposes a $5M distribution, V&A detects the COV-01 covenant breach, DEL scores it ineligible, DCP stamps VETOED, system re-routes to a safe Option B). The decision shown two ways — animated veto trace + the existing static liquidity chart.
- SOC 2 / ISO 27001 badge removed from the hero (the company is not certified yet — claiming an in-progress cert on an infrastructure site sold to regulated buyers is a real liability). Replaced with "Customer-Managed Encryption", which is true since the Terraform provisions CMEK.
- Contact email canonical at `hello@mizoki3.com` (a stray `pilot@mizoki3.com` from an alternate draft was rejected).

Added `mizoki3-site/README.md` packaging doc that walks through four deploy options (any static host / GCS / Cloud Run / Firebase) plus Terraform usage.

### `mizoki3-site/` Sub-Tree (2026-05-17)
- `mizoki3-site/console/index.html` — standalone Decision Control Plane (Risk Arbitration Console UI). Sidebar carries Counsel/Estate/Capital/Signal/Risk + Nexus TCKG substrate + Decision Control. SRPVDAL execution trace, TCKG subgraph SVG, decision queue.
- `mizoki3-site/infrastructure/main.tf` — Google Cloud Terraform module for the fiduciary substrate. Matches the actual stack: private VPC, Cloud Spanner with the GoogleSQL property-graph schema for TCKG, Pub/Sub event bus, Cloud Run for SRPVDAL/LangGraph orchestration, Vertex AI Model Garden for Claude reasoning isolation (publisher-model IAM condition pinning), Cloud KMS for encryption.
  - **Outstanding:** the Vertex AI binding pins `claude-3-5-sonnet-v2@20241022`. Bump to the current approved Claude model on Vertex AI Model Garden before any production apply.
  - **Migration note:** an earlier draft of this file used AWS (Bedrock, Neptune, MSK, EKS) — replaced 2026-05-18 because the website and orchestration actually run on Cloud Run, and reasoning runs on Vertex AI, not Bedrock.

### Flask Routes for Console + Infrastructure (2026-05-17)
Added in `app.py` (mirrors the `/blog/` and `/11/` patterns):
- `/console`, `/console/`, `/console/index.html` → serves `mizoki3-site/console/index.html`.
- `/console/<path:filename>` → serves any sub-asset under that directory.
- `/infrastructure/main.tf` → serves the Terraform module as `text/plain`.

Background: the homepage "Launch the Live Console" button pointed at `console/index.html`, but the file lived under `mizoki3-site/console/` with no Flask route, so it 404-ed on the live site. Routes resolved that.

### Branch Cleanup + Dependabot Bump (2026-05-17)
- Cherry-picked dependabot commit `54153c8` into main: Flask `3.0.3 → 3.1.3` in both `requirements.txt` and `mizoki-website-all-files/requirements.txt`.
- Deleted `origin/pre-migration-backup` (held the pre-MIZOKI3 MIZ OKI 3.5 site — kept only as a git-history reference, no longer needed; closed Copilot PR #2 as a side effect).
- Deleted `origin/dependabot/pip/pip-6f6034b2da` after the cherry-pick landed.
- Local safety tag `pre-backup-merge-safety` left in place (points at `f747688`) — not pushed; remove with `git tag -d pre-backup-merge-safety` when no longer wanted.

### Deployment Pipeline Status
- **Auto-deploy on push to `main` works as of 2026-05-18.** Every push triggers `.github/workflows/deploy-cloudrun.yml`, which builds the Docker image with Cloud Build, pushes to `gcr.io/spry-bus-425315-p6/mizoki-website:<sha>`, and rolls out a new Cloud Run revision. End-to-end run time: ~60 seconds.
- Service: `mizoki-website`, region `us-central1`, project `spry-bus-425315-p6`. Custom domain: `mizoki3.com`.
- **Manual fallback:** `./deploy.sh` still works the same way (Cloud Build → GCR → `gcloud run deploy`) when you need to deploy from your laptop without going through git.

#### GitHub Actions auth — Workload Identity Federation
The workflow authenticates via WIF, not a service-account key. No long-lived secrets in GitHub.

GCP setup (one-time, lives in `spry-bus-425315-p6`):
- Workload identity pool: `github-actions` (location `global`)
- OIDC provider: `github`, `issuer-uri=https://token.actions.githubusercontent.com`, `attribute-condition=assertion.repository_owner=='mediaintelligence'`
- Service account: `miz-oki-website-deployer@spry-bus-425315-p6.iam.gserviceaccount.com`
  - Roles: `run.admin`, `cloudbuild.builds.builder`, `iam.serviceAccountUser`, `storage.admin`, `serviceusage.serviceUsageAdmin`
- Binding (`roles/iam.workloadIdentityUser`) is `principalSet://…/attribute.repository/mediaintelligence/mizoki-3-5-website` — scoped to this repo only. No other GitHub repo can impersonate the deployer SA.

Repo secrets (set via `gh secret set`):
- `GCP_PROJECT_ID` = `spry-bus-425315-p6`
- `WIF_PROVIDER` = `projects/698171499447/locations/global/workloadIdentityPools/github-actions/providers/github`
- `WIF_SERVICE_ACCOUNT` = `miz-oki-website-deployer@spry-bus-425315-p6.iam.gserviceaccount.com`

To rotate the trust: delete and recreate the WIF provider in GCP, or revoke the principalSet binding on the deployer SA. To extend to another repo: add another `principalSet://…/attribute.repository/<owner>/<repo>` binding on the SA — don't widen the attribute condition.

### Verification Standard for May 2026 Changes
- `python3 -m py_compile mizoki_runtime/runtime.py app.py`
- `python3 -m unittest tests.test_app tests.test_runtime` — 25 passing tests.
- Smoke-test new routes via `app.test_client()` before pushing.

---

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
4. **Deployment**: Changes go live via `./deploy.sh` or `./master-deploy.sh`

---

## Contact

- Website: mizoki3.com
- Sales: sales@mizoki.com
