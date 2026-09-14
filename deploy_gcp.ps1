# Script de Deploy para o Google Cloud Run (Custo R$ 0,00 / Mês - Always Free Tier)
# Região: us-central1 (incluída no Always Free)
# Min-instances: 0 (Scale-to-Zero automático)

$SERVICE_NAME = "nexusfleet-amr"
$REGION = "us-central1"

Write-Host "🚀 Iniciando deploy do NexusFleet AMR no Google Cloud Run..." -ForegroundColor Cyan

gcloud run deploy $SERVICE_NAME `
  --source . `
  --region $REGION `
  --allow-unauthenticated `
  --min-instances 0 `
  --max-instances 2 `
  --memory 512Mi `
  --cpu 1 `
  --port 8000

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deploy concluído com sucesso!" -ForegroundColor Green
    Write-Host "Consulte a URL gerada acima para acessar seu Digital Twin em produção." -ForegroundColor Cyan
} else {
    Write-Host "❌ Falha no deploy. Verifique se o gcloud CLI está autenticado." -ForegroundColor Red
}
