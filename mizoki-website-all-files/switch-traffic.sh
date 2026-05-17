#!/bin/bash

# Script to easily go back and forth between the new and old website revisions.

SERVICE_NAME="mizoki-website"
REGION="us-central1"

echo "Select which version of the site you want to route traffic to:"
echo "1) Old Version (Revision: mizoki-website-00032-g78)"
echo "2) New Version (Revision: mizoki-website-00033-pwz)"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
    echo "Routing 100% traffic to the OLD version..."
    gcloud run services update-traffic $SERVICE_NAME --to-revisions=mizoki-website-00032-g78=100 --region=$REGION
    echo "Done! The old version is now live."
elif [ "$choice" == "2" ]; then
    echo "Routing 100% traffic to the NEW version..."
    gcloud run services update-traffic $SERVICE_NAME --to-revisions=mizoki-website-00033-pwz=100 --region=$REGION
    echo "Done! The new version is now live."
else
    echo "Invalid choice. Exiting."
fi
