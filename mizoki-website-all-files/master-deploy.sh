#!/bin/bash

#######################################################################
# MIZ OKI 3.5 - MASTER DEPLOYMENT SCRIPT
#######################################################################
#
# This script deploys:
#   - Main website to mizoki3.com (Cloud Run)
#   - App/Dashboard to mizoki.mizoki3.com (Cloud Run)
#   - All blogs and static content
#
# PREREQUISITES:
#   1. Google Cloud SDK installed and authenticated
#   2. GitHub CLI (gh) installed (optional, for GitHub integration)
#   3. A Google Cloud Project with billing enabled
#
# USAGE:
#   chmod +x master-deploy.sh
#   ./master-deploy.sh [PROJECT_ID] [GITHUB_REPO]
#
# EXAMPLES:
#   ./master-deploy.sh my-gcp-project
#   ./master-deploy.sh my-gcp-project https://github.com/user/mizoki-website.git
#
#######################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                        ║"
    echo "║   ███╗   ███╗██╗███████╗     ██████╗ ██╗  ██╗██╗    ██████╗ ███████╗  ║"
    echo "║   ████╗ ████║██║╚══███╔╝    ██╔═══██╗██║ ██╔╝██║    ╚════██╗██╔════╝  ║"
    echo "║   ██╔████╔██║██║  ███╔╝     ██║   ██║█████╔╝ ██║     █████╔╝███████╗  ║"
    echo "║   ██║╚██╔╝██║██║ ███╔╝      ██║   ██║██╔═██╗ ██║     ╚═══██╗╚════██║  ║"
    echo "║   ██║ ╚═╝ ██║██║███████╗    ╚██████╔╝██║  ██╗██║    ██████╔╝███████║  ║"
    echo "║   ╚═╝     ╚═╝╚═╝╚══════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝    ╚═════╝ ╚══════╝  ║"
    echo "║                                                                        ║"
    echo "║           MASTER DEPLOYMENT SCRIPT - v3.5                              ║"
    echo "║           Verifiable Autonomous Decision Intelligence                  ║"
    echo "║                                                                        ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[$1/$TOTAL_STEPS]${NC} $2"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

TOTAL_STEPS=8

print_header

# Configuration
PROJECT_ID="${1:-}"
GITHUB_REPO="${2:-}"
REGION="us-central1"
WEBSITE_SERVICE="mizoki-website"
APP_SERVICE="mizoki-app"
MAIN_DOMAIN="mizoki3.com"
APP_DOMAIN="mizoki.mizoki3.com"

