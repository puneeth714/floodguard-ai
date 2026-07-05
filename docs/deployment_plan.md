# Google Cloud Run Deployment Plan: FloodGuard AI

This document provides the step-by-step plan to containerize and deploy the **FloodGuard AI** platform to Google Cloud Run, serving both frontends and the FastAPI backend on a single server port.

---

## 📋 Pre-requisites & Assumptions
1.  **gcloud SDK**: You have `gcloud` installed locally and authenticated (`gcloud auth login`).
2.  **Docker**: Local Docker daemon is running (if building locally), or we can use **Google Cloud Build** (which does not require local Docker).
3.  **Active GCP Project**: Billing is enabled, and API services for Cloud Run, Artifact Registry, BigQuery, and Vertex AI are enabled.

---

## 🛠️ Step 1: Create the Dockerfile
We will write a multi-stage `Dockerfile` in the project root. This Dockerfile:
1.  Uses a Node image to build both frontend dist folders.
2.  Uses a Python image to set up the FastAPI server.
3.  Copies the built assets and runs Uvicorn.

```dockerfile
# --- Stage 1: Build Frontends ---
FROM node:20-alpine AS builder-resident
WORKDIR /frontend-resident
COPY frontend-resident/package*.json ./
RUN npm install
COPY frontend-resident/ ./
RUN npm run build

FROM node:20-alpine AS builder-official
WORKDIR /frontend-official
COPY frontend-official/package*.json ./
RUN npm install
COPY frontend-official/ ./
RUN npm run build

# --- Stage 2: Serve Backend + Static Assets ---
FROM python:3.12-slim
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app
COPY backend/app ./backend/app

# Copy built frontend assets matching main.py resolution paths
COPY --from=builder-resident /frontend-resident/dist ./frontend-resident/dist
COPY --from=builder-official /frontend-official/dist ./frontend-official/dist

# Set environment defaults
ENV PORT=8080
ENV PYTHONPATH=/workspace/backend

# Run server
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 🌐 Step 2: Set Up Artifact Registry
Run the following commands to create a Docker repository in Google Artifact Registry:
```bash
# Set GCP Project ID
gcloud config set project [YOUR_PROJECT_ID]

# Create repository in your preferred region (e.g. us-central1)
gcloud artifacts repositories create floodguard-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for FloodGuard AI"
```

---

## 🏗️ Step 3: Build & Push Container (Cloud Build)
We can use **Google Cloud Build** to build and push the container image directly in the cloud. This avoids needing Docker installed locally:
```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/[YOUR_PROJECT_ID]/floodguard-repo/floodguard-app:latest .
```

---

## 🚀 Step 4: Deploy to Google Cloud Run
Deploy the container to Cloud Run, authorizing unauthenticated access so the public can access the app:
```bash
gcloud run deploy floodguard-service \
    --image=us-central1-docker.pkg.dev/[YOUR_PROJECT_ID]/floodguard-repo/floodguard-app:latest \
    --region=us-central1 \
    --allow-unauthenticated \
    --port=8080 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=[YOUR_PROJECT_ID],ENVIRONMENT_MODE=production"
```

---

## 🔐 Step 5: IAM Role Bindings (Security)
Instead of embedding the `floodguard-sa-key.json` file inside the Docker container, we will bind the default Cloud Run Service Account (e.g., `[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`) with the required roles.

Run these commands to authorize Cloud Run to query BigQuery and Vertex AI directly:
```bash
# Allow Cloud Run to use BigQuery
gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
    --member="serviceAccount:[PROJECT_NUMBER]-compute@developer.gserviceaccount.com" \
    --role="roles/bigquery.admin"

# Allow Cloud Run to use Vertex AI Gemini Models
gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
    --member="serviceAccount:[PROJECT_NUMBER]-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```
