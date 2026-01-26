# MIZ OKI 3.5 — Verifiable Autonomous Decision Intelligence

[![Deploy to Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-4285F4?logo=google-cloud)](https://console.cloud.google.com/run)
[![GitHub](https://img.shields.io/badge/GitHub-mediaintelligence%2Fmizoki--website-181717?logo=github)](https://github.com/mediaintelligence/mizoki-website)

> **Decisions verified before execution—not explained after failure.**

MIZ OKI 3.5 is the first Business General Intelligence platform where autonomous agents propose actions, but a **Decision Control Plane** verifies, simulates, and authorizes every decision before execution.

---

## 🏗️ The SRDPV-DAL Pipeline

```
SENSE → REASON → PLAN → VALIDATE → DECIDE → ACT → LEARN
   ↑                                              |
   └──────────── Continuous Learning ─────────────┘
```

| Stage | Controller | Function |
|-------|------------|----------|
| **SENSE** | SENSE-ADC | Autonomous attention allocation, priority scoring |
| **REASON** | REASON-ADC | Causal GraphRAG, confounder detection |
| **PLAN** | PLAN-ADC | Multi-objective strategy generation |
| **VALIDATE** | VAL | Independent verification by multiple agents |
| **DECIDE** | DCP | Authorization scoring, approve/modify/reject |
| **ACT** | ACT-ADC | Execution with adaptive rollback |
| **LEARN** | LEARN-ADC | Outcome-based model updates |

---

## 🌐 Live URLs

| Domain | Purpose |
|--------|---------|
| [mizoki3.com](https://mizoki3.com) | Main website |
| [www.mizoki3.com](https://www.mizoki3.com) | Main website (www) |
| [mizoki.mizoki3.com](https://mizoki.mizoki3.com) | Platform login portal |
| [miz.mizoki3.com](https://miz.mizoki3.com) | Documentation portal |

---

## 📁 Repository Structure

```
mizoki-website/
│
├── 🧠 Application
│   ├── app.py                  # Flask entrypoint for Cloud Run
│   ├── templates/index.html    # Neuro-Grid landing page
│   └── requirements.txt        # Runtime dependencies
│
├── 🏠 Legacy Pages
│   ├── index.html              # Previous static homepage
│   ├── login.html              # Platform login (mizoki.mizoki3.com)
│   ├── how-it-works.html       # SRDPV-DAL pipeline deep-dive
│   ├── platform.html           # Four-layer architecture
│   ├── security.html           # Quantum-resistant security
│   ├── industries.html         # Industry templates
│   ├── pricing.html            # Enterprise/Growth/Pilot tiers
│   ├── case-studies.html       # Customer success stories
│   ├── roi.html                # Interactive ROI calculator
│   ├── walkthrough.html        # 12-minute demo request
│   ├── investor.html           # Investor overview
│   ├── sales-one-pager.html    # Quick sales summary
│   └── resources.html          # Documentation hub
│
├── 📝 Blog
│   ├── blog/index.html                      # Blog listing
│   ├── blog/decision-control-plane.html     # DCP deep-dive
│   └── blog/relu-lens-meta-algorithm.html   # ReLU Lens article
│
├── 🎨 Assets
│   ├── assets/css/             # Stylesheets
│   ├── assets/img/             # Images
│   └── assets/pdf/             # Downloadable documents
│
├── ⚙️ Infrastructure
│   ├── Dockerfile              # Python + gunicorn container
│   ├── cloudbuild.yaml         # Google Cloud Build config
│   ├── deploy.sh               # One-click deployment
│   ├── master-deploy.sh        # Multi-service deploy
│   └── github-push.sh          # Git helper script
│
└── 📚 Documentation
    ├── README.md               # This file
    └── CLAUDE.md               # AI assistant guide
```

---

## 🚀 Quick Deploy

### Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- Google Cloud Project with billing enabled
- Authenticated: `gcloud auth login`

### One-Click Deployment

```bash
# Clone the repository
git clone https://github.com/mediaintelligence/mizoki-website.git
cd mizoki-website

# Deploy to Cloud Run
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. ✅ Authenticate with Google Cloud
2. ✅ Enable required APIs (Cloud Build, Container Registry, Cloud Run)
3. ✅ Build Docker container
4. ✅ Deploy the Flask app to Cloud Run
5. ✅ Output your live URL

### Manual Deployment

```bash
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/mizoki-website
gcloud run deploy mizoki-website \\
  --image gcr.io/$PROJECT_ID/mizoki-website \\
  --region us-central1 \\
  --platform managed \\
  --allow-unauthenticated \\
  --port 8080
```

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:8080` to view the Neuro-Grid landing page.

---

## 🔧 Domain Configuration

### Adding Custom Domains

```bash
# Map a custom domain
gcloud beta run domain-mappings create \
  --service mizoki-website \
  --domain your-domain.com \
  --region us-central1
```

### Current Domain Mappings

```bash
# List all domain mappings
gcloud beta run domain-mappings list --region us-central1
```

### DNS Records Required

| Domain | Record Type | Value |
|--------|-------------|-------|
| `@` (root) | A | (provided by Cloud Run) |
| `www` | CNAME | `ghs.googlehosted.com.` |
| `mizoki` | CNAME | `ghs.googlehosted.com.` |

---

## 🎨 Design System

### Colors

| Variable | Hex | Usage |
|----------|-----|-------|
| `--bg-color` | `#050505` | Page background |
| `--text-color` | `#e0e0e0` | Primary text |
| `--accent-color` | `#00d4ff` | Neuro-Grid accents |
| `--highlight-color` | `#ff9f1c` | Primary calls-to-action |

### Typography

- **Headlines + Body:** Rajdhani

---

## 📈 Key Metrics

| Metric | Value |
|--------|-------|
| Decision Velocity | **50-75× faster** |
| Revenue Leakage Reduction | **↓35%** |
| Operational Cost Reduction | **↓41%** |
| Payback Period | **3.2 months** |
| Automation Coverage | **89%** |
| Query Latency | **<100ms** |
| Full Decision Cycle | **<60 seconds** |

---

## 🔒 Security Features

- **Quantum-Resistant Cryptography** — CRYSTALS-Kyber (key encapsulation), CRYSTALS-Dilithium (signatures)
- **Immutable Audit Logs** — Every decision cryptographically signed and logged
- **Human-in-the-Loop** — Full override capability, configurable escalation
- **Multi-Tenant Isolation** — Kubernetes namespace separation
- **Federated Learning** — Cross-tenant improvement with differential privacy

---

## 🛠️ Development

### Local Testing

```bash
# Build and run locally with Docker
docker build -t mizoki-website .
docker run -p 8080:8080 mizoki-website

# Open http://localhost:8080
```

### Making Changes

1. Edit HTML files directly (styles are inline)
2. Test locally with Docker
3. Commit changes: `git add -A && git commit -m "Your message"`
4. Deploy: `./deploy.sh`

### Adding New Pages

1. Copy an existing page as template
2. Update navigation in ALL HTML files
3. Add to Dockerfile if in a subdirectory
4. Update CLAUDE.md structure section

---

## 📊 Monitoring

```bash
# View service logs
gcloud run services logs read mizoki-website --region us-central1

# View service status
gcloud run services describe mizoki-website --region us-central1

# View in console
# https://console.cloud.google.com/run/detail/us-central1/mizoki-website/metrics
```

---

## 💰 Cost Estimate

Cloud Run pricing (scale-to-zero enabled):

| Resource | Cost |
|----------|------|
| CPU | $0.00002400/vCPU-second |
| Memory | $0.00000250/GiB-second |
| Requests | $0.40/million |

**Typical cost for marketing website: $5-20/month**

---

## 🐛 Troubleshooting

### Build Fails

```bash
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

### Deploy Fails

```bash
gcloud run services describe mizoki-website --region us-central1
```

### Site Not Loading

```bash
gcloud run services logs read mizoki-website --region us-central1 --limit=50
```

### SSL Certificate Issues

Certificates auto-provision when DNS is correctly configured. Check:
```bash
gcloud beta run domain-mappings describe --domain your-domain.com --region us-central1
```

---

## 📞 Contact

- **Sales:** sales@mizoki.com
- **Documentation:** [resources.html](https://mizoki3.com/resources.html)
- **Demo Request:** [walkthrough.html](https://mizoki3.com/walkthrough.html)
- **GitHub:** [mediaintelligence/mizoki-website](https://github.com/mediaintelligence/mizoki-website)

---

## 📄 License

© 2026 MIZ OKI. All rights reserved.

*Every action logged. Every decision auditable.*
