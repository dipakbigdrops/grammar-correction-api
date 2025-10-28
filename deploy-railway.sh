#!/bin/bash

# Railway.app Deployment Script for Grammar Correction API
# This script prepares and deploys the application to Railway

set -e

echo "🚀 Starting Railway.app deployment process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Railway CLI is installed
check_railway_cli() {
    print_status "Checking Railway CLI installation..."
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI is not installed!"
        echo "Please install it from: https://docs.railway.app/develop/cli"
        echo "Or run: npm install -g @railway/cli"
        exit 1
    fi
    print_success "Railway CLI is installed"
}

# Check if Git LFS is installed
check_git_lfs() {
    print_status "Checking Git LFS installation..."
    if ! command -v git-lfs &> /dev/null; then
        print_error "Git LFS is not installed!"
        echo "Please install it from: https://git-lfs.github.io/"
        exit 1
    fi
    print_success "Git LFS is installed"
}

# Initialize Git repository if not already done
init_git_repo() {
    print_status "Initializing Git repository..."
    if [ ! -d ".git" ]; then
        git init
        print_success "Git repository initialized"
    else
        print_success "Git repository already exists"
    fi
}

# Setup Git LFS for large model files
setup_git_lfs() {
    print_status "Setting up Git LFS for model files..."
    
    # Initialize Git LFS
    git lfs install
    
    # Track large model files
    git lfs track "model/*.safetensors"
    git lfs track "model/*.bin"
    git lfs track "model/spiece.model"
    git lfs track "model/tokenizer.json"
    git lfs track "model/training_args.bin"
    
    # Add .gitattributes
    git add .gitattributes
    
    print_success "Git LFS configured for model files"
}

# Create Railway project
create_railway_project() {
    print_status "Creating Railway project..."
    
    # Login to Railway (if not already logged in)
    railway login
    
    # Create new project
    railway project create "grammar-correction-api"
    
    print_success "Railway project created"
}

# Add Redis service to Railway project
add_redis_service() {
    print_status "Adding Redis service to Railway project..."
    
    # Add Redis addon
    railway add redis
    
    print_success "Redis service added"
}

# Set environment variables
set_environment_variables() {
    print_status "Setting environment variables..."
    
    # Core application settings
    railway variables set DEBUG=false
    railway variables set LOG_LEVEL=INFO
    railway variables set ALLOWED_ORIGINS='["*"]'
    railway variables set PORT=8000
    railway variables set HOST=0.0.0.0
    
    # Flower configuration
    railway variables set FLOWER_USER=admin
    railway variables set FLOWER_PASSWORD=BigDrops@9991
    
    # Performance settings
    railway variables set RATE_LIMIT_PER_MINUTE=100
    railway variables set RATE_LIMIT_BURST=200
    railway variables set MAX_WORKERS=4
    
    # Model settings
    railway variables set MODEL_PATH=./model
    railway variables set MAX_FILE_SIZE=10485760
    railway variables set MAX_ZIP_EXTRACT_SIZE=52428800
    railway variables set MAX_FILES_IN_ZIP=100
    
    # Security
    railway variables set SECRET_KEY=$(openssl rand -hex 32)
    
    print_success "Environment variables set"
}

# Deploy to Railway
deploy_to_railway() {
    print_status "Deploying to Railway..."
    
    # Link to Railway project
    railway link
    
    # Deploy the application
    railway up
    
    print_success "Application deployed to Railway!"
}

# Get deployment URL
get_deployment_url() {
    print_status "Getting deployment URL..."
    
    # Get the deployment URL
    DEPLOYMENT_URL=$(railway domain)
    
    if [ ! -z "$DEPLOYMENT_URL" ]; then
        print_success "Deployment URL: https://$DEPLOYMENT_URL"
        echo ""
        echo "🎉 Your Grammar Correction API is now live!"
        echo "📖 API Documentation: https://$DEPLOYMENT_URL/docs"
        echo "❤️ Health Check: https://$DEPLOYMENT_URL/health"
        echo "📊 Metrics: https://$DEPLOYMENT_URL/metrics"
    else
        print_warning "Could not retrieve deployment URL. Check Railway dashboard."
    fi
}

# Main deployment process
main() {
    echo "🎯 Grammar Correction API - Railway Deployment"
    echo "=============================================="
    echo ""
    
    # Pre-deployment checks
    check_railway_cli
    check_git_lfs
    
    # Git setup
    init_git_repo
    setup_git_lfs
    
    # Railway setup
    create_railway_project
    add_redis_service
    set_environment_variables
    
    # Deploy
    deploy_to_railway
    get_deployment_url
    
    echo ""
    print_success "🚀 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Upload your model files to the Railway project"
    echo "2. Test the API endpoints"
    echo "3. Monitor the application logs"
    echo "4. Set up custom domain if needed"
    echo ""
    echo "For more information, visit: https://docs.railway.app/"
}

# Run main function
main "$@"
