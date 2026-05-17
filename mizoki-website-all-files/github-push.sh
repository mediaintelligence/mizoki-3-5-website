#!/bin/bash

#######################################################################
# MIZ OKI 3.5 Website - Push to GitHub
#######################################################################
#
# USAGE:
#   chmod +x github-push.sh
#   ./github-push.sh YOUR_GITHUB_REPO_URL
#
# EXAMPLE:
#   ./github-push.sh https://github.com/yourusername/mizoki-website.git
#   ./github-push.sh git@github.com:yourusername/mizoki-website.git
#
#######################################################################

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           MIZ OKI 3.5 - Push to GitHub                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for repo URL argument
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <github-repo-url>${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 https://github.com/yourusername/mizoki-website.git"
    echo "  $0 git@github.com:yourusername/mizoki-website.git"
    echo ""
    echo -e "${CYAN}To create a new repo:${NC}"
    echo "  1. Go to https://github.com/new"
    echo "  2. Name it 'mizoki-website'"
    echo "  3. Don't initialize with README (we have one)"
    echo "  4. Run this script with the new repo URL"
    exit 1
fi

REPO_URL="$1"

echo -e "${GREEN}✓ Repository URL: ${REPO_URL}${NC}"

# Add remote origin
echo -e "\n${CYAN}[1/3] Adding remote origin...${NC}"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
echo -e "${GREEN}✓ Remote added${NC}"

# Push to GitHub
echo -e "\n${CYAN}[2/3] Pushing to GitHub...${NC}"
git push -u origin main --force
echo -e "${GREEN}✓ Code pushed${NC}"

# Get the web URL
WEB_URL=$(echo "$REPO_URL" | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/\.git$//')

echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    PUSH SUCCESSFUL!                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "Repository: ${CYAN}${WEB_URL}${NC}"
echo ""
echo "Next steps:"
echo "  1. Run ./deploy.sh to deploy to Google Cloud Run"
echo "  2. Or set up Cloud Build trigger for automatic deployments"
echo ""
echo -e "${YELLOW}To set up auto-deploy from GitHub:${NC}"
echo "  gcloud builds triggers create github \\"
echo "    --repo-name=mizoki-website \\"
echo "    --repo-owner=YOUR_GITHUB_USERNAME \\"
echo "    --branch-pattern='^main$' \\"
echo "    --build-config=cloudbuild.yaml"
echo ""
