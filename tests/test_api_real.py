"""
Real API Testing Script
Tests the API with actual HTTP requests and saves results
"""

import requests
import base64
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


class RealAPITester:
    """Test the API with real HTTP requests"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.test_dir = Path("tests")
        self.input_dir = self.test_dir / "input_images"
        self.output_dir = self.test_dir / "output_images"
        
        # Create directories
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_test_image(self, filename: str, text: str) -> str:
        """Generate a test image with text"""
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 150), text, fill='black', font=font)
        
        image_path = self.input_dir / filename
        img.save(image_path, format='PNG')
        return str(image_path)
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health")
            print(f"Health check status: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"Health data: {json.dumps(health_data, indent=2)}")
                return True
            else:
                print(f"Health check failed: {response.text}")
                return False
        except Exception as e:
            print(f"Health check error: {e}")
            return False
    
    def test_image_processing(self, image_path: str, test_name: str):
        """Test image processing with real API"""
        print(f"\n--- Testing {test_name} ---")
        
        try:
            # Send image to API
            with open(image_path, 'rb') as f:
                files = {'file': (image_path, f, 'image/png')}
                data = {'async_processing': 'true'}
                
                start_time = time.time()
                response = requests.post(f"{self.api_url}/process", files=files, data=data)
                end_time = time.time()
            
            print(f"Response status: {response.status_code}")
            print(f"Request time: {end_time - start_time:.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(f"API response: {json.dumps(result, indent=2)}")
                
                if result.get("status") == "SUCCESS":
                    api_result = result.get("result", {})
                    
                    # Extract results
                    original_text = api_result.get("original_text", "")
                    corrected_text = api_result.get("corrected_text", "")
                    corrections = api_result.get("corrections", [])
                    output_content = api_result.get("output_content", "")
                    
                    print(f"\nOriginal text: {original_text}")
                    print(f"Corrected text: {corrected_text}")
                    print(f"Corrections made: {len(corrections)}")
                    
                    for correction in corrections:
                        print(f"  - '{correction.get('original_word', '')}' -> '{correction.get('corrected_word', '')}'")
                    
                    # Save reconstructed image if available
                    if output_content and output_content.startswith("data:image"):
                        base64_data = output_content.split(",")[1]
                        image_data = base64.b64decode(base64_data)
                        
                        reconstructed_path = self.output_dir / f"reconstructed_{test_name}.png"
                        with open(reconstructed_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"Saved reconstructed image: {reconstructed_path}")
                    
                    return {
                        "success": True,
                        "original_text": original_text,
                        "corrected_text": corrected_text,
                        "corrections": corrections,
                        "processing_time": end_time - start_time
                    }
                else:
                    print(f"API processing failed: {result.get('message', 'Unknown error')}")
                    return {"success": False, "error": result.get("message", "Unknown error")}
            else:
                print(f"API request failed: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            print(f"Error testing {test_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def run_comprehensive_test(self):
        """Run comprehensive API tests"""
        print("Starting comprehensive API test...")
        
        # Test health endpoint first
        if not self.test_health_endpoint():
            print("Health check failed. Make sure the API is running.")
            return
        
        # Test cases
        test_cases = [
            {
                "name": "grammar_errors_1",
                "text": "This are a test sentence with grammar error. It dont work properly."
            },
            {
                "name": "grammar_errors_2",
                "text": "The students was working on theyre homework. They havent finished yet."
            },
            {
                "name": "grammar_errors_3",
                "text": "I recieved a email yesterday. The content was definately interesting."
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            # Generate test image
            image_path = self.generate_test_image(
                f"{test_case['name']}.png",
                test_case['text']
            )
            
            # Test with API
            result = self.test_image_processing(image_path, test_case['name'])
            result['test_name'] = test_case['name']
            result['text'] = test_case['text']
            results.append(result)
        
        # Save results
        results_file = self.test_dir / "real_api_test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n--- Test Results Summary ---")
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        print(f"Total tests: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Results saved to: {results_file}")
        
        if failed:
            print("\nFailed tests:")
            for result in failed:
                print(f"  - {result['test_name']}: {result.get('error', 'Unknown error')}")


def main():
    """Main function to run the tests"""
    import sys
    
    # Get API URL from command line or use default
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"Testing API at: {api_url}")
    
    tester = RealAPITester(api_url)
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
