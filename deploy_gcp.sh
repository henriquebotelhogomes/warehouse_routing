#!/usr/bin/env bash
set -e

# Deploy Automatizado NexusFleet AMR no Google Cloud Run (Always Free - $0/mês)
SERVICE_NAME="nexusfleet-amr"
REGION="us-central1"

echo "🚀 Iniciando deploy do NexusFleet AMR no Google Cloud Run..."

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 2 \
  --memory 512Mi \
  --cpu 1 \
  --port 8000

echo "✅ Deploy concluído com sucesso!"
