# AGENTS.md - AI Assistant Context

## Project Overview

**MIZ OKI 3.5** is a Verifiable Autonomous Decision Intelligence Platform. This repository contains the marketing website deployed on Google Cloud Run.

## Architecture

- **Deployment**: Docker container on Google Cloud Run
- **Web Server**: Nginx serving static HTML
- **Domain**: mizoki3.com (Cloud Run custom domain)

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
├── Dockerfile                    # Container definition
├── nginx.conf                    # Web server config
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

## Recent Work (January 2026)

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

## Cursor Cloud specific instructions

This repo is a **Flask app** (`app.py` + `mizoki_runtime/`) that serves the static
marketing HTML and a decision-intelligence API; it is **not** a Node/build-step project,
and the `nginx.conf` mentioned elsewhere is legacy/deprecated. There is no lint or build
step — "lint" here means `py_compile`, and HTML pages are self-contained (no bundler).

- **Python env**: a shared virtualenv lives at `/home/ubuntu/.venv` (created during cloud
  setup; the startup update script keeps its deps fresh). Use `/home/ubuntu/.venv/bin/python`
  and `/home/ubuntu/.venv/bin/pip`. The only runtime deps are `Flask` + `gunicorn`
  (`requirements.txt`). The sibling repo `mizoki-website` shares this same venv — it pins an
  older Flask (3.0.3) but runs fine on the installed 3.1.3.
- **Run (dev)**: `PORT=8080 /home/ubuntu/.venv/bin/python app.py` (Flask dev server on
  `0.0.0.0:8080`). Production uses gunicorn (see `Dockerfile`), but for development use
  `app.py` directly. There is no hot-reload configured (`debug=False`), so restart the
  process after editing `app.py` / `mizoki_runtime/`.
- **Lint/compile**: `/home/ubuntu/.venv/bin/python -m py_compile mizoki_runtime/runtime.py app.py`
- **Test**: `/home/ubuntu/.venv/bin/python -m unittest tests.test_app tests.test_runtime`
  (32 tests). This is the canonical verification gate before pushing.
- **Smoke / hello-world**: `GET /health` → `healthy`; `GET /api/health` → JSON snapshot;
  the homepage `/` 301-redirects most legacy `*.html` marketing pages. The platform's core
  feature is the **SRPVDAL decision loop**: `POST /api/boss/graph/loop` runs the 7-stage
  Sense→Reason→Plan→Validate→Decide→Act→Learn pipeline and increments
  `graph_native_loop_count` in `/api/health`.
- **Gotcha**: the Boss runtime writes generated artifacts under `data/` (decision logs,
  loop traces, `programmatic_runs.jsonl`). These are git-ignored (only `data/.gitkeep` is
  tracked) — don't commit them. `/api/boss/traces` is a *separate* store from the graph
  loop, so running `/api/boss/graph/loop` will not populate `/api/boss/traces` (use
  `gndi.recent_loops` via `/api/mcp/call`, or watch `graph_native_loop_count`).
- **Out of scope for local dev**: `deploy.sh` / `master-deploy.sh` require `gcloud` auth and
  a real GCP project (Cloud Run) — do not run them to verify changes; use the local dev
  server + unittest instead.

---

## Contact

- Website: mizoki3.com
- Sales: sales@mizoki.com
