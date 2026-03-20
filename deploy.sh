#!/bin/bash

#######################################################################
# MIZ OKI 3.5 Website - One-Click Deploy to Google Cloud Run
#######################################################################

set -euo pipefail

# Bypass gcloud auth config permission issues
cp -a ~/.config/gcloud /tmp/gcloud || true
export CLOUDSDK_CONFIG=/tmp/gcloud

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         MIZ OKI 3.5 - One-Click Cloud Run Deployment          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

SERVICE_NAME="${SERVICE_NAME:-mizoki-website}"
REGION="${REGION:-us-central1}"
IMAGE_NAME="${IMAGE_NAME:-mizoki-website}"

if ! command -v gcloud >/dev/null 2>&1; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
    echo -e "${YELLOW}No Google Cloud project configured.${NC}"
    read -r -p "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project "${PROJECT_ID}"
fi

echo -e "${GREEN}✓ Using project: ${PROJECT_ID}${NC}"

echo -e "\n${CYAN}[1/5] Checking authentication...${NC}"
if ! gcloud auth print-access-token >/dev/null 2>&1; then
    echo "Authenticating with Google Cloud..."
    gcloud auth login
fi
echo -e "${GREEN}✓ Authenticated${NC}"

echo -e "\n${CYAN}[2/5] Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com --quiet
echo -e "${GREEN}✓ APIs enabled${NC}"

echo -e "\n${CYAN}[3/5] Determining source version...${NC}"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    SOURCE_VERSION="$(git rev-parse --short HEAD)"
else
    SOURCE_VERSION="$(date +%Y%m%d%H%M%S)"
fi
IMAGE_TAG="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${SOURCE_VERSION}"
IMAGE_LATEST="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest"
echo -e "${GREEN}✓ Using image tag: ${IMAGE_TAG}${NC}"

echo -e "\n${CYAN}[4/5] Building container with Cloud Build...${NC}"
echo "This may take 2-3 minutes..."
gcloud builds submit --tag "${IMAGE_TAG}" --quiet

echo -e "\n${CYAN}[5/5] Deploying to Cloud Run...${NC}"
gcloud container images add-tag "${IMAGE_TAG}" "${IMAGE_LATEST}" --quiet || true
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

SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')"

echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT SUCCESSFUL!                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "Service URL: ${CYAN}${SERVICE_URL}${NC}"
echo ""
echo "Your MIZ OKI 3.5 website is now live."
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
