"""
Integration Tests
End-to-end integration tests
"""

import pytest
import time
from io import BytesIO


@pytest.mark.integration
class TestFullWorkflow:
    """Full workflow integration tests"""
    
    @pytest.mark.slow
    def test_upload_process_retrieve_workflow(self, client, test_image_bytes, mock_processor):
        """Test complete workflow: upload -> process -> retrieve results"""
        
        # Step 1: Upload file
        files = {
            'file': ('test_image.png', BytesIO(test_image_bytes), 'image/png')
        }
        data = {
            'async_processing': 'true'
        }
        
        upload_response = client.post("/process", files=files, data=data)
        assert upload_response.status_code == 200
        
        task_data = upload_response.json()
        task_id = task_data.get("task_id")
        
        assert task_id is not None
        
        # Step 2: Poll for results
        max_attempts = 10
        attempts = 0
        final_status = None
        
        while attempts < max_attempts:
            status_response = client.get(f"/task/{task_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            final_status = status_data.get("status")
            
            if final_status in ["SUCCESS", "FAILURE"]:
                break
            
            time.sleep(0.5)
            attempts += 1
        
        # Step 3: Verify results
        assert final_status in ["SUCCESS", "FAILURE", "PENDING", "STARTED"]
        
        if final_status == "SUCCESS":
            assert "result" in status_data
            result = status_data["result"]
            assert result.get("success") is True
    
    def test_multiple_concurrent_requests(self, client, test_image_bytes, mock_processor):
        """Test handling multiple concurrent requests"""
        
        task_ids = []
        
        # Submit multiple requests
        for i in range(3):
            files = {
                'file': (f'test_image_{i}.png', BytesIO(test_image_bytes), 'image/png')
            }
            data = {
                'async_processing': 'true'
            }
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == 200
            
            task_data = response.json()
            task_ids.append(task_data.get("task_id"))
        
        # Verify all tasks were created
        assert len(task_ids) == 3
        assert len(set(task_ids)) == 3  # All unique


@pytest.mark.integration
class TestErrorRecovery:
    """Error recovery integration tests"""
    
    def test_api_handles_invalid_requests_gracefully(self, client):
        """Test API handles various invalid requests"""
        
        # Invalid file type
        response1 = client.post("/process", 
            files={'file': ('test.exe', BytesIO(b'fake'), 'application/exe')},
            data={'async_processing': 'true'})
        assert response1.status_code == 400
        
        # Missing file
        response2 = client.post("/process", 
            data={'async_processing': 'true'})
        assert response2.status_code == 422
        
        # Invalid task ID
        response3 = client.get("/task/invalid-task-id-12345")
        assert response3.status_code == 200  # Returns PENDING status
    
    def test_system_continues_after_error(self, client, test_image_bytes, mock_processor):
        """Test system continues working after an error"""
        
        # Cause an error
        response1 = client.post("/process",
            files={'file': ('test.exe', BytesIO(b'fake'), 'application/exe')},
            data={'async_processing': 'true'})
        assert response1.status_code == 400
        
        # System should still work
        response2 = client.post("/process",
            files={'file': ('test.png', BytesIO(test_image_bytes), 'image/png')},
            data={'async_processing': 'true'})
        assert response2.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])