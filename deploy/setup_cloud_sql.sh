#!/bin/bash
# Setup Cloud SQL PostgreSQL instances for Interview Copilot
# Usage: ./setup_cloud_sql.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-us-central1}

echo "Setting up Cloud SQL for project: $PROJECT_ID in region: $REGION"

# Create Staging Database Instance
echo "Creating staging database instance..."
gcloud sql instances create interview-copilot-db-staging \
    --project=$PROJECT_ID \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --availability-type=zonal \
    --enable-bin-log=false

# Create Production Database Instance
echo "Creating production database instance..."
gcloud sql instances create interview-copilot-db-prod \
    --project=$PROJECT_ID \
    --database-version=POSTGRES_15 \
    --tier=db-n1-standard-1 \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=20GB \
    --storage-auto-increase \
    --backup-start-time=02:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=03 \
    --availability-type=regional \
    --enable-bin-log=true

# Create databases
echo "Creating databases..."
gcloud sql databases create interview_copilot_staging \
    --instance=interview-copilot-db-staging \
    --project=$PROJECT_ID

gcloud sql databases create interview_copilot_prod \
    --instance=interview-copilot-db-prod \
    --project=$PROJECT_ID

# Create database users
echo "Creating database users..."
gcloud sql users create interview_app_staging \
    --instance=interview-copilot-db-staging \
    --password=$(openssl rand -base64 32) \
    --project=$PROJECT_ID

gcloud sql users create interview_app_prod \
    --instance=interview-copilot-db-prod \
    --password=$(openssl rand -base64 32) \
    --project=$PROJECT_ID

echo "✅ Cloud SQL setup complete!"
echo ""
echo "Staging Instance: interview-copilot-db-staging"
echo "Production Instance: interview-copilot-db-prod"
echo ""
echo "Next steps:"
echo "1. Note the connection names for each instance"
echo "2. Update the DATABASE_URL secrets in Secret Manager"
echo "3. Grant Cloud Run service account access to Cloud SQL"
