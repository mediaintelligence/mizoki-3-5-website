#!/bin/bash

#######################################################################
# MIZ OKI 3.5 Website - One-Click Deploy to Google Cloud Run
#######################################################################
#
# PREREQUISITES:
# 1. Google Cloud SDK (gcloud) installed
# 2. Docker installed (for local builds) OR Cloud Build enabled
# 3. A Google Cloud Project with billing enabled
#
# USAGE:
#   chmod +x deploy.sh
#   ./deploy.sh
#
#######################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         MIZ OKI 3.5 - One-Click Cloud Run Deployment          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
SERVICE_NAME="mizoki-website"
REGION="us-central1"
IMAGE_NAME="mizoki-website"

# Check for gcloud
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project or prompt for one
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
    echo -e "${YELLOW}No Google Cloud project configured.${NC}"
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

echo -e "${GREEN}✓ Using project: ${PROJECT_ID}${NC}"

# Authenticate if needed
echo -e "\n${CYAN}[1/6] Checking authentication...${NC}"
if ! gcloud auth print-access-token &> /dev/null; then
    echo "Authenticating with Google Cloud..."
    gcloud auth login
fi
echo -e "${GREEN}✓ Authenticated${NC}"

# Enable required APIs
echo -e "\n${CYAN}[2/6] Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com --quiet
echo -e "${GREEN}✓ APIs enabled${NC}"

# Initialize Git if not already
echo -e "\n${CYAN}[3/6] Initializing Git repository...${NC}"
if [ ! -d ".git" ]; then
    git init
    git add -A
    git commit -m "Initial commit: MIZ OKI 3.5 Website"
    echo -e "${GREEN}✓ Git repository initialized${NC}"
else
    git add -A
    git commit -m "Update: MIZ OKI 3.5 Website deployment" --allow-empty
    echo -e "${GREEN}✓ Git repository updated${NC}"
fi

# Get commit SHA for tagging
COMMIT_SHA=$(git rev-parse --short HEAD)
IMAGE_TAG="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${COMMIT_SHA}"
IMAGE_LATEST="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest"

# Build and deploy using Cloud Build
echo -e "\n${CYAN}[4/6] Building container with Cloud Build...${NC}"
echo "This may take 2-3 minutes..."

gcloud builds submit \
    --tag "${IMAGE_TAG}" \
    --quiet

# Also tag as latest
echo -e "\n${CYAN}[5/6] Tagging as latest...${NC}"
gcloud container images add-tag "${IMAGE_TAG}" "${IMAGE_LATEST}" --quiet
echo -e "${GREEN}✓ Image tagged${NC}"

# Deploy to Cloud Run
echo -e "\n${CYAN}[6/6] Deploying to Cloud Run...${NC}"
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_TAG}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80 \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')

echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT SUCCESSFUL!                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "Service URL: ${CYAN}${SERVICE_URL}${NC}"
echo ""
echo "Your MIZ OKI 3.5 website is now live!"
echo ""
echo "Quick Links:"
echo "  • Homepage:     ${SERVICE_URL}"
echo "  • Pricing:      ${SERVICE_URL}/pricing.html"
echo "  • Case Studies: ${SERVICE_URL}/case-studies.html"
echo "  • ROI Calc:     ${SERVICE_URL}/roi.html"
echo ""
echo -e "${YELLOW}To set up a custom domain:${NC}"
echo "  gcloud run domain-mappings create --service ${SERVICE_NAME} --domain YOUR_DOMAIN --region ${REGION}"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "  gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
