# Interview Copilot - Deployment Guide

## Overview

This guide covers deploying Interview Copilot to Google Cloud Run with staging and production environments.

## Prerequisites

### Required Tools
- Google Cloud SDK (`gcloud`)
- Docker
- Git

### Google Cloud Setup
1. **Create GCP Project**:
   ```bash
   gcloud projects create YOUR_PROJECT_ID
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Billing**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Enable billing for your project

3. **Enable Required APIs**:
   ```bash
   gcloud services enable \
       run.googleapis.com \
       cloudbuild.googleapis.com \
       sql-component.googleapis.com \
       sqladmin.googleapis.com \
       secretmanager.googleapis.com \
       containerregistry.googleapis.com
   ```

4. **Set IAM Permissions**:
   ```bash
   # Grant Cloud Build service account necessary permissions
   PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
       --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
       --role="roles/iam.serviceAccountUser"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
       --role="roles/cloudsql.client"
   ```

## Initial Setup

### 1. Setup Cloud SQL

Run the Cloud SQL setup script:

```bash
cd deploy
chmod +x setup_cloud_sql.sh
./setup_cloud_sql.sh YOUR_PROJECT_ID us-central1
```

This creates:
- Staging database instance (db-f1-micro)
- Production database instance (db-n1-standard-1)
- Databases and users for each environment

### 2. Setup Secret Manager

Run the Secret Manager setup script:

```bash
chmod +x setup_secrets.sh
./setup_secrets.sh YOUR_PROJECT_ID
```

Then update the secrets with your actual values:

```bash
# Update API keys
echo -n "your-actual-google-api-key" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-
echo -n "your-actual-brave-api-key" | gcloud secrets versions add BRAVE_API_KEY --data-file=-
echo -n "your-actual-judge0-api-key" | gcloud secrets versions add JUDGE0_API_KEY --data-file=-

# Update database URLs (get connection names from Cloud SQL)
STAGING_CONN=$(gcloud sql instances describe interview-copilot-db-staging --format="value(connectionName)")
PROD_CONN=$(gcloud sql instances describe interview-copilot-db-prod --format="value(connectionName)")

echo -n "postgresql://interview_app_staging:PASSWORD@/interview_copilot_staging?host=/cloudsql/$STAGING_CONN" | \
    gcloud secrets versions add DATABASE_URL_STAGING --data-file=-

echo -n "postgresql://interview_app_prod:PASSWORD@/interview_copilot_prod?host=/cloudsql/$PROD_CONN" | \
    gcloud secrets versions add DATABASE_URL_PROD --data-file=-
```

### 3. Configure Cloud Build Triggers

#### Production Trigger (main branch)
```bash
gcloud builds triggers create github \
    --name="interview-copilot-production" \
    --repo-name="YOUR_REPO_NAME" \
    --repo-owner="YOUR_GITHUB_USERNAME" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml"
```

#### Staging Trigger (develop branch)
```bash
gcloud builds triggers create github \
    --name="interview-copilot-staging" \
    --repo-name="YOUR_REPO_NAME" \
    --repo-owner="YOUR_GITHUB_USERNAME" \
    --branch-pattern="^develop$" \
    --build-config="cloudbuild-staging.yaml"
```

### 4. Update Cloud Build Configuration

Edit `cloudbuild.yaml` and `cloudbuild-staging.yaml`:

1. Replace `_CLOUD_RUN_SUFFIX` with your actual Cloud Run URL suffix
2. Update `_CLOUD_SQL_INSTANCE_PROD` and `_CLOUD_SQL_INSTANCE_STAGING` with your instance connection names

## Deployment

### Staging Deployment

1. Create or switch to `develop` branch:
   ```bash
   git checkout -b develop
   ```

2. Push to trigger deployment:
   ```bash
   git push origin develop
   ```

3. Monitor deployment:
   ```bash
   gcloud builds list --limit=5
   gcloud builds log BUILD_ID
   ```

4. Verify deployment:
   ```bash
   # Get staging URLs
   gcloud run services describe interview-copilot-api-staging --region=us-central1 --format="value(status.url)"
   gcloud run services describe interview-copilot-ui-staging --region=us-central1 --format="value(status.url)"
   ```

### Production Deployment

1. Merge to `main` branch:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

2. Monitor deployment (same as staging)

3. Verify production deployment

## Post-Deployment

### Setup Monitoring

1. **Create Uptime Checks**:
   ```bash
   gcloud monitoring uptime create interview-copilot-api-prod \
       --resource-type=uptime-url \
       --host=YOUR_API_URL \
       --path=/health
   ```

2. **Setup Alerts**:
   - Go to Cloud Console > Monitoring > Alerting
   - Create alerts for:
     - High error rates
     - High latency
     - Low availability

### Database Migrations

Run migrations after deployment:

```bash
# Connect to Cloud SQL
gcloud sql connect interview-copilot-db-prod --user=interview_app_prod

# Run migrations (if using Alembic)
alembic upgrade head
```

## Rollback

If deployment fails or issues are detected:

```bash
# List revisions
gcloud run revisions list --service=interview-copilot-api-prod --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic interview-copilot-api-prod \
    --to-revisions=PREVIOUS_REVISION=100 \
    --region=us-central1
```

## Troubleshooting

### Build Failures

1. Check Cloud Build logs:
   ```bash
   gcloud builds log BUILD_ID
   ```

2. Common issues:
   - Missing secrets: Verify Secret Manager setup
   - Permission errors: Check IAM roles
   - Docker build errors: Test locally first

### Runtime Errors

1. Check Cloud Run logs:
   ```bash
   gcloud run services logs read interview-copilot-api-prod --region=us-central1
   ```

2. Common issues:
   - Database connection: Verify Cloud SQL connection and secrets
   - API key errors: Check Secret Manager values
   - Memory/CPU limits: Adjust in cloudbuild.yaml

### Database Issues

1. Check Cloud SQL status:
   ```bash
   gcloud sql instances describe interview-copilot-db-prod
   ```

2. Test connection:
   ```bash
   gcloud sql connect interview-copilot-db-prod --user=interview_app_prod
   ```

## Cost Optimization

### Staging Environment
- Use `db-f1-micro` for Cloud SQL
- Set `min-instances=0` for Cloud Run (scales to zero)
- Consider pausing during off-hours

### Production Environment
- Monitor usage and adjust instance sizes
- Use committed use discounts for predictable workloads
- Setup budget alerts

## Security Best Practices

1. **Secrets**: Never commit secrets to Git
2. **IAM**: Use least privilege principle
3. **Network**: Consider VPC for production
4. **Backups**: Verify Cloud SQL backups are running
5. **Updates**: Keep dependencies updated

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
