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
├── mizoki3-site/
│   ├── console/index.html        # Standalone Decision Control Plane
│   │                             # (Risk Arbitration Console UI)
│   └── infrastructure/main.tf    # Terraform for the fiduciary substrate
│                                 # (VPC, Neptune TCKG, MSK, EKS, Bedrock IAM)
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

## Recent Work (May 2026)

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

### `mizoki3-site/` Sub-Tree (2026-05-17)
- `mizoki3-site/console/index.html` — standalone Decision Control Plane (Risk Arbitration Console UI). Sidebar carries Counsel/Estate/Capital/Signal/Risk + Nexus TCKG substrate + Decision Control. SRPVDAL execution trace, TCKG subgraph SVG, decision queue.
- `mizoki3-site/infrastructure/main.tf` — Terraform module for the fiduciary substrate (zero-trust VPC, Neptune TCKG, MSK serverless event bus, EKS for SRPVDAL/LangGraph orchestration, Bedrock IAM isolation, KMS).
  - **Outstanding:** the Bedrock IAM policy still pins `claude-3-5-sonnet-20240620-v1:0`. Bump to the current approved Claude model on Bedrock before any production apply.

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
- **Live deploys to Cloud Run go through `./deploy.sh`** (Cloud Build → GCR → `gcloud run deploy`). Service: `mizoki-website`, region `us-central1`, project `spry-bus-425315-p6`.
- **GitHub Actions auto-deploy is broken** (`.github/workflows/*.yml`) — has been failing on every push since 2026-05-15 because the `GCP_PROJECT_ID` and `GCP_SA_KEY` repo secrets are not configured (`gh secret list` returns empty). The workflow errors at the `google-github-actions/auth@v2` step. To fix: either set the two secrets via `gh secret set`, or migrate the workflow to Workload Identity Federation. Until then, deploys are manual.

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
