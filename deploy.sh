#!/bin/bash

# Grammar Correction API - Production Deployment Script
# This script helps deploy the application to production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="grammar-correction"
DOCKER_REGISTRY="your-registry"  # UPDATE THIS
IMAGE_TAG="v1.0.0"  # UPDATE THIS
IMAGE_NAME="grammar-correction-api"

echo -e "${BLUE} Grammar Correction API - Production Deployment${NC}"
echo "=================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW} Checking prerequisites...${NC}"

if ! command_exists kubectl; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}❌ docker is not installed or not in PATH${NC}"
    exit 1
fi

echo -e "${GREEN} Prerequisites check passed${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}  .env file not found. Creating from template...${NC}"
    if [ -f "env.production.example" ]; then
        cp env.production.example .env
        echo -e "${YELLOW} Please edit .env file with your production values before continuing${NC}"
        echo -e "${YELLOW} Required: REDIS_PASSWORD, ALLOWED_ORIGINS, DOCKER_REGISTRY${NC}"
        read -p "Press Enter after updating .env file..."
    else
        echo -e "${RED} env.production.example not found${NC}"
        exit 1
    fi
fi

# Load environment variables
source .env

# Validate required environment variables
echo -e "${YELLOW} Validating environment variables...${NC}"

if [ -z "$REDIS_PASSWORD" ] || [ "$REDIS_PASSWORD" = "your_secure_redis_password_here_minimum_32_chars" ]; then
    echo -e "${RED} REDIS_PASSWORD must be set in .env file${NC}"
    exit 1
fi

if [ -z "$ALLOWED_ORIGINS" ] || [[ "$ALLOWED_ORIGINS" == *"yourdomain.com"* ]]; then
    echo -e "${RED} ALLOWED_ORIGINS must be set with your actual domains in .env file${NC}"
    exit 1
fi

echo -e "${GREEN} Environment variables validated${NC}"

# Build and push Docker image
echo -e "${YELLOW} Building and pushing Docker image...${NC}"

FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Build the image
docker build -t "${FULL_IMAGE_NAME}" .

# Push the image
docker push "${FULL_IMAGE_NAME}"

echo -e "${GREEN} Docker image built and pushed: ${FULL_IMAGE_NAME}${NC}"

# Update Kubernetes deployment with actual image
echo -e "${YELLOW} Updating Kubernetes deployment with actual image...${NC}"

# Update the deployment file with the actual image name
sed -i.bak "s|your-registry/grammar-correction-api:v1.0.0|${FULL_IMAGE_NAME}|g" kubernetes/04-deployment.yaml

echo -e "${GREEN} Kubernetes deployment updated${NC}"

# Create namespace if it doesn't exist
echo -e "${YELLOW} Creating namespace...${NC}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
echo -e "${YELLOW} Deploying to Kubernetes...${NC}"

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

echo -e "${GREEN} Kubernetes resources deployed${NC}"

# Wait for deployment to be ready
echo -e "${YELLOW} Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/grammar-api -n "${NAMESPACE}"

# Get service information
echo -e "${GREEN} Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE} Service Information:${NC}"
kubectl get services -n "${NAMESPACE}"
echo ""
echo -e "${BLUE} Pod Status:${NC}"
kubectl get pods -n "${NAMESPACE}"
echo ""

# Get the service URL
SERVICE_IP=$(kubectl get service grammar-api -n "${NAMESPACE}" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
SERVICE_PORT=$(kubectl get service grammar-api -n "${NAMESPACE}" -o jsonpath='{.spec.ports[0].port}')

if [ -n "$SERVICE_IP" ]; then
    echo -e "${GREEN} API URL: http://${SERVICE_IP}:${SERVICE_PORT}${NC}"
    echo -e "${GREEN} API Docs: http://${SERVICE_IP}:${SERVICE_PORT}/docs${NC}"
    echo -e "${GREEN} Health Check: http://${SERVICE_IP}:${SERVICE_PORT}/health${NC}"
else
    echo -e "${YELLOW}  Service IP not available. Check with: kubectl get service grammar-api -n ${NAMESPACE}${NC}"
fi

echo ""
echo -e "${BLUE} Useful Commands:${NC}"
echo "  View logs: kubectl logs -f deployment/grammar-api -n ${NAMESPACE}"
echo "  Scale API: kubectl scale deployment grammar-api --replicas=3 -n ${NAMESPACE}"
echo "  Scale Worker: kubectl scale deployment grammar-worker --replicas=2 -n ${NAMESPACE}"
echo "  Delete deployment: kubectl delete namespace ${NAMESPACE}"

echo ""
echo -e "${GREEN} Production deployment completed!${NC}"
