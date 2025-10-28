# Grammar Correction API - Production Deployment Script (Windows PowerShell)
# This script helps deploy the application to production

param(
    [string]$Environment = "production",
    [string]$DockerRegistry = "your-registry",  # UPDATE THIS
    [string]$ImageTag = "v1.0.0",  # UPDATE THIS
    [string]$ImageName = "grammar-correction-api"
)

# Configuration
$Namespace = "grammar-correction"
$FullImageName = "$DockerRegistry/$ImageName`:$ImageTag"

Write-Host "🚀 Grammar Correction API - Production Deployment" -ForegroundColor Blue
Write-Host "=================================================="

# Function to check if command exists
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-CommandExists "kubectl")) {
    Write-Host "❌ kubectl is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

if (-not (Test-CommandExists "docker")) {
    Write-Host "❌ docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path "env.production.example") {
        Copy-Item "env.production.example" ".env"
        Write-Host "📝 Please edit .env file with your production values before continuing" -ForegroundColor Yellow
        Write-Host "   Required: REDIS_PASSWORD, ALLOWED_ORIGINS, DOCKER_REGISTRY" -ForegroundColor Yellow
        Read-Host "Press Enter after updating .env file"
    } else {
        Write-Host "❌ env.production.example not found" -ForegroundColor Red
        exit 1
    }
}

# Load environment variables from .env file
Write-Host "🔍 Loading environment variables..." -ForegroundColor Yellow
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Validate required environment variables
Write-Host "🔍 Validating environment variables..." -ForegroundColor Yellow

$RedisPassword = [Environment]::GetEnvironmentVariable("REDIS_PASSWORD")
$AllowedOrigins = [Environment]::GetEnvironmentVariable("ALLOWED_ORIGINS")

if ([string]::IsNullOrEmpty($RedisPassword) -or $RedisPassword -eq "your_secure_redis_password_here_minimum_32_chars") {
    Write-Host "❌ REDIS_PASSWORD must be set in .env file" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($AllowedOrigins) -or $AllowedOrigins -like "*yourdomain.com*") {
    Write-Host "❌ ALLOWED_ORIGINS must be set with your actual domains in .env file" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment variables validated" -ForegroundColor Green

# Build and push Docker image
Write-Host "🐳 Building and pushing Docker image..." -ForegroundColor Yellow

# Build the image
docker build -t $FullImageName .

# Push the image
docker push $FullImageName

Write-Host "✅ Docker image built and pushed: $FullImageName" -ForegroundColor Green

# Update Kubernetes deployment with actual image
Write-Host "📝 Updating Kubernetes deployment with actual image..." -ForegroundColor Yellow

# Update the deployment file with the actual image name
$DeploymentFile = "kubernetes/04-deployment.yaml"
$Content = Get-Content $DeploymentFile
$Content = $Content -replace "your-registry/grammar-correction-api:v1.0.0", $FullImageName
$Content | Set-Content $DeploymentFile

Write-Host "✅ Kubernetes deployment updated" -ForegroundColor Green

# Create namespace if it doesn't exist
Write-Host "📦 Creating namespace..." -ForegroundColor Yellow
kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
Write-Host "🚀 Deploying to Kubernetes..." -ForegroundColor Yellow

# Apply secrets first
kubectl apply -f kubernetes/02-redis-secret.yaml

# Apply other resources
kubectl apply -f kubernetes/01-namespace.yaml
kubectl apply -f kubernetes/02-redis.yaml
kubectl apply -f kubernetes/03-configmap.yaml
kubectl apply -f kubernetes/04-deployment.yaml
kubectl apply -f kubernetes/05-service.yaml
kubectl apply -f kubernetes/06-hpa.yaml
kubectl apply -f kubernetes/07-worker.yaml
kubectl apply -f kubernetes/08-flower.yaml

Write-Host "✅ Kubernetes resources deployed" -ForegroundColor Green

# Wait for deployment to be ready
Write-Host "⏳ Waiting for deployment to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment/grammar-api -n $Namespace

# Get service information
Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Service Information:" -ForegroundColor Blue
kubectl get services -n $Namespace
Write-Host ""
Write-Host "📈 Pod Status:" -ForegroundColor Blue
kubectl get pods -n $Namespace
Write-Host ""

# Get the service URL
$ServiceInfo = kubectl get service grammar-api -n $Namespace -o json | ConvertFrom-Json
$ServiceIP = $ServiceInfo.status.loadBalancer.ingress[0].ip
$ServicePort = $ServiceInfo.spec.ports[0].port

if ($ServiceIP) {
    Write-Host "🌐 API URL: http://$ServiceIP`:$ServicePort" -ForegroundColor Green
    Write-Host "📚 API Docs: http://$ServiceIP`:$ServicePort/docs" -ForegroundColor Green
    Write-Host "🔍 Health Check: http://$ServiceIP`:$ServicePort/health" -ForegroundColor Green
} else {
    Write-Host "⚠️  Service IP not available. Check with: kubectl get service grammar-api -n $Namespace" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Blue
Write-Host "  View logs: kubectl logs -f deployment/grammar-api -n $Namespace"
Write-Host "  Scale API: kubectl scale deployment grammar-api --replicas=3 -n $Namespace"
Write-Host "  Scale Worker: kubectl scale deployment grammar-worker --replicas=2 -n $Namespace"
Write-Host "  Delete deployment: kubectl delete namespace $Namespace"

Write-Host ""
Write-Host "✅ Production deployment completed!" -ForegroundColor Green
