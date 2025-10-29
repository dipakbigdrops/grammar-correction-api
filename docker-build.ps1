# Docker Build Script for Grammar Correction API (PowerShell)

Write-Host "🐳 Building Grammar Correction API Docker Image..." -ForegroundColor Cyan
Write-Host ""

# Build the image
docker build -t grammar-correction-api:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Docker image built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run the container:" -ForegroundColor Yellow
    Write-Host "  docker run -d --name grammar-api -p 8000:8000 grammar-correction-api:latest"
    Write-Host ""
    Write-Host "Or use Docker Compose:" -ForegroundColor Yellow
    Write-Host "  docker-compose up -d"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Build failed! Check the error messages above." -ForegroundColor Red
    exit 1
}

