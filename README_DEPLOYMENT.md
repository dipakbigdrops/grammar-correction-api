# Deployment Guide - Model Download from Hugging Face

## ✅ Setup Complete!

Your codebase has been customized to:
- **Exclude model files from Git** (solves Git LFS issues)
- **Download model from Hugging Face during deployment**
- **Work seamlessly on Render**

## Quick Start for Render Deployment

### 1. Set Environment Variables in Render

Go to **Render Dashboard → Your Web Service → Environment** and add:

```
PYTHON_VERSION=3.11.0
GIT_LFS_SKIP_SMUDGE=1
MODEL_ID=dipak-bigdrops/grammar-correction-model
APP_NAME=Grammar Correction API
ENVIRONMENT=production
DEBUG=false
MODEL_PATH=./model
REDIS_HOST=red-d42auu75r7bs73dj7j40
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
ALLOWED_ORIGINS=["*"]
```

### 2. Deploy

1. Push your code to GitHub (model files are ignored)
2. Render will automatically build and deploy
3. During build, model will be downloaded from Hugging Face
4. No Git LFS errors! ✅

## How It Works

### Before (With Git LFS - Problem)
```
Git Clone → Download LFS files → Build → Deploy
         ❌ LFS budget exceeded!
```

### Now (With Hugging Face - Solution)
```
Git Clone → Skip LFS → Build → Download from HF → Deploy
         ✅ No LFS issues!
```

## What Changed

### ✅ Files Modified

1. **`.gitattributes`** - Commented out Git LFS tracking
2. **`.gitignore`** - Model files now ignored
3. **`Dockerfile`** - Downloads model from Hugging Face during build
4. **`.dockerignore`** - Excludes model files from Docker build

### ✅ Files Created

1. **`model/.gitkeep`** - Keeps model directory in Git (empty)
2. **`DOWNLOAD_MODEL.md`** - Detailed model download documentation
3. **`README_DEPLOYMENT.md`** - This file

## Model Location

- **Repository**: `dipak-bigdrops/grammar-correction-model`
- **URL**: https://huggingface.co/dipak-bigdrops/grammar-correction-model
- **Download**: Automatic during Docker build on Render

## Build Process

When Render builds your Docker image:

1. ✅ Git clone (skips LFS files - no errors)
2. ✅ Install Python dependencies
3. ✅ Copy application code
4. ✅ **Download model from Hugging Face** (if `MODEL_ID` is set)
5. ✅ Build completes successfully

## Verification

After deployment, check:

1. **Build Logs**: Should show:
   ```
   Downloading model from Hugging Face: dipak-bigdrops/grammar-correction-model
   Model downloaded successfully from Hugging Face
   ```

2. **Health Endpoint**: `https://your-app.onrender.com/health`
   - Should show: `"grammar_model_loaded": true`

3. **API Docs**: `https://your-app.onrender.com/docs`

## Troubleshooting

### Build Still Shows LFS Errors?

1. Ensure `GIT_LFS_SKIP_SMUDGE=1` is set in Render
2. Verify `.gitattributes` has LFS rules commented out
3. Check model files are in `.gitignore`

### Model Not Downloading?

1. Check `MODEL_ID=dipak-bigdrops/grammar-correction-model` is set
2. Verify model is public on Hugging Face
3. Check build logs for download errors

### Model Not Loading?

1. Check build logs for download success message
2. Verify `MODEL_PATH=./model` is set
3. Check health endpoint for model status

## Local Development

For local development, download the model manually:

```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='dipak-bigdrops/grammar-correction-model', local_dir='./model')"
```

Or use the upload script in download mode.

## Benefits

✅ **No Git LFS issues** - Model files excluded from Git
✅ **Faster Git operations** - Smaller repository
✅ **Easy updates** - Update model on Hugging Face, redeploy
✅ **Automatic download** - Model downloads during build
✅ **Works on Render** - No LFS bandwidth limits

## Summary

Your codebase is now optimized for Render deployment:
- Model files excluded from Git ✅
- Model downloads from Hugging Face during build ✅
- No Git LFS issues ✅
- Ready to deploy! 🚀

