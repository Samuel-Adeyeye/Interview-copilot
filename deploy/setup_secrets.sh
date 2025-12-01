#!/bin/bash
# Setup Google Secret Manager secrets for Interview Copilot
# Usage: ./setup_secrets.sh [PROJECT_ID]

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}

echo "Setting up Secret Manager for project: $PROJECT_ID"

# Enable Secret Manager API
echo "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

# Create secrets (you'll need to add the actual values later)
echo "Creating secrets..."

# Google API Key
echo "Creating GOOGLE_API_KEY secret..."
echo -n "YOUR_GOOGLE_API_KEY_HERE" | gcloud secrets create GOOGLE_API_KEY \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# Brave API Key
echo "Creating BRAVE_API_KEY secret..."
echo -n "YOUR_BRAVE_API_KEY_HERE" | gcloud secrets create BRAVE_API_KEY \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# Judge0 API Key
echo "Creating JUDGE0_API_KEY secret..."
echo -n "YOUR_JUDGE0_API_KEY_HERE" | gcloud secrets create JUDGE0_API_KEY \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# Database URL for Staging
echo "Creating DATABASE_URL_STAGING secret..."
echo -n "postgresql://interview_app_staging:PASSWORD@/interview_copilot_staging?host=/cloudsql/PROJECT_ID:REGION:interview-copilot-db-staging" | gcloud secrets create DATABASE_URL_STAGING \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# Database URL for Production
echo "Creating DATABASE_URL_PROD secret..."
echo -n "postgresql://interview_app_prod:PASSWORD@/interview_copilot_prod?host=/cloudsql/PROJECT_ID:REGION:interview-copilot-db-prod" | gcloud secrets create DATABASE_URL_PROD \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

echo "✅ Secret Manager setup complete!"
echo ""
echo "⚠️  IMPORTANT: Update the secret values with your actual API keys:"
echo ""
echo "gcloud secrets versions add GOOGLE_API_KEY --data-file=- <<< 'your-actual-key'"
echo "gcloud secrets versions add BRAVE_API_KEY --data-file=- <<< 'your-actual-key'"
echo "gcloud secrets versions add JUDGE0_API_KEY --data-file=- <<< 'your-actual-key'"
echo "gcloud secrets versions add DATABASE_URL_STAGING --data-file=- <<< 'your-actual-connection-string'"
echo "gcloud secrets versions add DATABASE_URL_PROD --data-file=- <<< 'your-actual-connection-string'"
