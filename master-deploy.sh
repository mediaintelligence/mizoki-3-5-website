#!/bin/bash
PROJECT_ID=$1
REPO_URL=$2

if [ -z "$PROJECT_ID" ] || [ -z "$REPO_URL" ]; then
    echo "Usage: $0 PROJECT_ID REPO_URL"
    exit 1
fi

# Ensure script exits on first error
set -e

echo "Setting Google Cloud Project to $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

echo "Running deployment script..."
./deploy.sh

echo "Pushing to GitHub..."
./github-push.sh "$REPO_URL"
