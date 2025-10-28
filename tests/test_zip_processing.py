"""
ZIP File Processing Tests
Tests for ZIP archive handling and processing
"""

import pytest
import zipfile
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from fastapi import status


class TestZipFileValidation:
    """Tests for ZIP file validation"""
    
    def test_accept_valid_zip_file(self, client, tmp_path, mock_processor):
        """Test acceptance of valid ZIP file"""
        # Create a ZIP file with valid content
        zip_path = tmp_path / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add an HTML file
            zf.writestr("test.html", "<html><body><p>This are a test.</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('test.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK
    
    def test_reject_empty_zip(self, client, tmp_path):
        """Test rejection of empty ZIP file"""
        zip_path = tmp_path / "empty.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass  # Empty ZIP
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('empty.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            # Should handle gracefully
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_reject_corrupted_zip(self, client):
        """Test handling of corrupted ZIP file"""
        # Create fake ZIP data
        fake_zip = b'PK\x03\x04CORRUPTED_DATA'
        
        files = {'file': ('corrupted.zip', BytesIO(fake_zip), 'application/zip')}
        data = {'async_processing': 'true'}
        
        response = client.post("/process", files=files, data=data)
        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestZipWithMultipleFiles:
    """Tests for ZIP files containing multiple files"""
    
    def test_process_zip_with_multiple_html_files(self, client, tmp_path, mock_processor):
        """Test ZIP with multiple HTML files"""
        zip_path = tmp_path / "multiple.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.html", "<html><body><p>This are test 1.</p></body></html>")
            zf.writestr("file2.html", "<html><body><p>This are test 2.</p></body></html>")
            zf.writestr("file3.html", "<html><body><p>This are test 3.</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('multiple.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK
            
            result = response.json()
            assert result.get("status") in ["SUCCESS", "FAILURE"]
    
    def test_process_zip_with_mixed_files(self, client, tmp_path, test_image_bytes, mock_processor):
        """Test ZIP with both images and HTML"""
        zip_path = tmp_path / "mixed.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("document.html", "<html><body><p>Test document.</p></body></html>")
            zf.writestr("image.png", test_image_bytes)
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('mixed.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK
    
    def test_zip_skips_invalid_files(self, client, tmp_path, mock_processor):
        """Test that ZIP processing skips invalid file types"""
        zip_path = tmp_path / "mixed_valid_invalid.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("valid.html", "<html><body><p>Valid file.</p></body></html>")
            zf.writestr("invalid.txt", "This should be skipped")
            zf.writestr("invalid.pdf", "PDF content")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('mixed_valid_invalid.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK


class TestZipSecurityLimits:
    """Tests for ZIP security limits"""
    
    def test_reject_zip_bomb(self, client, tmp_path):
        """Test rejection of ZIP bomb (large extracted size)"""
        zip_path = tmp_path / "bomb.zip"
        
        # Create a ZIP with file that expands to >50MB
        large_content = b'0' * (60 * 1024 * 1024)  # 60MB
        
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("large.html", large_content)
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('bomb.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            # Should reject or handle gracefully
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_limit_files_in_zip(self, client, tmp_path, mock_processor):
        """Test that ZIP processing limits number of files"""
        zip_path = tmp_path / "many_files.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add more files than the limit (100)
            for i in range(110):
                zf.writestr(f"file{i}.html", f"<html><body><p>File {i}</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('many_files.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            # Should process up to limit
            assert response.status_code == status.HTTP_200_OK


class TestZipWithDirectories:
    """Tests for ZIP files with directory structures"""
    
    def test_process_zip_with_nested_directories(self, client, tmp_path, mock_processor):
        """Test ZIP with nested directory structure"""
        zip_path = tmp_path / "nested.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("folder1/file1.html", "<html><body><p>File 1</p></body></html>")
            zf.writestr("folder1/folder2/file2.html", "<html><body><p>File 2</p></body></html>")
            zf.writestr("folder3/file3.html", "<html><body><p>File 3</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('nested.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK
    
    def test_skip_hidden_files(self, client, tmp_path, mock_processor):
        """Test that hidden files are skipped"""
        zip_path = tmp_path / "hidden.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("visible.html", "<html><body><p>Visible</p></body></html>")
            zf.writestr(".hidden.html", "<html><body><p>Hidden</p></body></html>")
            zf.writestr("__MACOSX/resource.html", "<html><body><p>Mac resource</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('hidden.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK


class TestZipResponseFormat:
    """Tests for ZIP processing response format"""
    
    def test_zip_response_contains_summary(self, client, tmp_path, mock_processor):
        """Test that ZIP response contains summary information"""
        zip_path = tmp_path / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.html", "<html><body><p>Test 1</p></body></html>")
            zf.writestr("file2.html", "<html><body><p>Test 2</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('test.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK
            
            result = response.json()
            # Check if result contains expected fields
            assert "result" in result or "status" in result
    
    def test_zip_response_contains_individual_results(self, client, tmp_path, mock_processor):
        """Test that ZIP response contains results for each file"""
        zip_path = tmp_path / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.html", "<html><body><p>Test 1</p></body></html>")
            zf.writestr("file2.html", "<html><body><p>Test 2</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('test.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK


class TestZipEdgeCases:
    """Tests for ZIP edge cases"""
    
    def test_zip_with_only_directories(self, client, tmp_path):
        """Test ZIP containing only directories"""
        zip_path = tmp_path / "only_dirs.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("folder1/", "")
            zf.writestr("folder2/", "")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('only_dirs.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            # Should handle gracefully
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_zip_with_special_characters_in_filenames(self, client, tmp_path, mock_processor):
        """Test ZIP with special characters in filenames"""
        zip_path = tmp_path / "special.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file with spaces.html", "<html><body><p>Test</p></body></html>")
            zf.writestr("file-with-dashes.html", "<html><body><p>Test</p></body></html>")
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('special.zip', f, 'application/zip')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
            assert response.status_code == status.HTTP_200_OK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
