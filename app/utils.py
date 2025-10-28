"""
Utility Functions
"""
import hashlib
import os
from typing import Optional
import redis
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)

# Redis connection
redis_client = None


def get_redis_client():
    """Get Redis client instance - uses fakeredis as fallback for Windows"""
    global redis_client
    if redis_client is None:
        try:
            # Try to connect to real Redis first
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            redis_client.ping()
            logger.info("✅ Connected to Redis server successfully")
        except Exception as e:
            logger.warning(f"Real Redis not available: {e}")
            try:
                # Fallback to fakeredis (in-memory Redis for development)
                import fakeredis
                redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
                redis_client.ping()
                logger.info("✅ Using FakeRedis (in-memory) - perfect for development!")
            except Exception as fake_error:
                logger.error(f"Failed to initialize FakeRedis: {fake_error}")
                redis_client = None
    return redis_client


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_cached_result(file_hash: str) -> Optional[dict]:
    """Get cached result from Redis"""
    if not settings.ENABLE_CACHING:
        return None
    
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        cached = client.get(f"result:{file_hash}")
        if cached:
            logger.info(f"Cache hit for hash: {file_hash}")
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Error getting cached result: {e}")
    
    return None


def set_cached_result(file_hash: str, result: dict):
    """Cache result in Redis"""
    if not settings.ENABLE_CACHING:
        return
    
    client = get_redis_client()
    if client is None:
        return
    
    try:
        client.setex(
            f"result:{file_hash}",
            settings.CACHE_TTL,
            json.dumps(result)
        )
        logger.info(f"Cached result for hash: {file_hash}")
    except Exception as e:
        logger.error(f"Error caching result: {e}")


def create_directories():
    """Create necessary directories"""
    directories = [
        "/tmp/uploads",
        "/tmp/outputs",
        "/tmp/cache"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")

def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str = "/tmp/uploads") -> str:
    """Save uploaded file and return path"""
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_hash = hashlib.md5(file_content).hexdigest()[:8]
    base_name, ext = os.path.splitext(filename)
    
    # Limit base_name length to prevent filesystem issues
    max_base_length = 200  # Leave room for hash and extension
    if len(base_name) > max_base_length:
        base_name = base_name[:max_base_length]
    
    # Sanitize filename to remove problematic characters
    base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_', '.'))
    base_name = base_name.strip()
    
    # If base_name is empty after sanitization, use a default
    if not base_name:
        base_name = "file"
    
    unique_filename = f"{base_name}_{file_hash}{ext}"
    
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    logger.info(f"Saved uploaded file to: {file_path}")
    return file_path


def cleanup_old_files(directory: str, max_age_seconds: int = 3600):
    """Clean up old files from directory"""
    import time
    
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    removed_count = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Error removing file {file_path}: {e}")
    
    if removed_count > 0:
        logger.info(f"Cleaned up {removed_count} old files from {directory}")