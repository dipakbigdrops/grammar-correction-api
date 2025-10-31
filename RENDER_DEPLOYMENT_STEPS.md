# Complete Render Deployment Guide - Step by Step

## 🎯 Overview

This guide will walk you through deploying your Grammar Correction API to Render with automatic model download from Hugging Face.

**Repository**: https://github.com/dipakbigdrops/grammar-correction-api  
**Model Repository**: https://huggingface.co/dipak-bigdrops/grammar-correction-model

---

## ✅ Prerequisites Checklist

- [ ] Render account created (https://render.com)
- [ ] GitHub repository: https://github.com/dipakbigdrops/grammar-correction-api
- [ ] Hugging Face model uploaded: `dipak-bigdrops/grammar-correction-model`
- [ ] Model files removed from Git (✅ Already done)

---

## 📋 Step 1: Create Key-Value Store (Redis)

### 1.1 Navigate to Render Dashboard

1. Go to **https://dashboard.render.com**
2. Log in to your Render account

### 1.2 Create Key-Value Store

1. Click **"New +"** button (top right)
2. Select **"Key-Value"** from the dropdown
3. Configure:
   - **Name**: `grammar-correction-kv` (or your preferred name)
   - **Plan**: `Starter` (or `Free` for testing)
   - **Region**: Choose closest to you (e.g., `Oregon`)
   - Click **"Create Key-Value"**

### 1.3 Get Connection Details

After creation, note these values (you'll need them later):

- **Internal Redis Host**: `red-xxxxxxxxxxxxxxxxx` (e.g., `red-d42auu75r7bs73dj7j40`)
- **Internal Redis Port**: Usually `6379`
- **Redis Password**: (if shown, or leave empty if not provided)
- **Internal Redis URL**: `redis://red-xxxxxxxxxxxxxxxxx:6379`

**Important**: Use the **Internal Redis Host**, not the external/public URL.

---

## 📋 Step 2: Create Web Service

### 2.1 Navigate to Create Service

1. In Render Dashboard, click **"New +"** button
2. Select **"Web Service"**

### 2.2 Connect Repository

1. Click **"Connect account"** if not already connected
2. Select your GitHub account
3. Choose repository: **`dipakbigdrops/grammar-correction-api`**
4. Click **"Connect"**

### 2.3 Configure Service

Fill in the following settings:

#### Basic Information
- **Name**: `grammar-correction-api` (or your choice)
- **Region**: Same as Key-Value store (e.g., `Oregon`)
- **Branch**: `master` (or `main` if that's your default branch)

#### Build & Deploy Settings
- **Runtime**: Select **"Docker"** (important!)
- **Build Command**: **Leave empty** (Dockerfile handles this)
- **Start Command**: **Leave empty** (Dockerfile CMD handles this)
- **Health Check Path**: `/health`

#### Advanced Settings (Optional)
- **Auto-Deploy**: `Yes` (automatically deploys on push)
- **Disk** (Optional):
  - Click **"Add Disk"**
  - **Disk Name**: `app-disk`
  - **Mount Path**: `/tmp`
  - **Size**: `1 GB`
  - Click **"Save"**

#### Don't Deploy Yet!
- Click **"Advanced"** at the bottom
- Scroll to **"Environment Variables"** section
- **DO NOT** click "Create Web Service" yet - we need to set environment variables first

---

## 📋 Step 3: Set Environment Variables

### 3.1 Navigate to Environment Variables

In the Web Service configuration, scroll to **"Environment Variables"** section.

### 3.2 Add Required Variables

Click **"Add Environment Variable"** for each of the following:

#### Critical Variables (MUST SET)

```bash
Key: PYTHON_VERSION
Value: 3.11.0
```

```bash
Key: GIT_LFS_SKIP_SMUDGE
Value: 1
```

```bash
Key: MODEL_ID
Value: dipak-bigdrops/grammar-correction-model
```

```bash
Key: MODEL_PATH
Value: ./model
```

```bash
Key: APP_NAME
Value: Grammar Correction API
```

```bash
Key: ENVIRONMENT
Value: production
```

```bash
Key: DEBUG
Value: false
```

#### Redis/Key-Value Store Variables

Replace `red-d42auu75r7bs73dj7j40` with your actual Redis host from Step 1:

```bash
Key: REDIS_HOST
Value: red-d42auu75r7bs73dj7j40
```

```bash
Key: REDIS_PORT
Value: 6379
```

```bash
Key: REDIS_DB
Value: 0
```

```bash
Key: REDIS_PASSWORD
Value: 
(Leave empty if no password, or enter your password if provided)
```

#### CORS Settings (MUST be valid JSON)

```bash
Key: ALLOWED_ORIGINS
Value: ["*"]
```

**Important**: Must include brackets and quotes - `["*"]` not just `*`

### 3.3 Optional Variables

These are optional but recommended:

```bash
Key: API_WORKERS
Value: 2
```

```bash
Key: ENABLE_CACHING
Value: true
```

```bash
Key: CACHE_TTL
Value: 3600
```

```bash
Key: RATE_LIMIT_PER_MINUTE
Value: 1000
```

```bash
Key: RATE_LIMIT_BURST
Value: 2000
```

### 3.4 Complete Service Creation

1. Review all environment variables
2. Scroll to bottom
3. Click **"Create Web Service"**

---

## 📋 Step 4: Monitor Deployment

### 4.1 Watch Build Logs

After clicking "Create Web Service", Render will:

1. **Clone repository** - Should complete without Git LFS errors
2. **Build Docker image** - Installs dependencies
3. **Download model from Hugging Face** - Automatically downloads model
4. **Deploy service** - Starts the application

### 4.2 Check Build Logs

Watch the logs for:

✅ **Expected Messages:**
```
Cloning from https://github.com/dipakbigdrops/grammar-correction-api
(No Git LFS errors)
...
Downloading model from Hugging Face: dipak-bigdrops/grammar-correction-model
Model downloaded successfully from Hugging Face
...
Successfully built
Service is live
```

❌ **If you see errors:**

- **Git LFS errors**: Ensure `GIT_LFS_SKIP_SMUDGE=1` is set
- **lxml build errors**: Ensure `PYTHON_VERSION=3.11.0` (not 3.13)
- **Model download errors**: Check `MODEL_ID` is correct and model is public
- **ALLOWED_ORIGINS error**: Ensure value is `["*"]` with brackets and quotes

---

## 📋 Step 5: Verify Deployment

### 5.1 Get Your Service URL

After deployment, Render will provide:
- **Service URL**: `https://your-app-name.onrender.com`

### 5.2 Test Endpoints

#### Health Check
```bash
GET https://your-app-name.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "redis_connected": true,
  "grammar_model_loaded": true,
  "ocr_available": true,
  "beautifulsoup_available": true,
  "image_reconstruction_available": true,
  "html_reconstruction_available": true
}
```

#### Root Endpoint
```bash
GET https://your-app-name.onrender.com/
```

**Expected Response:**
```json
{
  "message": "Welcome to Grammar Correction API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

#### API Documentation
```bash
GET https://your-app-name.onrender.com/docs
```

Should show Swagger UI with all API endpoints.

---

## 📋 Step 6: Test API Functionality

### 6.1 Test Process Endpoint

```bash
POST https://your-app-name.onrender.com/process
Content-Type: multipart/form-data

file: <your-image-file>
async_processing: true
```

### 6.2 Verify Model is Working

Check the health endpoint - `"grammar_model_loaded": true` confirms model downloaded and loaded successfully.

---

## 🔧 Complete Environment Variables Reference

### Copy-Paste Ready List

Here's a complete list of all environment variables to set in Render:

```bash
# CRITICAL - Python Version (must be 3.11, NOT 3.13)
PYTHON_VERSION=3.11.0

# CRITICAL - Skip Git LFS
GIT_LFS_SKIP_SMUDGE=1

# Model Configuration
MODEL_ID=dipak-bigdrops/grammar-correction-model
MODEL_PATH=./model

# Application Settings
APP_NAME=Grammar Correction API
ENVIRONMENT=production
DEBUG=false

# Redis/Key-Value Store (replace with your values)
REDIS_HOST=red-d42auu75r7bs73dj7j40
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# CORS (MUST be valid JSON)
ALLOWED_ORIGINS=["*"]

# Optional Settings
API_WORKERS=2
ENABLE_CACHING=true
CACHE_TTL=3600
RATE_LIMIT_PER_MINUTE=1000
RATE_LIMIT_BURST=2000
```

---

## 🚨 Troubleshooting Guide

### Issue 1: Build Fails with lxml Error

**Error:**
```
ERROR: Failed building wheel for lxml
```

**Solution:**
1. Ensure `PYTHON_VERSION=3.11.0` is set (NOT 3.13)
2. Redeploy service

---

### Issue 2: Git LFS Errors During Clone

**Error:**
```
This repository exceeded its LFS budget
```

**Solution:**
1. Ensure `GIT_LFS_SKIP_SMUDGE=1` is set
2. Verify `.gitattributes` has LFS rules commented out
3. Verify model files are in `.gitignore`
4. Redeploy service

---

### Issue 3: Model Not Downloading

**Error:**
```
WARNING: MODEL_ID not set during build - model will not be downloaded
```

**Solution:**
1. Verify `MODEL_ID=dipak-bigdrops/grammar-correction-model` is set
2. Check model is public on Hugging Face: https://huggingface.co/dipak-bigdrops/grammar-correction-model
3. Check build logs for download errors
4. Redeploy service

---

### Issue 4: ALLOWED_ORIGINS JSON Error

**Error:**
```
error parsing value for field "ALLOWED_ORIGINS" from source "EnvSettingsSource"
```

**Solution:**
1. Change `ALLOWED_ORIGINS=*` to `ALLOWED_ORIGINS=["*"]`
2. Must be valid JSON format with brackets and quotes
3. Redeploy service

---

### Issue 5: Redis Connection Failed

**Error:**
```
Redis connection test failed
```

**Solution:**
1. Verify `REDIS_HOST` matches your Key-Value store internal host
2. Verify `REDIS_PORT=6379`
3. Set `REDIS_PASSWORD` if your Key-Value store requires it
4. App will still work with FakeRedis fallback, but verify settings

---

### Issue 6: Port/Start Command Error

**Error:**
```
bash: line 1: app.main:app: command not found
```

**Solution:**
1. Leave **Start Command** empty in Render (Dockerfile handles this)
2. Ensure Docker deployment is enabled
3. Verify Dockerfile CMD is correct

---

### Issue 7: Health Check Shows "degraded"

**Status:**
```json
{
  "status": "degraded",
  "grammar_model_loaded": false
}
```

**Possible Causes:**
1. Model didn't download during build
2. Model download failed
3. `MODEL_ID` not set correctly

**Solution:**
1. Check build logs for model download messages
2. Verify `MODEL_ID` is set correctly
3. Verify model is public on Hugging Face
4. Redeploy service

---

## ✅ Deployment Checklist

Use this checklist to ensure everything is configured correctly:

### Pre-Deployment
- [ ] Key-Value store created on Render
- [ ] Redis connection details noted (host, port, password)
- [ ] Web Service created on Render
- [ ] GitHub repository connected
- [ ] Docker deployment enabled

### Environment Variables
- [ ] `PYTHON_VERSION=3.11.0` set (NOT 3.13)
- [ ] `GIT_LFS_SKIP_SMUDGE=1` set
- [ ] `MODEL_ID=dipak-bigdrops/grammar-correction-model` set
- [ ] `MODEL_PATH=./model` set
- [ ] `REDIS_HOST` set (from Key-Value store)
- [ ] `REDIS_PORT=6379` set
- [ ] `REDIS_DB=0` set
- [ ] `REDIS_PASSWORD` set (or left empty if not required)
- [ ] `ALLOWED_ORIGINS=["*"]` set (as valid JSON)
- [ ] `APP_NAME` set
- [ ] `ENVIRONMENT=production` set
- [ ] `DEBUG=false` set

### Build Settings
- [ ] Runtime set to **Docker**
- [ ] Build Command: **Empty** (or not set)
- [ ] Start Command: **Empty** (or not set)
- [ ] Health Check Path: `/health`

### Verification
- [ ] Build completes successfully
- [ ] Build logs show model download from Hugging Face
- [ ] Service starts successfully
- [ ] Health endpoint returns `"status": "healthy"`
- [ ] Health endpoint shows `"grammar_model_loaded": true`
- [ ] API docs accessible at `/docs`
- [ ] Root endpoint accessible at `/`

---

## 📊 Expected Build Timeline

1. **Git Clone** (30-60 seconds)
   - Should complete without Git LFS errors

2. **Docker Build** (5-10 minutes)
   - Install system dependencies
   - Install Python dependencies
   - Install Rust
   - Copy application code

3. **Model Download** (2-5 minutes)
   - Downloads from Hugging Face: `dipak-bigdrops/grammar-correction-model`
   - Saves to `./model` directory

4. **Service Start** (30-60 seconds)
   - Starts FastAPI application
   - Loads model into memory
   - Connects to Redis
   - Becomes live

**Total Deployment Time**: ~10-20 minutes (first time)

---

## 🔄 Redeployment

After initial deployment, redeployments are faster:

1. **Push changes to GitHub**
2. **Render automatically detects changes**
3. **Automatically rebuilds and redeploys**
4. **Model re-downloads if needed** (cached if same version)

---

## 📝 Summary

✅ **Model files removed from Git** - No Git LFS issues  
✅ **Model downloads from Hugging Face** - Automatic during deployment  
✅ **All environment variables documented** - Easy to configure  
✅ **Deployment ready** - All errors fixed  

**Your repository is now optimized for Render deployment!** 🚀

---

## 📞 Need Help?

If deployment fails:

1. **Check build logs** in Render Dashboard
2. **Verify all environment variables** are set correctly
3. **Check troubleshooting section** above
4. **Verify model is public** on Hugging Face

**Repository**: https://github.com/dipakbigdrops/grammar-correction-api  
**Model**: https://huggingface.co/dipak-bigdrops/grammar-correction-model

