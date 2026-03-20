# MIZ OKI 3.5 Website

Verifiable Autonomous Decision Intelligence Platform Website

**7-Stage SRDPV-DAL Pipeline:** SENSE → REASON → PLAN → VALIDATE → DECIDE → ACT → LEARN

**Core Innovations:**
- Decision Control Plane (DCP)
- Validation & Arbitration Layer
- Counterfactual Simulation Engine
- Temporal-Causal Knowledge Graph (TCO-KG)

**Recent Updates:**
- Migrated domain infrastructure to point Google Cloud Global External Load Balancer (mizoki-lb) over to a native Serverless Network Endpoint Group (NEG) hooked to the updated Cloud Run service.
- Added a real Python-based Boss Agent runtime with MCP-style tool registration, skill memory, tool aliases, GraphRAG retrieval, and knowledge-graph-aware routing.
- Exposed Boss/MCP capabilities through Flask JSON APIs for discovery, tool execution, skill learning, and decision traces.
- Synchronized deployment paths for end-to-end orchestration across Cells 1-34.
- Restructured site to use a robust Python/Flask routing engine (`app.py`).
- Implemented canonical URL resolving for the corporate blog directly under `/blog/` on the main domain.
- Stripped legacy subdomains natively with automatic 301 handlers.

---

## 🚀 One-Click Master Deployment

```bash
chmod +x master-deploy.sh
./master-deploy.sh YOUR_GCP_PROJECT_ID https://github.com/YOUR_USERNAME/mizoki-website.git
```

This deploys:
- ✅ Main website to Cloud Run
- ✅ All 12 marketing pages
- ✅ Blog with thought leadership
- ✅ Pushes to GitHub
- ✅ Configures custom domain

---

## Quick Deploy to Google Cloud Run

### Prerequisites

1. **Google Cloud SDK** installed ([Install Guide](https://cloud.google.com/sdk/docs/install))
2. **Google Cloud Project** with billing enabled
3. **Docker** installed (optional - Cloud Build handles this)

### One-Click Deployment

```bash
# Clone or download this repository
cd mizoki-website

# Make deploy script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

That's it! The script will:
1. ✅ Authenticate with Google Cloud
2. ✅ Enable required APIs (Cloud Build, Container Registry, Cloud Run)
3. ✅ Initialize Git repository
4. ✅ Build Docker container using Cloud Build
5. ✅ Deploy to Cloud Run
6. ✅ Output your live URL

### Manual Deployment (Alternative)

If you prefer manual control:

```bash
# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/mizoki-website

# Deploy to Cloud Run
gcloud run deploy mizoki-website \
  --image gcr.io/$PROJECT_ID/mizoki-website \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080
```

### Custom Domain Setup

After deployment, add your custom domain:

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service mizoki-website \
  --domain mizoki3.com \
  --region us-central1

# Follow the DNS verification steps provided
```

### Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| REGION | us-central1 | GCP region for deployment |
| MEMORY | 256Mi | Container memory allocation |
| CPU | 1 | vCPU allocation |
| MIN_INSTANCES | 0 | Minimum running instances (0 = scale to zero) |
| MAX_INSTANCES | 10 | Maximum instances during load |

### File Structure

```
mizoki-website/
├── index.html              # Homepage
├── how-it-works.html       # Technical deep dive
├── platform.html           # Architecture overview
├── security.html           # Security & compliance
├── industries.html         # Industry templates
├── pricing.html            # Pricing tiers
├── case-studies.html       # Customer success stories
├── resources.html          # Documentation hub
├── roi.html                # ROI calculator
├── walkthrough.html        # Demo request
├── investor.html           # Investor overview
├── sales-one-pager.html    # Sales summary
├── assets/                 # Static assets
│   ├── css/
│   ├── img/
│   └── pdf/
├── app.py                  # Core Flask application, page routing, and Boss/MCP APIs
├── mizoki_runtime/
│   ├── __init__.py
│   └── runtime.py          # Boss agent runtime, MCP registry, GraphRAG, and KG integration
├── requirements.txt        # Python pip dependencies
├── Dockerfile              # Container definition (runs `app.py` with gunicorn)
├── cloudbuild.yaml         # Cloud Build deployment config
├── deploy.sh               # One-click deploy script
├── master-deploy.sh        # Advanced deploy and synchronization script
└── README.md               # This file
```

### Monitoring & Logs

```bash
# View logs
gcloud run services logs read mizoki-website --region us-central1

# View metrics in console
# https://console.cloud.google.com/run/detail/us-central1/mizoki-website/metrics
```

### Updating the Site

After making changes:

```bash
# Simply re-run the deploy script
./deploy.sh

# Or manually
gcloud builds submit --tag gcr.io/$PROJECT_ID/mizoki-website:v2
gcloud run deploy mizoki-website --image gcr.io/$PROJECT_ID/mizoki-website:v2 --region us-central1
```

### Cost Estimate

Cloud Run pricing (as of 2026):
- **CPU**: $0.00002400/vCPU-second
- **Memory**: $0.00000250/GiB-second
- **Requests**: $0.40/million requests

With scale-to-zero enabled, you only pay when the site is accessed. Typical cost for a marketing website: **$5-20/month**.

### Troubleshooting

**Build fails:**
```bash
# Check Cloud Build logs
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

**Deploy fails:**
```bash
# Check service status
gcloud run services describe mizoki-website --region us-central1
```

**Site not loading:**
```bash
# Check container logs
gcloud run services logs read mizoki-website --region us-central1 --limit=50
```

### Support

- Documentation: [resources.html](resources.html)
- Demo Request: [walkthrough.html](walkthrough.html)
- Contact: sales@mizoki.com

### Boss Agent and MCP APIs

The Flask app now exposes a concrete Boss/MCP surface:

- `GET /api/health`
- `GET /api/mcp/tools`
- `POST /api/mcp/call`
- `GET /api/boss/discover`
- `POST /api/boss/skills/learn`
- `POST /api/boss/execute`
- `GET /api/boss/traces`

---

© 2026 MIZ OKI. All rights reserved.
