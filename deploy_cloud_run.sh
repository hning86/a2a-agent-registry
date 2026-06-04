#!/bin/bash

# Exit on error
set -e

echo "============================================="
echo "Starting Cloud Run Deployment for A2A Sandbox"
echo "============================================="

# Detect project configuration
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
  echo "Error: No active Google Cloud project detected."
  echo "Please set one first using: gcloud config set project <PROJECT_ID>"
  exit 1
fi

REGION="us-central1"
REPO_NAME="a2a-playground"
SERVICE_NAME="a2a-web-ui"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/web-ui:latest"

echo "Using GCP Project: $PROJECT_ID"
echo "Using GCP Region:  $REGION"
echo "Image destination: $IMAGE_TAG"

# Enable required GCP APIs
echo "Enabling services (artifactregistry, cloudbuild, run)..."
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com

# Create Artifact Registry Repository if not exists
echo "Checking Artifact Registry Repository..."
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null; then
  echo "Creating Artifact Registry repository '$REPO_NAME'..."
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repository for A2A Sandbox Playground Web UI"
else
  echo "Artifact Registry repository already exists."
fi

# Submit Build to Cloud Build
echo "Submitting build to Google Cloud Build..."
gcloud builds submit --tag "$IMAGE_TAG" .

# Deploy to Cloud Run
echo "Deploying container to Google Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_TAG" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --set-env-vars GOOGLE_CLOUD_PROJECT="${PROJECT_ID}",GOOGLE_CLOUD_LOCATION="global",GOOGLE_GENAI_USE_VERTEXAI="TRUE"

echo "============================================="
echo "Deployment Completed Successfully!"
echo "============================================="
