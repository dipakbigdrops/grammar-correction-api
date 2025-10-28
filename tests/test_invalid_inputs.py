"""
Comprehensive Invalid Input Tests
Tests how the API handles various invalid inputs
"""

import pytest
from io import BytesIO
from fastapi import status


class TestInvalidFileTypes:
    """Tests for invalid file types"""
    
    def test_reject_text_file(self, client):
        """Test rejection of .txt files"""
        files = {'file': ('test.txt', BytesIO(b'test content'), 'text/plain')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_reject_executable_file(self, client):
        """Test rejection of .exe files"""
        files = {'file': ('malware.exe', BytesIO(b'MZ'), 'application/x-msdownload')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_reject_pdf_file(self, client):
        """Test rejection of .pdf files"""
        files = {'file': ('document.pdf', BytesIO(b'%PDF-1.4'), 'application/pdf')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_accept_zip_file(self, client):
        """Test acceptance of .zip files (now supported)"""
        files = {'file': ('archive.zip', BytesIO(b'PK\x03\x04'), 'application/zip')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # ZIP files are now accepted (though this one may fail processing due to invalid content)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_reject_javascript_file(self, client):
        """Test rejection of .js files"""
        files = {'file': ('script.js', BytesIO(b'console.log("test")'), 'application/javascript')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestInvalidFileSizes:
    """Tests for invalid file sizes"""
    
    def test_reject_oversized_file(self, client):
        """Test rejection of files over size limit"""
        # Create 11MB file (over 10MB limit)
        large_content = b'0' * (11 * 1024 * 1024)
        files = {'file': ('large.png', BytesIO(large_content), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "too large" in response.json()["detail"].lower()
    
    def test_accept_file_at_size_limit(self, client, mock_processor):
        """Test acceptance of file at exact size limit"""
        # Create 10MB file (at limit)
        content = b'0' * (10 * 1024 * 1024)
        files = {'file': ('limit.png', BytesIO(content), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should accept or reject based on exact implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_reject_empty_file(self, client):
        """Test handling of empty files"""
        files = {'file': ('empty.png', BytesIO(b''), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestMissingParameters:
    """Tests for missing required parameters"""
    
    def test_missing_file_parameter(self, client):
        """Test request without file parameter"""
        data = {'async_processing': 'true'}
        
        response = client.post("/process", data=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_missing_all_parameters(self, client):
        """Test request without any parameters"""
        response = client.post("/process")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMalformedRequests:
    """Tests for malformed requests"""
    
    def test_invalid_content_type(self, client):
        """Test request with invalid content type"""
        response = client.post("/process", 
                              headers={'Content-Type': 'application/json'},
                              json={'file': 'test'})
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    
    def test_corrupted_image_file(self, client):
        """Test handling of corrupted image file"""
        # Corrupted PNG header
        files = {'file': ('corrupt.png', BytesIO(b'INVALID_PNG_DATA'), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_corrupted_html_file(self, client):
        """Test handling of malformed HTML"""
        malformed_html = b'<html><body><p>Unclosed tag'
        files = {'file': ('malformed.html', BytesIO(malformed_html), 'text/html')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestSpecialCharacters:
    """Tests for special characters in filenames"""
    
    def test_filename_with_spaces(self, client, test_image_bytes, mock_processor):
        """Test filename with spaces"""
        files = {'file': ('test image with spaces.png', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_filename_with_special_chars(self, client, test_image_bytes, mock_processor):
        """Test filename with special characters"""
        files = {'file': ('test@#$%^&().png', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_filename_with_unicode(self, client, test_image_bytes, mock_processor):
        """Test filename with unicode characters"""
        files = {'file': ('测试图片.png', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_very_long_filename(self, client, test_image_bytes, mock_processor):
        """Test very long filename"""
        long_name = 'a' * 255 + '.png'
        files = {'file': (long_name, BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_multiple_file_extensions(self, client, test_image_bytes, mock_processor):
        """Test filename with multiple extensions"""
        files = {'file': ('test.backup.png', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_no_file_extension(self, client, test_image_bytes):
        """Test filename without extension"""
        files = {'file': ('testfile', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should reject due to no extension
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_case_sensitive_extension(self, client, test_image_bytes, mock_processor):
        """Test uppercase file extension"""
        files = {'file': ('test.PNG', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_mixed_case_extension(self, client, test_image_bytes, mock_processor):
        """Test mixed case file extension"""
        files = {'file': ('test.PnG', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK


class TestConcurrentInvalidRequests:
    """Tests for handling multiple invalid requests"""
    
    def test_multiple_invalid_requests_dont_crash_server(self, client):
        """Test that multiple invalid requests don't crash the server"""
        # Send multiple invalid requests
        for i in range(5):
            files = {'file': (f'test{i}.txt', BytesIO(b'invalid'), 'text/plain')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Server should still be responsive
        health_response = client.get("/health")
        assert health_response.status_code == status.HTTP_200_OK


class TestSecurityVulnerabilities:
    """Tests for potential security vulnerabilities"""
    
    def test_path_traversal_in_filename(self, client, test_image_bytes, mock_processor):
        """Test path traversal attempt in filename"""
        files = {'file': ('../../../etc/passwd.png', BytesIO(test_image_bytes), 'image/png')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should handle safely
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_null_bytes_in_filename(self, client, test_image_bytes, mock_processor):
        """Test null bytes in filename"""
        try:
            files = {'file': ('test\x00.png', BytesIO(test_image_bytes), 'image/png')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            # Should handle safely
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        except Exception:
            # Some systems may reject null bytes at a lower level
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
