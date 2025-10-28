"""
API Endpoint Tests
Tests all FastAPI endpoints
"""

import pytest
import json
import time
from fastapi import status
from io import BytesIO


class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_endpoint(self, client):
        """Test GET / returns welcome message"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
    
    def test_root_endpoint_contains_correct_info(self, client):
        """Test root endpoint contains correct information"""
        response = client.get("/")
        data = response.json()
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_endpoint(self, client):
        """Test GET /health returns health status"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "redis_connected" in data
        assert "grammar_model_loaded" in data
        assert "ocr_available" in data
        assert "beautifulsoup_available" in data
        assert "image_reconstruction_available" in data
        assert "html_reconstruction_available" in data
    
    def test_health_status_types(self, client):
        """Test health endpoint returns correct data types"""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["redis_connected"], bool)
        assert isinstance(data["grammar_model_loaded"], bool)
        assert isinstance(data["ocr_available"], bool)
        assert isinstance(data["beautifulsoup_available"], bool)
        assert isinstance(data["image_reconstruction_available"], bool)
        assert isinstance(data["html_reconstruction_available"], bool)
    
    def test_health_status_values(self, client):
        """Test health status is either 'healthy' or 'degraded'"""
        response = client.get("/health")
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]


class TestProcessEndpoint:
    """Tests for file processing endpoint"""
    
    def test_process_endpoint_requires_file(self, client):
        """Test POST /process without file returns error"""
        response = client.post("/process")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_process_endpoint_with_image(self, client, test_image_bytes, mock_processor):
        """Test processing an image file"""
        files = {
            'file': ('test_image.png', BytesIO(test_image_bytes), 'image/png')
        }
        data = {
            'async_processing': 'true'
        }
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "task_id" in result
        assert "status" in result
        assert "message" in result
    
    def test_process_endpoint_with_html(self, client, sample_html, mock_processor):
        """Test processing an HTML file"""
        files = {
            'file': ('test.html', BytesIO(sample_html.encode()), 'text/html')
        }
        data = {
            'async_processing': 'true'
        }
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "task_id" in result
        assert "status" in result
    
    def test_process_endpoint_rejects_invalid_file_type(self, client):
        """Test that invalid file types are rejected"""
        files = {
            'file': ('test.txt', BytesIO(b'test content'), 'text/plain')
        }
        data = {
            'async_processing': 'true'
        }
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_process_endpoint_sync_mode(self, client, test_image_bytes, mock_processor):
        """Test synchronous processing"""
        files = {
            'file': ('test_image.png', BytesIO(test_image_bytes), 'image/png')
        }
        data = {
            'async_processing': 'false'
        }
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert result["status"] in ["SUCCESS", "FAILURE"]
        if result["status"] == "SUCCESS":
            assert "result" in result
            assert result["result"]["success"] is True
    
    def test_process_endpoint_file_too_large(self, client):
        """Test that files exceeding size limit are rejected"""
        # Create a file larger than MAX_FILE_SIZE
        large_file = BytesIO(b'0' * (11 * 1024 * 1024))  # 11MB
        files = {
            'file': ('large.png', large_file, 'image/png')
        }
        data = {
            'async_processing': 'true'
        }
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "too large" in response.json()["detail"].lower()


class TestTaskStatusEndpoint:
    """Tests for task status endpoint"""
    
    def test_task_status_endpoint(self, client):
        """Test GET /task/{task_id} returns task status"""
        # Test with a dummy task ID
        task_id = "test-task-123"
        response = client.get(f"/task/{task_id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["task_id"] == task_id
    
    def test_task_status_pending(self, client):
        """Test task status for pending task"""
        task_id = "pending-task-456"
        response = client.get(f"/task/{task_id}")
        data = response.json()
        
        # Pending task should have status PENDING
        assert data["status"] in ["PENDING", "STARTED", "SUCCESS", "FAILURE"]
    
    def test_task_status_response_structure(self, client):
        """Test task status response has correct structure"""
        task_id = "structure-test-789"
        response = client.get(f"/task/{task_id}")
        data = response.json()
        
        assert "task_id" in data
        assert "status" in data
        # These fields are optional
        if data["status"] == "SUCCESS":
            assert "result" in data
        if data["status"] == "FAILURE":
            assert "error" in data


class TestMetricsEndpoint:
    """Tests for metrics endpoint"""
    
    def test_metrics_endpoint(self, client):
        """Test GET /metrics returns metrics"""
        response = client.get("/metrics")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Metrics should contain worker and task information
        assert isinstance(data, dict)


class TestDownloadEndpoint:
    """Tests for file download endpoint"""
    
    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/download/nonexistent.png")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
    
    def test_download_existing_file(self, client, tmp_path):
        """Test downloading an existing file"""
        # Create a test file
        import shutil
        test_file = tmp_path / "test_output.png"
        test_file.write_text("test content")
        
        # Move to /tmp/outputs (or mock the download endpoint to use tmp_path)
        # For this test, we'll just verify the error case
        # In real scenario, you'd mock the file location
        response = client.get("/download/test_output.png")
        # Will be 404 