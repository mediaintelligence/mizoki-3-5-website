# AGENTS.md - AI Assistant Context

## Project Overview

**MIZ OKI 3.5** is a Verifiable Autonomous Decision Intelligence Platform. This repository contains the marketing website deployed on Google Cloud Run.

## 🔒 SOURCE OF TRUTH & DEPLOY GOVERNANCE (LOCKED 2026-07-30)

**This document and `CLAUDE.md` are the ONLY sources of truth for this site.**
The v1.5 "night dossier" look and feel is LOCKED (`canon.lock.json`, 19 core
surfaces, sha256-pinned; see `docs/DESIGN_CANON.md`), and `/demo` + the
Executive Briefing are the core of the operation.

**Nothing ships to production without specific human approval:**

- The deploy workflow (`deploy-homepage.yml`) is manual-dispatch-ONLY and
  requires a human to type `APPROVED`; it refuses any tree that fails
  `python3 scripts/check_design_canon.py`.
- There is NO push-triggered deploy; the Deploy Router no longer matches
  this workflow. `deploy.sh` / `master-deploy.sh` carry the same approval
  gate (`MIZOKI_DEPLOY_APPROVED=APPROVED` or interactive confirmation).
- Canon-pinned files change only on an explicit human instruction, with the
  lockfile re-pinned (`check_design_canon.py --update`) in the same change.
- Agents: never dispatch the deploy workflow, run the deploy scripts, or
  edit canon files without that explicit human instruction.

## Architecture

- **Deployment**: Docker container on Google Cloud Run
- **Web Server**: Nginx serving static HTML
- **Domain**: mizoki3.com (Cloud Run custom domain)

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

## Contact

- Website: mizoki3.com
- Sales: sales@mizoki.com
