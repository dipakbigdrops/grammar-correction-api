# Railway.app Deployment Guide for Grammar Correction API

## Overview
This guide will help you deploy your Grammar Correction API to Railway.app, a modern cloud platform that makes deployment simple and efficient.

## Prerequisites

### 1. Install Railway CLI
```bash
# Install via npm
npm install -g @railway/cli

# Or install via curl (Linux/Mac)
curl -fsSL https://railway.app/install.sh | sh

# Verify installation
railway --version
```

### 2. Install Git LFS
```bash
# Windows (via Chocolatey)
choco install git-lfs

# macOS (via Homebrew)
brew install git-lfs

# Linux (Ubuntu/Debian)
sudo apt install git-lfs

# Verify installation
git lfs version
```

### 3. Login to Railway
```bash
railway login
```

## Quick Deployment

### Option 1: Automated Script (Recommended)
```bash
# Make the script executable
chmod +x deploy-railway.sh

# Run the deployment script
./deploy-railway.sh
```

### Option 2: Manual Deployment

#### Step 1: Initialize Git Repository
```bash
# Initialize Git repository
git init

# Setup Git LFS for model files
git lfs install
git lfs track "model/*.safetensors"
git lfs track "model/*.bin"
git lfs track "model/spiece.model"
git lfs track "model/tokenizer.json"
git lfs track "model/training_args.bin"

# Add all files
git add .
git commit -m "Initial commit: Grammar Correction API"
```

#### Step 2: Create Railway Project
```bash
# Create new Railway project
railway project create "grammar-correction-api"

# Link to Railway project
railway link
```

#### Step 3: Add Redis Service
```bash
# Add Redis addon
railway add redis
```

#### Step 4: Set Environment Variables
```bash
# Core settings
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
```

#### Step 5: Deploy
```bash
# Deploy the application
railway up
```

## Environment Variables Reference

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["*"]` |
| `PORT` | Application port | `8000` |
| `HOST` | Application host | `0.0.0.0` |
| `FLOWER_USER` | Flower monitoring username | `admin` |
| `FLOWER_PASSWORD` | Flower monitoring password | `BigDrops@9991` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `100` |
| `RATE_LIMIT_BURST` | Rate limit burst | `200` |
| `MAX_WORKERS` | Maximum worker processes | `4` |
| `MODEL_PATH` | Path to model files | `./model` |
| `MAX_FILE_SIZE` | Maximum file size (bytes) | `10485760` |
| `MAX_ZIP_EXTRACT_SIZE` | Maximum ZIP extract size | `52428800` |
| `MAX_FILES_IN_ZIP` | Maximum files in ZIP | `100` |

## Model Files Upload

Since your model files are large (~895MB), you have several options:

### Option 1: Upload via Railway Dashboard
1. Go to your Railway project dashboard
2. Navigate to the "Files" section
3. Upload the `model/` directory contents

### Option 2: Use Railway CLI
```bash
# Upload model files
railway files upload model/
```

### Option 3: Use Git LFS (Recommended for version control)
```bash
# Add model files to Git LFS
git add model/
git commit -m "Add model files via LFS"
git push origin main
```

## Post-Deployment

### 1. Verify Deployment
```bash
# Get deployment URL
railway domain

# Test health endpoint
curl https://your-app.railway.app/health

# Test API documentation
open https://your-app.railway.app/docs
```

### 2. Monitor Application
```bash
# View logs
railway logs

# View metrics
railway metrics
```

### 3. Scale Application
```bash
# Scale to more instances
railway scale 2

# Scale to specific instance type
railway scale --instances 3 --type standard
```

## Troubleshooting

### Common Issues

#### 1. Model Files Not Found
```bash
# Check if model files are uploaded
railway files list

# Re-upload if missing
railway files upload model/
```

#### 2. Redis Connection Issues
```bash
# Check Redis service status
railway status

# Restart Redis service
railway restart redis
```

#### 3. Memory Issues
```bash
# Check memory usage
railway metrics

# Scale to higher memory instance
railway scale --type standard
```

#### 4. Build Failures
```bash
# Check build logs
railway logs --build

# Verify requirements.txt
cat requirements.txt
```

## Production Considerations

### 1. Custom Domain
```bash
# Add custom domain
railway domain add your-domain.com
```

### 2. SSL Certificate
Railway automatically provides SSL certificates for custom domains.

### 3. Monitoring
- Use Railway's built-in metrics
- Set up alerts for critical issues
- Monitor memory and CPU usage

### 4. Backup Strategy
- Regular database backups (if using database)
- Model files backup
- Environment variables backup

## Cost Optimization

### 1. Instance Sizing
- Start with `standard` instance type
- Scale based on actual usage
- Use `hobby` for development/testing

### 2. Resource Management
- Monitor memory usage
- Optimize model loading
- Use caching effectively

## Support

- Railway Documentation: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Railway Support: https://railway.app/support

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Upload model files
3. ✅ Test all endpoints
4. ✅ Set up monitoring
5. ✅ Configure custom domain
6. ✅ Set up CI/CD pipeline
7. ✅ Implement backup strategy
