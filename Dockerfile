FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for ML libraries and image processing
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (required for tokenizers and sentencepiece compilation)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Skip Git LFS during build (prevents LFS download failures)
ENV GIT_LFS_SKIP_SMUDGE=1

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download model from Hugging Face during deployment
# This solves Git LFS issues by downloading model at build time instead of from Git
RUN mkdir -p ./model && \
    if [ -n "$MODEL_ID" ]; then \
        echo "Downloading model from Hugging Face: $MODEL_ID"; \
        python -c "from huggingface_hub import snapshot_download; import os; snapshot_download(repo_id=os.environ['MODEL_ID'], local_dir='./model', token=os.environ.get('HF_TOKEN', None))"; \
        echo "Model downloaded successfully from Hugging Face"; \
        ls -lh ./model/ || echo "Model directory listing failed"; \
    else \
        echo "WARNING: MODEL_ID not set - model will not be downloaded"; \
        echo "App will work but grammar correction may be limited (fallback mode)"; \
    fi

# Create necessary directories
RUN mkdir -p /tmp/uploads /tmp/cache /tmp/outputs && \
    chmod -R 755 /tmp

# Expose port (supports PORT env var for Cloud Run, defaults to 8000)
EXPOSE 8000
ENV PORT=8000

# Health check with extended start period for model loading
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]