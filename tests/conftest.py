"""
Pytest Configuration and Shared Fixtures
This file contains all reusable test fixtures
"""

import pytest
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import io

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.celery_app import celery_app
from app.processor import GrammarCorrectionProcessor
from app.config import settings


# ===========================
# Application Fixtures
# ===========================

@pytest.fixture(scope="session")
def test_app():
    """
    Provides the FastAPI test application
    Scope: session (created once for all tests)
    """
    return app


@pytest.fixture(scope="module")
def client(test_app):
    """
    Provides a test client for making HTTP requests
    Scope: module (created once per test module)
    """
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def celery_config():
    """
    Celery configuration for testing
    """
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,  # Execute tasks synchronously
        'task_eager_propagates': True,
    }


@pytest.fixture(scope="session")
def processor():
    """
    Provides a processor instance for testing
    Mock the model loading if model is not available in test environment
    """
    try:
        proc = GrammarCorrectionProcessor()
        return proc
    except Exception as e:
        # If model loading fails in test environment, create a mock processor
        pytest.skip(f"Skipping tests requiring model: {e}")


# ===========================
# Test Data Fixtures
# ===========================

@pytest.fixture
def sample_text():
    """Sample text with grammar errors"""
    return "This are a test sentence with grammar error."


@pytest.fixture
def corrected_text():
    """Expected corrected text"""
    return "This is a test sentence with grammar errors."


@pytest.fixture
def sample_corrections():
    """Sample corrections list"""
    return [
        {
            "original_word": "are",
            "corrected_word": "is",
            "original_context": "this are a test",
            "corrected_context": "this is a test"
        },
        {
            "original_word": "error",
            "corrected_word": "errors",
            "original_context": "with grammar error",
            "corrected_context": "with grammar errors"
        }
    ]


@pytest.fixture
def sample_html():
    """Sample HTML content"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Document</title></head>
    <body>
        <h1>Test Heading</h1>
        <p>This are a test paragraph with error.</p>
        <div>Another test content here.</div>
    </body>
    </html>
    """


@pytest.fixture
def test_image_bytes():
    """
    Create a simple test image as bytes
    """
    img = Image.new('RGB', (800, 600), color='white')
    # Add some text-like patterns (in real test, use image with actual text)
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a default font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    draw.text((50, 50), "This are a test image.", fill='black', font=font)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr.getvalue()


@pytest.fixture
def test_image_file(tmp_path, test_image_bytes):
    """
    Create a temporary test image file
    """
    image_path = tmp_path / "test_image.png"
    with open(image_path, 'wb') as f:
        f.write(test_image_bytes)
    return str(image_path)


@pytest.fixture
def test_html_file(tmp_path, sample_html):
    """
    Create a temporary HTML file
    """
    html_path = tmp_path / "test_document.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(sample_html)
    return str(html_path)


@pytest.fixture
def test_text_file(tmp_path, sample_text):
    """
    Create a temporary text file
    """
    text_path = tmp_path / "test_text.txt"
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(sample_text)
    return str(text_path)


# ===========================
# Mock Fixtures
# ===========================

@pytest.fixture
def mock_redis(monkeypatch):
    """
    Mock Redis client
    """
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        def get(self, key):
            return self.data.get(key)
        
        def setex(self, key, ttl, value):
            self.data[key] = value
        
        def ping(self):
            return True
    
    mock_redis_instance = MockRedis()
    
    def mock_get_redis_client():
        return mock_redis_instance
    
    from app import utils
    monkeypatch.setattr(utils, "get_redis_client", mock_get_redis_client)
    
    return mock_redis_instance


@pytest.fixture
def mock_processor(monkeypatch):
    """
    Mock processor for testing without actual model
    """
    class MockProcessor:
        def __init__(self):
            self.model = True
            self.tokenizer = True
            self.ocr_reader = True
        
        def is_ready(self):
            return {
                "grammar_model_loaded": True,
                "ocr_available": True
            }
        
        def process_input(self, input_path, output_dir="/tmp"):
            return {
                "success": True,
                "input_type": "image",
                "original_text": "This are a test.",
                "corrected_text": "This is a test.",
                "corrections": [
                    {
                        "original_word": "are",
                        "corrected_word": "is",
                        "original_context": "this are a",
                        "corrected_context": "this is a"
                    }
                ],
                "corrections_count": 1,
                "output_file": None,
                "processing_time_seconds": 1.5
            }
        
        def correct_grammar(self, text):
            return text.replace("are a", "is a").replace("error", "errors")
        
        def identify_corrections(self, original, corrected, context_words=3):
            return [
                {
                    "original_word": "are",
                    "corrected_word": "is",
                    "original_context": "this are a test",
                    "corrected_context": "this is a test"
                }
            ]
    
    mock_proc = MockProcessor()
    
    def mock_get_processor():
        return mock_proc
    
    from app import processor
    monkeypatch.setattr(processor, "get_processor", mock_get_processor)
    
    return mock_proc



# Environment Configuration


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment variables
    Auto-used for all tests
    """
    # Store original values
    original_env = {}
    
    # Test environment variables
    test_env = {
        "DEBUG": "True",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "ENABLE_CACHING": "False",  # Disable caching in tests
        "MODEL_PATH": "./model",
    }
    
    # Set test environment
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value



# Cleanup Fixtures


@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path):
    """
    Automatically cleanup temporary files after each test
    """
    yield
    # Cleanup code runs after test
    import shutil
    if tmp_path.exists():
        try:
            shutil.rmtree(tmp_path)
        except Exception as e:
            # Log cleanup errors but don't fail tests
            print(f"Warning: Failed to cleanup {tmp_path}: {e}")