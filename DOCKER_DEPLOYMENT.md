# Docker Deployment Guide

## Quick Start

### Build Docker Image

```bash
docker build -t grammar-correction-api:latest .
```

### Run with Docker Compose (Development)

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Run with Docker Compose (Production)

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Or load environment variables first:

```bash
export $(cat production.env | xargs)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Run Standalone Container

```bash
docker run -d \
  --name grammar-api \
  -p 8000:8000 \
  -e REDIS_HOST=redis \
  -e REDIS_PASSWORD=BigDrops@9991 \
  -v $(pwd)/model:/app/model:ro \
  grammar-correction-api:latest
```

## Docker Image Details

- **Base Image**: `python:3.11-slim`
- **Port**: 8000 (or use `PORT` environment variable)
- **Health Check**: `/health` endpoint
- **Start Period**: 120 seconds (for model loading)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Application port |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PASSWORD` | `BigDrops@9991` | Redis password |
| `MODEL_PATH` | `/app/model` | Path to model files |
| `ENVIRONMENT` | `production` | Environment mode |

## Model Files

The model files should be in the `model/` directory:
- `config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `generation_config.json`
- `special_tokens_map.json`
- `model.safetensors` (if available)

Model files are mounted as read-only volume in Docker Compose.

## Deployment Platforms

### Google Cloud Run

```bash
gcloud run deploy grammar-correction-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "REDIS_HOST=redis,ENVIRONMENT=production"
```

### AWS ECS / Fargate

Use the Docker image with ECS task definition. Set environment variables in task definition.

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name grammar-api \
  --image grammar-correction-api:latest \
  --dns-name-label grammar-api \
  --ports 8000 \
  --environment-variables PORT=8000
```

### Render.com / Railway / Fly.io

These platforms typically auto-detect Dockerfile and build automatically. Ensure:
- `PORT` environment variable is set
- Model files are available (via volume or Git LFS)

## Health Check

The container includes a health check that verifies the `/health` endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "redis_connected": true,
  "grammar_model_loaded": true
}
```

## Troubleshooting

### Model Files Missing

If model files are missing, the API will start but grammar correction may not work. Ensure:
1. Model files are in `model/` directory
2. Files are mounted/copied correctly in Docker

### Build Fails

Common issues:
- **Rust compilation errors**: Ensure Rust toolchain installs correctly
- **Memory errors**: Use `--memory` flag: `docker build --memory=4g .`
- **Network issues**: Use build arguments or proxy if behind firewall

### Container Won't Start

Check logs:
```bash
docker logs grammar-api
```

Common issues:
- Model loading timeout: Increase `start-period` in HEALTHCHECK
- Port already in use: Change port mapping
- Redis connection: Verify Redis is running and accessible

## Production Checklist

- [ ] Model files included in image or mounted as volume
- [ ] Redis configured and accessible
- [ ] Environment variables set correctly
- [ ] Health check passing
- [ ] CORS configured for your domain
- [ ] Rate limiting configured appropriately
- [ ] Monitoring/logging set up
- [ ] Backup strategy for model files

