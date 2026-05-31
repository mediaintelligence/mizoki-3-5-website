# MIZOKI3 — Marketing Site, Operations Console & Infrastructure

**MIZOKI3 — Autonomous Strategic Intelligence Infrastructure.**
One Intelligence. Many Domains. Shared Causal Memory.

This package contains three deliverables: the public marketing/GTM website, the
Decision Control Plane operations console, and the Google Cloud infrastructure
as Terraform.

---

## 1. Package Contents

```
mizoki3-site/
├── index.html                 Main single-page website (10 chapters)
├── console/
│   └── index.html             Decision Control Plane operations console
├── assets/                    11 brand infographics (PNG)
│   ├── 01-hero-system.png
│   ├── 02-editorial-overview.png
│   ├── 03-canonical-loop.png
│   ├── 04-orchestration-framework.png
│   ├── 05-governance.png
│   ├── 06-knowledge-graph.png
│   ├── 07-legal-cell.png
│   ├── 08-estate-cell.png
│   ├── 09-risk-cell.png
│   ├── 10-media-cell.png
│   └── 11-nexus.png
├── infrastructure/
│   ├── main.tf                Google Cloud Terraform (Cloud Run, BigQuery,
│   │                          Neo4j, Pub/Sub, Vertex AI, Cloud KMS, VPC)
│   └── terraform.tfvars.example   Example variable values
├── Dockerfile                 Container image for the website (nginx)
├── nginx.conf                 nginx config (Cloud Run port 8080)
├── cloudbuild.yaml            Cloud Build → Cloud Run deploy pipeline
├── .dockerignore
└── README.md                  This file
```

Everything in the website resolves with **relative paths**, so it works from a
domain root or any sub-path without modification.

---

## 2. The Website

The website is a static single-page site — pure HTML, CSS, and a small amount of
vanilla JavaScript. No build step, no framework, no dependencies. The only
external requests are Google Fonts.

### 2.1 Preview locally

Open `index.html` directly in a browser, or serve the folder so the relative
asset paths resolve cleanly:

```bash
cd mizoki3-site
python3 -m http.server 8080
# then open http://localhost:8080
```

The operations console is reachable at `http://localhost:8080/console/`.

### 2.2 Deploy — Option A: any static host

Upload the entire `mizoki3-site/` folder (minus `infrastructure/`, `Dockerfile`,
`nginx.conf`, `cloudbuild.yaml`) to Netlify, Vercel, Cloudflare Pages, GitHub
Pages, or similar. No configuration required — `index.html` is the entry point.

### 2.3 Deploy — Option B: Google Cloud Storage (static hosting)

```bash
# Create a bucket named for your domain
gcloud storage buckets create gs://www.mizoki3.com --location=US

# Upload the site
gcloud storage cp index.html  gs://www.mizoki3.com/
gcloud storage cp -r console  gs://www.mizoki3.com/
gcloud storage cp -r assets   gs://www.mizoki3.com/

# Make objects public and set the entry document
gcloud storage buckets update gs://www.mizoki3.com --web-main-page-suffix=index.html
gsutil iam ch allUsers:objectViewer gs://www.mizoki3.com
```

Then point your domain at the bucket via a Cloud Load Balancer for HTTPS.

### 2.4 Deploy — Option C: Cloud Run (recommended)

Since the MIZ OKI platform already runs on Cloud Run, the website ships with a
`Dockerfile` (nginx) and a `cloudbuild.yaml` so it deploys the same way as the
32 platform cells.

```bash
# One-shot build + deploy
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=SHORT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo manual)

# Or build and run locally to test the container first
docker build -t mizoki3-website .
docker run -p 8080:8080 mizoki3-website
# open http://localhost:8080
```

The container listens on port `8080` (the Cloud Run default). nginx serves
`index.html`, `console/`, and `assets/`, with a 7-day cache on images.

### 2.5 Deploy — Option D: Firebase Hosting

```bash
firebase init hosting          # set public directory to "."
firebase deploy --only hosting
```

---

## 3. The Operations Console

`console/index.html` is the Decision Control Plane terminal — a standalone page
in the same dark brand style, with a live self-typing SRPVDAL loop. It is linked
from the main site (the DCP section and the footer) and back-links to the
homepage. It deploys automatically with any of the website options above; no
separate steps are needed.

---

## 4. The Infrastructure (Terraform)

`infrastructure/main.tf` provisions the MIZOKI3 backend on **Google Cloud**.
It is the cloud the website describes in its Architecture chapter.

### 4.1 What it provisions

| Component                | Google Cloud service                          |
|--------------------------|------------------------------------------------|
| Zero-trust network       | VPC + private subnet + Cloud NAT + firewall    |
| TCKG substrate           | Neo4j (Compute Engine) + BigQuery dataset + GCS |
| Nexus event bus          | Cloud Pub/Sub topic + subscription             |
| SRPVDAL orchestrator     | Cloud Run service (internal-only ingress)      |
| Reasoning isolation      | Vertex AI — current Claude models only         |
| Fiduciary encryption     | Cloud KMS (CMEK, 90-day rotation)              |

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

### 4.3 Configure

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your `project_id` (and `region` if not
`us-central1`).

### 4.4 Deploy

```bash
terraform init      # download the Google provider
terraform validate  # check syntax
terraform plan      # review what will be created
terraform apply     # provision (type "yes" to confirm)
```

After apply, `terraform output` prints the orchestrator URL and the approved
model list.

### 4.5 Teardown

```bash
terraform destroy
```

Note: the Cloud KMS key has `prevent_destroy = true` as a fiduciary safeguard.
To tear the key down, remove that `lifecycle` block first — deliberately.

---

## 5. Notes

- **Project ID** — `main.tf` defaults `project_id` to `mizoki3-prod`. Override
  it in `terraform.tfvars` with your actual project.
- **Terraform not validated here** — the `terraform` CLI was unavailable in the
  build environment. Run `terraform validate` before your first `apply`.
- **CMEK service agents** — the Terraform grants Cloud KMS decrypt rights to the
  Compute, Storage, Pub/Sub, and BigQuery service agents. If `apply` reports a
  missing service agent, run a no-op create for that service first (e.g. enable
  the API), then re-apply.
- **Contact** — the website's CTA points to `hello@mizoki3.com`.

---

© 2026 MIZOKI3, Inc. · Miami, FL
