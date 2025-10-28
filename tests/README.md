# Image Processing API Tests

This directory contains comprehensive tests for the grammar correction API's image processing capabilities.

## Test Files

### 1. `test_image_processing.py`
Main test file that tests the complete image processing pipeline using pytest and FastAPI TestClient.

**Features:**
- Generates test images with grammatical mistakes
- Processes images through the API
- Converts base64 output to standard images
- Saves all results to test directories
- Verifies corrections were made correctly

**Usage:**
```bash
# Run all image processing tests
pytest tests/test_image_processing.py -v

# Run specific test method
pytest tests/test_image_processing.py::TestImageProcessingPipeline::test_image_processing_pipeline -v
```

### 2. `test_api_real.py`
Script to test the API with real HTTP requests (requires running API server).

**Features:**
- Tests health endpoint
- Sends real HTTP requests to the API
- Saves reconstructed images
- Generates comprehensive test results

**Usage:**
```bash
# Test with default localhost:8000
python tests/test_api_real.py

# Test with custom API URL
python tests/test_api_real.py http://your-api-url:port
```

### 3. `generate_test_images.py`
Utility script to generate test images with grammatical mistakes.

**Usage:**
```bash
python tests/generate_test_images.py
```

## Test Directory Structure

```
tests/
├── input_images/          # Generated test images with grammar errors
├── output_images/         # Reconstructed images from API
├── test_image_processing.py
├── test_api_real.py
├── generate_test_images.py
└── README.md
```

## Prerequisites

1. **API Server Running**: For real API tests, ensure the grammar correction API is running
2. **Dependencies**: Install required packages:
   ```bash
   pip install pytest pillow requests fastapi
   ```

## Running Tests

### 1. Unit Tests (with mocked API)
```bash
# Run all tests
pytest tests/ -v

# Run only image processing tests
pytest tests/test_image_processing.py -v

# Run with detailed output
pytest tests/test_image_processing.py -v -s
```

### 2. Real API Tests
```bash
# Start the API server first
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, run real API tests
python tests/test_api_real.py
```

### 3. Generate Test Images
```bash
python tests/generate_test_images.py
```

## Test Cases

The tests include various grammatical error scenarios:

1. **Basic Grammar Errors**: "This are a test" → "This is a test"
2. **Contractions**: "It dont work" → "It doesn't work"
3. **Spelling Mistakes**: "recieved" → "received"
4. **Plural/Singular**: "The students was" → "The students were"
5. **Possessive Errors**: "theyre homework" → "their homework"

## Expected Outputs

### Test Results
- `image_processing_test_results.json`: Detailed test results from pytest
- `real_api_test_results.json`: Results from real API tests

### Generated Images
- `input_images/`: Original test images with grammar errors
- `output_images/`: Reconstructed images with corrections highlighted

## Troubleshooting

### Common Issues

1. **Font Not Found**: The test tries multiple font paths. If all fail, it uses the default font.
2. **API Not Running**: Ensure the API server is running before running real API tests.
3. **Permission Errors**: Ensure write permissions for the test directories.

### Debug Mode
Run tests with debug output:
```bash
pytest tests/test_image_processing.py -v -s --tb=long
```

## Customization

### Adding New Test Cases
Edit the `test_cases` list in `test_image_processing.py`:

```python
test_cases = [
    {
        "filename": "my_test.png",
        "text": "Your test sentence with errors.",
        "expected_corrections": ["error1", "error2"]
    }
]
```

### Modifying API URL
Change the default API URL in `test_api_real.py`:

```python
def __init__(self, api_url: str = "http://your-api-url:port"):
```

## Performance Testing

The tests include performance measurements:
- Total request time
- API processing time
- Image generation time

Adjust performance thresholds in the test files as needed for your environment.
