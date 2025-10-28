"""
Utility script to generate test images with grammatical mistakes
Can be run independently to create test images
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def generate_test_image_with_grammar_errors(filename: str, text_with_errors: str, output_dir: str = "tests/input_images") -> str:
    """
    Generate a test image containing text with grammatical mistakes
    
    Args:
        filename: Name of the image file to create
        text_with_errors: Text containing grammatical mistakes
        output_dir: Directory to save the image
        
    Returns:
        Path to the generated image file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
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
    image_path = Path(output_dir) / filename
    img.save(image_path, format='PNG')
    
    print(f"Generated test image: {image_path}")
    return str(image_path)


def main():
    """Generate multiple test images with different grammatical errors"""
    
    test_cases = [
        {
            "filename": "test_grammar_errors_1.png",
            "text": "This are a test sentence with grammar error. It dont work properly."
        },
        {
            "filename": "test_grammar_errors_2.png", 
            "text": "The students was working on theyre homework. They havent finished yet."
        },
        {
            "filename": "test_grammar_errors_3.png",
            "text": "I recieved a email yesterday. The content was definately interesting."
        },
        {
            "filename": "test_grammar_errors_4.png",
            "text": "She dont know how to seperate the items. Its definately a problem."
        },
        {
            "filename": "test_grammar_errors_5.png",
            "text": "The team was working hard on theyre project. They havent completed it yet."
        }
    ]
    
    print("Generating test images with grammatical mistakes...")
    
    for test_case in test_cases:
        generate_test_image_with_grammar_errors(
            test_case["filename"], 
            test_case["text"]
        )
    
    print(f"\nGenerated {len(test_cases)} test images in tests/input_images/")


if __name__ == "__main__":
    main()
