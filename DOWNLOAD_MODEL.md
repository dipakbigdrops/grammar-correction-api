# Model Download Configuration

## Overview

Model files are **NOT** stored in the Git repository to avoid Git LFS issues. Instead, they are downloaded from Hugging Face Hub during deployment.

## Model Repository

- **Hugging Face Repository**: `dipak-bigdrops/grammar-correction-model`
- **URL**: https://huggingface.co/dipak-bigdrops/grammar-correction-model

## How It Works

1. **During Build**: The Dockerfile automatically downloads the model from Hugging Face if `MODEL_ID` environment variable is set
2. **No Git LFS**: Model files are completely excluded from Git, solving LFS bandwidth issues
3. **Automatic Download**: On Render, the model is downloaded during the Docker build process

## Configuration

### Required Environment Variable

Set this in Render Dashboard → Environment Variables:

```
MODEL_ID=dipak-bigdrops/grammar-correction-model
```

### Optional Environment Variable

Only needed if your model is private:

```
HF_TOKEN=hf_your_token_here
```

## Deployment Process

1. **Build Phase**: 
   - Dockerfile checks for `MODEL_ID`
   - Downloads model from Hugging Face using `snapshot_download()`
   - Saves to `./model` directory

2. **Runtime**:
   - App loads model from `./model` directory
   - Works exactly as if model was in repository

## Verification

After deployment, check the build logs for:
```
Downloading model from Hugging Face: dipak-bigdrops/grammar-correction-model
Model downloaded successfully from Hugging Face
```

Check health endpoint:
```
https://your-app.onrender.com/health
```

Should show: `"grammar_model_loaded": true`

## Troubleshooting

### Model Not Downloading

1. Check `MODEL_ID` is set correctly in Render
2. Verify model is public on Hugging Face (or set `HF_TOKEN` if private)
3. Check build logs for download errors

### Model Files Missing Locally

For local development, you can:
1. Download from Hugging Face manually:
   ```bash
   python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='dipak-bigdrops/grammar-correction-model', local_dir='./model')"
   ```

2. Or use the upload script in reverse (download mode)

## Benefits

✅ No Git LFS bandwidth issues
✅ Faster Git operations (model files not in repo)
✅ Easy model updates (update on Hugging Face, redeploy)
✅ Smaller repository size
✅ Works seamlessly on Render

