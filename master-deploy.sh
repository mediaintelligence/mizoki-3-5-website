#!/bin/bash

#######################################################################
# MIZ OKI 3.5 - MASTER DEPLOYMENT SCRIPT
#######################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

PROJECT_ID="${1:-}"
GITHUB_REPO="${2:-}"
REGION="${REGION:-us-central1}"
WEBSITE_SERVICE="${WEBSITE_SERVICE:-mizoki-website}"
MAIN_DOMAIN="${MAIN_DOMAIN:-mizoki3.com}"
APP_DOMAIN="${APP_DOMAIN:-mizoki.mizoki3.com}"

print_header() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║           MASTER DEPLOYMENT SCRIPT - MIZ OKI 3.5                     ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[$1/$2]${NC} $3"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_header

TOTAL_STEPS=5

print_step 1 "${TOTAL_STEPS}" "Checking prerequisites"
for tool in gcloud git; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo -e "${RED}Error: ${tool} is required but not installed.${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ Required tools found${NC}"

if [ -z "${PROJECT_ID}" ]; then
    PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
fi
if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
    echo -e "${YELLOW}No Google Cloud project configured.${NC}"
    read -r -p "Enter your Google Cloud Project ID: " PROJECT_ID
fi
gcloud config set project "${PROJECT_ID}" >/dev/null
echo -e "${GREEN}✓ Using project: ${PROJECT_ID}${NC}"

print_step 2 "${TOTAL_STEPS}" "Validating repository contents"
REQUIRED_FILES=(
    "app.py"
    "requirements.txt"
    "Dockerfile"
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
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${file}" ]; then
        echo -e "${RED}Error: Missing required file: ${file}${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ Repository contents validated${NC}"

if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}Warning: working tree has uncommitted changes. Deployment will use local contents as-is.${NC}"
fi

if [ -n "${GITHUB_REPO}" ]; then
    print_step 3 "${TOTAL_STEPS}" "Synchronizing GitHub remote"
    if git remote get-url origin >/dev/null 2>&1; then
        git remote set-url origin "${GITHUB_REPO}"
    else
        git remote add origin "${GITHUB_REPO}"
    fi
    CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    git push -u origin "${CURRENT_BRANCH}"
    echo -e "${GREEN}✓ GitHub synchronized${NC}"
else
    print_step 3 "${TOTAL_STEPS}" "Skipping GitHub synchronization"
    echo -e "${YELLOW}No GitHub repository supplied. Skipping push.${NC}"
fi

print_step 4 "${TOTAL_STEPS}" "Deploying website to Cloud Run"
SERVICE_NAME="${WEBSITE_SERVICE}" REGION="${REGION}" ./deploy.sh

print_step 5 "${TOTAL_STEPS}" "Post-deploy summary"
WEBSITE_URL="$(gcloud run services describe "${WEBSITE_SERVICE}" --region="${REGION}" --format='value(status.url)')"
echo -e "${GREEN}✓ Website deployed: ${WEBSITE_URL}${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify site is working: ${WEBSITE_URL}"
echo "  2. Map ${MAIN_DOMAIN}: gcloud run domain-mappings create --service ${WEBSITE_SERVICE} --domain ${MAIN_DOMAIN} --region ${REGION}"
echo "  3. Map ${APP_DOMAIN}: gcloud run domain-mappings create --service ${WEBSITE_SERVICE} --domain ${APP_DOMAIN} --region ${REGION}"
echo "  4. Review logs: gcloud run services logs read ${WEBSITE_SERVICE} --region ${REGION}"
