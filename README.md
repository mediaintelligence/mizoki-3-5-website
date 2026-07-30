# MIZOKI3 — Website

Marketing site for **MIZOKI3 — a Verifiable Autonomous Decision Intelligence Platform**.
Canonical hero line: **"A nervous system for your business."**

Live at **[mizoki3.com](https://mizoki3.com)** on Google Cloud Run.

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
python3.13 -m unittest tests.test_app tests.test_runtime   # 73 passing
```

> **Gotcha:** the machine's default `python3` is Homebrew 3.14 **without Flask**, so `tests.test_app`
> ImportErrors there (only `test_runtime` runs). Use **`python3.13`** (has Flask) for the app tests
> and the local server.

## Deployment

Push to `main` → the **`deploy-cloudrun.yml`** GitHub Actions workflow (Workload Identity Federation —
no long-lived keys) builds the Docker image and rolls a new Cloud Run revision in ~60s. Manual
fallback: `./deploy.sh`.

## Recent updates (2026-07-03)

- **Manufacturing** added as a first-class 6th example-domain lens — new `manufacturing/` page, wired
  into the homepage hero graph, schema inspector, executable simulation, §04 divisions panel, and the
  footer on every page; `/manufacturing` Flask route + sitemap entry.
- **Homepage connector gateway expanded 9 → 12** — added Shopify, Meta Ads, Klaviyo, DV360 (removed
  Stripe); §01 canonical-event copy now names Google Ads · Meta · Shopify.
- Added the **Creative Single Point of Truth v1.0** canonical reference doc.

See [`CLAUDE.md`](CLAUDE.md) → *Recent Work (July 2026)* for the full engineering log.