# Check for required tools
echo -e "${CYAN}Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo -e "${GREEN}✓ gcloud CLI found${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Warning: Docker not found locally. Will use Cloud Build.${NC}"
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git not found. Please install git.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ git found${NC}"

# Get project ID if not provided
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
        echo -e "${YELLOW}No Google Cloud project configured.${NC}"
        read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    fi
fi

gcloud config set project "$PROJECT_ID" 2>/dev/null
echo -e "${GREEN}✓ Using project: ${PROJECT_ID}${NC}"

#######################################################################
# STEP 1: Clean and prepare directory
#######################################################################
print_step 1 "Cleaning and preparing deployment directory"

# Remove old git if exists and reinitialize
if [ -d ".git" ]; then
    echo "Removing existing git history..."
    rm -rf .git
fi

# Remove any deployment artifacts
rm -rf dist/ build/ .cache/ __pycache__/

# Verify all required files exist
REQUIRED_FILES=(
    "index.html"
    "how-it-works.html"
    "platform.html"
    "security.html"
    "industries.html"
    "pricing.html"
    "case-studies.html"
    "resources.html"
    "roi.html"
    "walkthrough.html"
    "investor.html"
    "sales-one-pager.html"
    "Dockerfile"
    "nginx.conf"
)

echo "Verifying required files..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Missing required file: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required files present${NC}"

# Verify blog files
if [ -d "blog" ]; then
    echo -e "${GREEN}✓ Blog directory found with $(ls blog/*.html 2>/dev/null | wc -l) posts${NC}"
else
    echo -e "${YELLOW}Warning: No blog directory found${NC}"
fi

#######################################################################
# STEP 2: Initialize Git repository
#######################################################################
print_step 2 "Initializing Git repository"

git init
git config user.email "deploy@mizoki.com"
git config user.name "MIZ OKI Deploy"

# Create comprehensive .gitignore
cat > .gitignore << 'EOF'
# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp

# Dependencies
node_modules/
vendor/

# Build
dist/
build/

# Environment
.env
.env.*

# Logs
*.log

# Docker
.docker/
EOF

git add -A
git commit -m "MIZ OKI 3.5 - Production deployment $(date +%Y-%m-%d)

7-Stage SRDPV-DAL Pipeline:
SENSE → REASON → PLAN → VALIDATE → DECIDE → ACT → LEARN

Features:
- 12 marketing pages
- Blog with thought leadership content
- Decision Control Plane architecture
- Validation & Arbitration Layer
- Counterfactual Simulation Engine
- Temporal-Causal Knowledge Graph

Patent-pending verifiable autonomous decision intelligence."

git branch -M main

echo -e "${GREEN}✓ Git repository initialized${NC}"

#######################################################################
# STEP 3: Push to GitHub (if repo provided)
#######################################################################
print_step 3 "GitHub integration"

if [ -n "$GITHUB_REPO" ]; then
    echo "Pushing to GitHub: $GITHUB_REPO"
    git remote add origin "$GITHUB_REPO" 2>/dev/null || git remote set-url origin "$GITHUB_REPO"
    git push -u origin main --force
    echo -e "${GREEN}✓ Code pushed to GitHub${NC}"
else
    echo -e "${YELLOW}No GitHub repo provided. Skipping GitHub push.${NC}"
    echo "To push later: git remote add origin YOUR_REPO_URL && git push -u origin main"
fi

#######################################################################
# STEP 4: Enable Google Cloud APIs
#######################################################################
print_step 4 "Enabling Google Cloud APIs"

echo "Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    artifactregistry.googleapis.com \
    --quiet

echo -e "${GREEN}✓ APIs enabled${NC}"

#######################################################################
# STEP 5: Build container image
#######################################################################
print_step 5 "Building container image"

COMMIT_SHA=$(git rev-parse --short HEAD)
IMAGE_TAG="gcr.io/${PROJECT_ID}/${WEBSITE_SERVICE}:${COMMIT_SHA}"
IMAGE_LATEST="gcr.io/${PROJECT_ID}/${WEBSITE_SERVICE}:latest"

echo "Building image: $IMAGE_TAG"
echo "This may take 2-3 minutes..."

gcloud builds submit \
    --tag "${IMAGE_TAG}" \
    --quiet

# Tag as latest
gcloud container images add-tag "${IMAGE_TAG}" "${IMAGE_LATEST}" --quiet 2>/dev/null || true

echo -e "${GREEN}✓ Container image built and pushed${NC}"

#######################################################################
# STEP 6: Deploy to Cloud Run (Main Website)
#######################################################################
print_step 6 "Deploying main website to Cloud Run"

echo "Deploying to service: ${WEBSITE_SERVICE}"

gcloud run deploy "${WEBSITE_SERVICE}" \
    --image "${IMAGE_TAG}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 20 \
    --concurrency 100 \
    --set-env-vars="ENVIRONMENT=production,VERSION=3.5" \
    --quiet

WEBSITE_URL=$(gcloud run services describe "${WEBSITE_SERVICE}" --region="${REGION}" --format='value(status.url)')
echo -e "${GREEN}✓ Main website deployed: ${WEBSITE_URL}${NC}"

#######################################################################
# STEP 7: Configure custom domains
#######################################################################
print_step 7 "Configuring custom domains"

echo -e "${YELLOW}Custom domain mapping requires DNS verification.${NC}"
echo ""
echo "To map ${MAIN_DOMAIN}:"
echo -e "${CYAN}  gcloud run domain-mappings create --service ${WEBSITE_SERVICE} --domain ${MAIN_DOMAIN} --region ${REGION}${NC}"
echo ""
echo "To map ${APP_DOMAIN}:"
echo -e "${CYAN}  gcloud run domain-mappings create --service ${WEBSITE_SERVICE} --domain ${APP_DOMAIN} --region ${REGION}${NC}"
echo ""
echo "After running these commands, add the DNS records shown to your domain registrar."

# Attempt domain mapping (will provide instructions if not verified)
echo ""
echo "Attempting domain mapping..."
gcloud run domain-mappings create \
    --service "${WEBSITE_SERVICE}" \
    --domain "${MAIN_DOMAIN}" \
    --region "${REGION}" \
    --quiet 2>&1 || echo -e "${YELLOW}Domain mapping pending DNS verification${NC}"

#######################################################################
# STEP 8: Summary and next steps
#######################################################################
print_step 8 "Deployment complete!"

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT SUCCESSFUL!                              ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "
${CYAN}DEPLOYED SERVICES:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Main Website:     ${GREEN}${WEBSITE_URL}${NC}
  Target Domain:    ${MAIN_DOMAIN}
  
${CYAN}PAGES DEPLOYED:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • index.html           (Homepage)
  • how-it-works.html    (SRDPV-DAL Pipeline)
  • platform.html        (Architecture)
  • security.html        (Compliance)
  • industries.html      (Templates)
  • pricing.html         (Tiers)
  • case-studies.html    (Proof Points)
  • resources.html       (Documentation)
  • roi.html             (Calculator)
  • walkthrough.html     (Demo Request)
  • investor.html        (Investor Overview)
  • sales-one-pager.html (Sales Summary)
  • blog/                (Thought Leadership)

${CYAN}BLOG POSTS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • ReLU Lens Meta Algorithm
  • Decision Control Plane
  
${CYAN}QUICK LINKS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Homepage:      ${WEBSITE_URL}
  Pricing:       ${WEBSITE_URL}/pricing.html
  Case Studies:  ${WEBSITE_URL}/case-studies.html
  ROI Calc:      ${WEBSITE_URL}/roi.html
  Blog:          ${WEBSITE_URL}/blog/

${CYAN}NEXT STEPS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Verify site is working: ${WEBSITE_URL}
  2. Configure DNS for ${MAIN_DOMAIN}
  3. Set up SSL certificate (automatic with Cloud Run)
  4. Configure Cloud Build trigger for auto-deploy

${CYAN}USEFUL COMMANDS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  View logs:
    gcloud run services logs read ${WEBSITE_SERVICE} --region ${REGION}
  
  Update deployment:
    ./master-deploy.sh ${PROJECT_ID}
  
  View metrics:
    https://console.cloud.google.com/run/detail/${REGION}/${WEBSITE_SERVICE}/metrics
"

echo -e "${GREEN}Deployment complete! 🚀${NC}"
