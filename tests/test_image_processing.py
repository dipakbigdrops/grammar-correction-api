"""
Comprehensive Image Processing Test
Tests the complete image processing pipeline including:
1. Generating test images with grammatical mistakes
2. Processing through API
3. Converting base64 output to standard images
4. Saving results to test directory
"""

import pytest
import os
import base64
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
from fastapi.testclient import TestClient


class TestImageProcessingPipeline:
    """Comprehensive test for image processing pipeline"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = Path("tests")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for test outputs
        self.input_dir = self.test_dir / "input_images"
        self.output_dir = self.test_dir / "output_images"
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_test_image_with_grammar_errors(self, filename: str, text_with_errors: str) -> str:
        """
        Generate a test image containing text with grammatical mistakes
        
        Args:
            filename: Name of the image file to create
            text_with_errors: Text containing grammatical mistakes
            
        Returns:
            Path to the generated image file
        """
        # Create image with white background
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a system font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            try:
                # Try Windows font
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
        
        # Draw text with grammar errors
        draw.text((50, 150), text_with_errors, fill='black', font=font)
        
        # Save image
        image_path = self.input_dir / filename
        img.save(image_path, format='PNG')
        
        print(f"Generated test image: {image_path}")
        return str(image_path)
    
    def test_image_processing_pipeline(self, client: TestClient):
        """Test complete image processing pipeline"""
        
        # Test cases with different grammatical errors
        # Note: OCR may not detect all text perfectly, so we focus on basic functionality
        from tests.test_constants import TEST_CASES_WITH_EXPECTATIONS
        test_cases = TEST_CASES_WITH_EXPECTATIONS
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            print(f"\n--- Processing Test Case {i+1}: {test_case['filename']} ---")
            
            # 1. Generate test image with grammar errors
            image_path = self.generate_test_image_with_grammar_errors(
                test_case["filename"], 
                test_case["text"]
            )
            
            # 2. Process image through API
            with open(image_path, 'rb') as f:
                files = {'file': (test_case["filename"], f, 'image/png')}
                data = {'async_processing': 'true'}
                
                response = client.post("/process", files=files, data=data)
            
            # 3. Verify API response
            assert response.status_code == 200, f"API request failed: {response.text}"
            
            result = response.json()
            assert result["status"] in ["SUCCESS", "FAILURE"], f"Unexpected status: {result['status']}"
            
            if result["status"] == "SUCCESS":
                # 4. Extract and process results
                api_result = result["result"]
                
                # Save original text
                original_text = api_result.get("original_text", "")
                corrected_text = api_result.get("corrected_text", "")
                corrections = api_result.get("corrections", [])
                output_content = api_result.get("output_content", "")
                
                # 5. Convert base64 image to standard image and save
                if output_content and output_content.startswith("data:image"):
                    # Extract base64 data
                    base64_data = output_content.split(",")[1]
                    image_data = base64.b64decode(base64_data)
                    
                    # Save reconstructed image
                    reconstructed_path = self.output_dir / f"reconstructed_{test_case['filename']}"
                    with open(reconstructed_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"Saved reconstructed image: {reconstructed_path}")
                else:
                    print("No base64 image output received")
                    reconstructed_path = None
                
                # 6. Save detailed results
                test_result = {
                    "test_case": i + 1,
                    "filename": test_case["filename"],
                    "original_text": original_text,
                    "corrected_text": corrected_text,
                    "corrections": corrections,
                    "corrections_count": len(corrections),
                    "processing_time": api_result.get("processing_time_seconds", 0),
                    "reconstructed_image_path": str(reconstructed_path) if reconstructed_path else None,
                    "api_response": result
                }
                
                results.append(test_result)
                
                # 7. Verify corrections were made
                print(f"Original text: {original_text}")
                print(f"Corrected text: {corrected_text}")
                print(f"Corrections made: {len(corrections)}")
                
                for correction in corrections:
                    print(f"  - '{correction.get('original_word', '')}' -> '{correction.get('corrected_word', '')}'")
                
                # Verify that some corrections were made
                assert len(corrections) > 0, f"No corrections made for test case {i+1}"
                
                # Verify that at least some expected error words were corrected
                corrected_words = [corr.get('original_word', '').lower() for corr in corrections]
                corrected_count = sum(1 for expected_error in test_case["expected_corrections"] 
                                    if expected_error.lower() in corrected_words)
                assert corrected_count > 0, f"None of the expected errors {test_case['expected_corrections']} were corrected. Found corrections: {corrected_words}"
            
            else:
                print(f"API processing failed: {result.get('message', 'Unknown error')}")
                results.append({
                    "test_case": i + 1,
                    "filename": test_case["filename"],
                    "error": result.get("message", "Unknown error"),
                    "api_response": result
                })
        
        # 8. Save comprehensive test results
        results_file = self.test_dir / "image_processing_test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n--- Test Results Summary ---")
        print(f"Total test cases: {len(test_cases)}")
        print(f"Successful processing: {len([r for r in results if 'error' not in r])}")
        print(f"Failed processing: {len([r for r in results if 'error' in r])}")
        print(f"Results saved to: {results_file}")
        
        # Verify at least one test case succeeded
        successful_cases = [r for r in results if 'error' not in r]
        assert len(successful_cases) > 0, "No test cases processed successfully"
    
    def test_image_processing_with_real_api(self):
        """Test image processing with real API (if running)"""
        # This test can be run when the API is actually running
        # Uncomment and modify the URL as needed
        
        # api_url = "http://localhost:8000/process"
        # 
        # # Generate test image
        # image_path = self.generate_test_image_with_grammar_errors(
        #     "real_api_test.png",
        #     "This are a test for real API processing."
        # )
        # 
        # # Send request to real API
        # with open(image_path, 'rb') as f:
        #     files = {'file': (image_path, f, 'image/png')}
        #     data = {'async_processing': 'true'}
        #     
        #     response = requests.post(api_url, files=files, data=data)
        # 
        # assert response.status_code == 200
        # result = response.json()
        # print(f"Real API response: {result}")
        
        pytest.skip("Real API test skipped - uncomment to test with running API")
    
    def test_base64_image_conversion(self):
        """Test base64 image conversion functionality"""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        base64_string = f"data:image/png;base64,{img_base64}"
        
        # Convert back to image
        base64_data = base64_string.split(",")[1]
        image_data = base64.b64decode(base64_data)
        
        # Save converted image
        converted_path = self.output_dir / "base64_conversion_test.png"
        with open(converted_path, 'wb') as f:
            f.write(image_data)
        
        # Verify the image was saved correctly
        assert converted_path.exists()
        
        # Load and verify the image
        loaded_img = Image.open(converted_path)
        assert loaded_img.size == (100, 100)
        
        print(f"Base64 conversion test successful: {converted_path}")
    
    def test_image_processing_performance(self, client: TestClient):
        """Test image processing performance"""
        # Generate a larger test image
        large_text = "This are a test sentence with multiple grammar error. " * 10
        image_path = self.generate_test_image_with_grammar_errors(
            "performance_test.png",
            large_text
        )
        
        # Measure processing time
        start_time = time.time()
        
        with open(image_path, 'rb') as f:
            files = {'file': ('performance_test.png', f, 'image/png')}
            data = {'async_processing': 'true'}
            
            response = client.post("/process", files=files, data=data)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert response.status_code == 200
        result = response.json()
        
        if result["status"] == "SUCCESS":
            api_processing_time = result["result"].get("processing_time_seconds", 0)
            print(f"Total request time: {total_time:.2f}s")
            print(f"API processing time: {api_processing_time:.2f}s")
            
            # Performance should be reasonable (adjust threshold as needed)
            assert total_time < 30, f"Processing took too long: {total_time:.2f}s"
    
    def teardown_method(self):
        """Cleanup after tests"""
        # Optional: Clean up test files
        # Uncomment if you want to clean up after each test
        # import shutil
        # if self.input_dir.exists():
        #     shutil.rmtree(self.input_dir)
        # if self.output_dir.exists():
        #     shutil.rmtree(self.output_dir)
        pass
