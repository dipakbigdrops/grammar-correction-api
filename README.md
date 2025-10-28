# Grammar Correction API - Production Ready

A high-performance, scalable API for grammar correction with OCR and HTML processing support.

## Features

-   **ZIP Archive Support** - Process multiple files in one request
-   Asynchronous task processing with Celery
-   Redis caching for improved performance
-   Support for images (OCR), HTML files, and ZIP archives
-   Batch processing via ZIP files (up to 100 files per archive)
-   Docker & Docker Compose support
-   Kubernetes deployment with auto-scaling
-   Monitoring with Flower
-   Load testing with Locust
-   Production-ready with health checks
-   Handles 10,000+ requests per minute
-   Comprehensive security features (ZIP bomb protection, file validation)

## Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for K8s deployment)
- Python 3.10+ (for local development)
- Your trained grammar correction model

##  Project Structure