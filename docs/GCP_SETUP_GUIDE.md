# Google Cloud Platform Setup Guide for Interview Copilot

This guide details the step-by-step process to set up your Google Cloud environment for the Interview Copilot CI/CD pipeline.

## 1. Prerequisites

*   A Google Cloud Project
*   Billing enabled for the project
*   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed locally (optional, but recommended for command-line setup)

## 2. Enable Required APIs

You need to enable the following APIs for the pipeline to build images, store them, and deploy to Cloud Run.

Run the following command in your terminal (or search for these in the Google Cloud Console "APIs & Services" library):

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com
```

*   **Cloud Build API**: For running the CI/CD pipeline.
*   **Cloud Run API**: For hosting the API and UI services.
*   **Container Registry API**: For storing Docker images (gcr.io).
*   **Secret Manager API**: For securely managing API keys and database credentials.
*   **Cloud SQL Admin API**: For managing the PostgreSQL database.

## 3. Configure Secrets in Secret Manager

The pipeline uses Secret Manager to inject sensitive environment variables. You must create the following secrets in your Google Cloud Project.

### Required Secrets

| Secret Name | Value Description |
| :--- | :--- |
| `GOOGLE_API_KEY` | Your Google Gemini API Key |
| `BRAVE_API_KEY` | Your Brave Search API Key (if using Brave) |
| `JUDGE0_API_KEY` | Your Judge0 API Key (if using Judge0) |
| `DATABASE_URL_STAGING` | Connection string for Staging DB (e.g., `postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance`) |
| `DATABASE_URL_PROD` | Connection string for Production DB |

### How to Create Secrets (Console)
1.  Go to **Security** > **Secret Manager** in the Google Cloud Console.
2.  Click **Create Secret**.
3.  Name: Enter the name from the table above (e.g., `GOOGLE_API_KEY`).
4.  Secret value: Paste your API key.
5.  Click **Create Secret**.
6.  Repeat for all required secrets.

### How to Create Secrets (CLI)
```bash
# Example for GOOGLE_API_KEY
echo -n "your-api-key-here" | gcloud secrets create GOOGLE_API_KEY --data-file=-
```

## 4. Service Account Permissions

The **Cloud Build Service Account** needs specific permissions to deploy to Cloud Run and access secrets.

1.  Go to **IAM & Admin** > **IAM**.
2.  Find the member ending in `@cloudbuild.gserviceaccount.com`.
3.  Edit the principal and ensure it has the following roles:
    *   **Cloud Build Service Account** (Default)
    *   **Cloud Run Admin** (To deploy services)
    *   **Service Account User** (To act as the runtime service account)
    *   **Secret Manager Secret Accessor** (To read the secrets during deployment)
    *   **Cloud SQL Client** (To connect to the database)

## 5. Cloud SQL Setup (If using Cloud SQL)

If you are using Cloud SQL for the database:

1.  Create a PostgreSQL instance in Cloud SQL.
2.  Create a database (e.g., `interview-copilot-db-staging`).
3.  Create a user and password.
4.  **Important**: Update the `substitutions` section in your `cloudbuild.yaml` and `cloudbuild-staging.yaml` files with your actual connection name:
    ```yaml
    _CLOUD_SQL_INSTANCE_STAGING: 'YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME'
    ```

## 6. Set Up Cloud Build Triggers

1.  Go to **Cloud Build** > **Triggers**.
2.  Click **Create Trigger**.
3.  **Name**: `deploy-staging` (or similar).
4.  **Event**: Push to a branch.
5.  **Source**: Connect your GitHub repository and select the `staging` branch (or `main` if deploying directly).
6.  **Configuration**: Select **Cloud Build configuration file (yaml or json)**.
7.  **Location**: `cloudbuild-staging.yaml` (for staging) or `cloudbuild.yaml` (for prod).
8.  Click **Create**.

Now, whenever you push to the configured branch, Cloud Build will automatically build your containers, run tests, and deploy to Cloud Run!
