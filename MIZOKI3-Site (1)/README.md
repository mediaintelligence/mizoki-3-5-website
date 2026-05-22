# MIZOKI3 — Marketing Site, Operations Console & Infrastructure

**MIZOKI3 — Autonomous Strategic Intelligence Infrastructure.**
One Intelligence. Many Domains. Shared Causal Memory.

This package contains three deliverables: the public marketing/GTM website
(React + Vite), the Decision Control Plane operations console (standalone
HTML), and the Google Cloud infrastructure as Terraform.

---

## 1. Package Contents

```
mizoki3-site/
├── src/
│   ├── main.jsx                React entry
│   ├── App.jsx                 Section composition + reveal observer
│   ├── data.js                 All content (Counsel/Estate/Capital/Signal/Risk + more)
│   ├── index.css               Tailwind + custom CSS
│   └── components/             17 section components
│       ├── Nav.jsx · Hero.jsx · Manifesto.jsx · Overview.jsx
│       ├── Flywheel.jsx · Orchestration.jsx · DCP.jsx · Veto.jsx
│       ├── Divisions.jsx · Nexus.jsx · Memory.jsx
│       ├── Governance.jsx · Infrastructure.jsx
│       ├── Demo.jsx · UseCases.jsx · CTA.jsx · Footer.jsx
├── public/
│   ├── assets/                 11 brand infographics (PNG)
│   └── console/index.html      Operations console (standalone)
├── index.html                  Vite entry HTML
├── package.json                React 18 · Vite 6 · Tailwind 3.4 · lucide-react
├── vite.config.js
├── tailwind.config.js          Custom division colors + fonts
├── postcss.config.js
├── infrastructure/
│   ├── main.tf                 Google Cloud Terraform
│   └── terraform.tfvars.example
├── Dockerfile                  Multi-stage: Node build → nginx serve
├── nginx.conf                  Cloud Run port 8080 + SPA fallback
├── cloudbuild.yaml             Cloud Build → Cloud Run pipeline
├── archive/                    Previous static-HTML version (preserved)
├── .dockerignore · .gitignore
└── README.md                   This file
```

The site is a single-page React app with 13 chapters: Premise, Complete
Picture, Compounding Engine, SRPVDAL Orchestration, Decision Control Plane,
Verification & Arbitration, One Brain·Many Lenses (Divisions), Central
Nervous System (Nexus), Memory, Governed Autonomy, Fiduciary-Grade
Infrastructure, How a Pilot Begins, Who Operates With MIZOKI3.

---

## 2. The Website (React + Vite)

### 2.1 Develop locally

```bash
cd mizoki3-site
npm install            # one-time
npm run dev            # http://localhost:5173 with hot reload
```

### 2.2 Build the static bundle

```bash
npm run build          # writes optimized output to dist/
npm run preview        # serve dist/ locally at http://localhost:8080
```

### 2.3 Deploy — Cloud Run (recommended)

The platform itself runs on Cloud Run, so the site deploys the same way.
The `Dockerfile` is multi-stage: a Node stage runs `npm install` and
`vite build`, then an nginx stage serves the bundle on port 8080.

```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=SHORT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo manual)
```

To test the container locally before pushing:

```bash
docker build -t mizoki3-website .
docker run -p 8080:8080 mizoki3-website
# open http://localhost:8080
```

### 2.4 Deploy — alternative static hosts

The `dist/` output is plain static files, so any static host works after
`npm run build`:

```bash
# Google Cloud Storage
gcloud storage cp -r dist/* gs://www.mizoki3.com/

# Firebase Hosting
firebase init hosting          # set public directory to "dist"
firebase deploy --only hosting

# Netlify / Vercel / Cloudflare Pages — upload dist/
```

---

## 3. The Operations Console

`public/console/index.html` is the Decision Control Plane terminal — a
standalone static page in the same brand style, with a live self-typing
SRPVDAL loop. Vite copies the entire `public/` folder into `dist/` verbatim,
so the console is available at `/console/` once deployed. The nginx config
serves it without the SPA fallback so deep links work cleanly.

---

## 4. The Infrastructure (Terraform)

`infrastructure/main.tf` provisions the MIZOKI3 backend on **Google Cloud**.
It is the cloud the website describes in its Architecture chapter.

### 4.1 What it provisions

| Component                | Google Cloud service                            |
|--------------------------|--------------------------------------------------|
| Zero-trust network       | VPC + private subnet + Cloud NAT + firewall      |
| TCKG substrate           | Neo4j (Compute Engine) + BigQuery dataset + GCS  |
| Nexus event bus          | Cloud Pub/Sub topic + subscription               |
| SRPVDAL orchestrator     | Cloud Run service (internal-only ingress)        |
| Reasoning isolation      | Vertex AI — current Claude models only           |
| Fiduciary encryption     | Cloud KMS (CMEK, 90-day rotation)                |

Reasoning is pinned to current-generation Claude on Vertex AI
(**Opus 4.7, Opus 4.6, Sonnet 4.6**). Older generations (`claude-3.x`) are
intentionally excluded — see the `approved_claude_models` variable.

### 4.2 Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) ≥ 1.5
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`)
- A GCP project with billing enabled
- These APIs enabled:

```bash
gcloud services enable \
  compute.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com \
  cloudkms.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  --project=YOUR_PROJECT_ID
```

- Authentication for Terraform:

```bash
gcloud auth application-default login
```

### 4.3 Configure and deploy

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set project_id (and region if not us-central1).

terraform init      # download the Google provider
terraform validate  # check syntax
terraform plan      # review what will be created
terraform apply     # provision (type "yes" to confirm)
```

After apply, `terraform output` prints the orchestrator URL and the approved
model list. To tear down: `terraform destroy` (the Cloud KMS key is guarded
by `prevent_destroy` — remove that lifecycle block first, deliberately).

---

## 5. Notes

- **Project ID** — `main.tf` defaults `project_id` to `mizoki3-prod`.
  Override it in `terraform.tfvars`.
- **`npm install` not run here** — the build environment for this package
  doesn't ship with Node, so dependencies were declared in `package.json`
  but not installed. Run `npm install` locally before `npm run dev` or the
  first Cloud Build (Cloud Build's Docker stage installs them automatically).
- **Terraform not validated here** — `terraform` CLI was unavailable.
  Run `terraform validate` once before your first `apply`.
- **Compliance** — the site claims architectural posture (Customer-Managed
  Encryption, Zero-Trust Deployment, Audit-Ready by Default), **not**
  certifications. Add SOC 2 / ISO badges only after the audits complete.
- **Contact** — the website's CTA points to `hello@mizoki3.com`.

---

© 2026 MIZOKI3, Inc. · Miami, FL · Connecticut
