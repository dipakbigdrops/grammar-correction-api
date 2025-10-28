# -*- coding: utf-8 -*-
# This script is intended to be run in a standard Python environment (e.g., VS Code)
# Using EasyOCR for image processing due to persistent PaddleOCR issues in Colab

import os
import json
import re
import cv2
import numpy as np
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
# Removed Colab-specific imports: google.colab.files, google.colab.userdata
from difflib import Differ
# Removed sys import as PaddleOCR diagnostics are removed
# Removed PaddleOCR imports and related flags
# from paddleocr import PaddleOCR, draw_ocr

# Import EasyOCR
try:
    import easyocr
    easyocr_available = True
    print("EasyOCR imported.")
except ImportError as e:
    print(f"ImportError: Could not import EasyOCR. Please ensure EasyOCR is installed correctly. {e}")
    easyocr_available = False
except Exception as e:
    print(f"Unexpected error during EasyOCR import: {e}")
    easyocr_available = False


# Load the grammar correction model and tokenizer
# IMPORTANT: Update this path to the location of your saved model on your local machine
model_inference = None
tokenizer_inference = None
saved_model_path = "/content/drive/MyDrive/grammer_correction" # Example path: change to your model's directory
print(f"Loading grammar correction model from {saved_model_path}...")
try:
    if os.path.exists(saved_model_path):
        model_inference = AutoModelForSeq2SeqLM.from_pretrained(saved_model_path)
        tokenizer_inference = AutoTokenizer.from_pretrained(saved_model_path)
        print("Grammar correction model and tokenizer loaded successfully.")
    else:
        print(f"Error: Grammar correction model not found at {saved_model_path}.")
        print("Please update 'saved_model_path' to your model's location.")
except Exception as e:
    print(f"Error loading grammar correction model or tokenizer: {e}")


# Initialize EasyOCR reader (only if EasyOCR is available and not already initialized)
easyocr_reader_initialized = False
if easyocr_available:
     if 'reader' not in globals():
         print("Attempting to initialize EasyOCR reader...")
         try:
             # Initialize EasyOCR reader with desired languages
             reader = easyocr.Reader(['en']) # Specify languages here
             print("EasyOCR reader initialized successfully.")
             easyocr_reader_initialized = True
         except Exception as e:
             print(f"Error initializing EasyOCR reader: {e}")
             print("EasyOCR initialization failed. Image processing will be limited.")
             easyocr_reader_initialized = False
     else:
         print("EasyOCR reader is already initialized.")
         easyocr_reader_initialized = True # Assume initialized if variable exists
else:
    print("EasyOCR not available. Skipping reader initialization.")


def handle_input(input_source_path):
    """
    Handles input from a file path.

    Args:
        input_source_path (str): The path to the input file (image or HTML).

    Returns:
        tuple: A tuple containing the content of the input and its type ('image', 'html').
               For images, content will be the file path. For HTML, content will be the string.
               Returns (None, None) if the file is not found or type is unsupported.
    """
    if not os.path.isfile(input_source_path):
        print(f"Error: File not found at {input_source_path}")
        return None, 'file_not_found'

    file_extension = os.path.splitext(input_source_path)[1].lower()

    if file_extension in ['.jpg', '.png', '.jpeg']:
        return input_source_path, 'image' # For images, return the path to be read later
    elif file_extension in ['.html', '.htm']:
        try:
            with open(input_source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 'html'
        except Exception as e:
            print(f"Error reading HTML file {input_source_path}: {e}")
            return None, 'html_read_error'
    else:
        print(f"Unsupported file type: {file_extension}")
        return None, 'unknown_file_type'


def extract_text(content, input_type):
    """
    Extracts text and relevant structural/positional information from input.

    Args:
        content (str): The input content (file path for image, HTML string).
        input_type (str): The type of input ('image', 'html').

    Returns:
        tuple: A tuple containing the extracted text and structural/positional information.
               For 'image', returns (list of extracted text strings, list of EasyOCR results including bbox).
               For 'html', returns (extracted text string with structure preserved, None).
    """
    if input_type == 'image':
        if not easyocr_available or not easyocr_reader_initialized:
            print("EasyOCR is not available or not initialized. Cannot extract text from image.")
            return [], []

        # EasyOCR returns a list of tuples: (bbox, text, confidence)
        try:
            results = reader.readtext(content) # content is the image path
            extracted_texts = [item[1] for item in results] # Extract just the text
            # Return the full results list for image reconstruction (includes bboxes and confidence)
            return extracted_texts, results
        except Exception as e:
            print(f"Error during EasyOCR text extraction: {e}")
            return [], []


    elif input_type == 'html':
        # Use BeautifulSoup to parse HTML
        soup = BeautifulSoup(content, 'html.parser')

        # Extract text, preserving some structure by adding newlines for blocks
        extracted_text = ""
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'li']):
             extracted_text += element.get_text() + "\n"

        # Fallback for simple text extraction if no block elements are found
        if not extracted_text:
             extracted_text = soup.get_text()

        return extracted_text, None

    else:
        # Handle unknown or invalid input types
        print(f"Unsupported input type for extraction: {input_type}")
        return None, None

def correct_grammar(text):
    """
    Corrects the grammar of a given text using the loaded model.

    Args:
        text (str): The input text with potential grammar errors.

    Returns:
        str: The corrected text.
    """
    if model_inference is None or tokenizer_inference is None:
        return "Error: Grammar correction model not loaded."

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_inference.to(device)

    # Tokenize the input text
    inputs = tokenizer_inference(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    # Generate the corrected text
    with torch.no_grad():
        generated_ids = model_inference.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=128,
            num_beams=5,  # You can adjust this for different decoding strategies
            early_stopping=True
        )

    # Decode the generated IDs to text
    corrected_text = tokenizer_inference.decode(generated_ids[0], skip_special_tokens=True)

    return corrected_text

def identify_corrections(original_text, corrected_text, context_words=2):
    """
    Compares original and corrected text to identify changed words using sequence matching.
    Returns a list of dictionaries with change details, including original and corrected words
    and surrounding context.

    Args:
        original_text (str): The original text string.
        corrected_text (str): The corrected text string.
        context_words (int): The number of words to include as context before and after the change.

    Returns:
        list: A list of dictionaries, where each dictionary represents a change
              and contains 'original_word', 'corrected_word', 'original_context', and 'corrected_context'.
              Returns empty list if no changes are found.
    """
    # Tokenize including punctuation as separate tokens
    original_tokens_with_sep = re.findall(r'(\b\w+\b|\W+)', original_text)
    corrected_tokens_with_sep = re.findall(r'(\b\w+\b|\W+)', corrected_text)

    # Create lists of only words for diffing
    original_words = [token.lower() for token in original_tokens_with_sep if re.fullmatch(r'\b\w+\b', token)]
    corrected_words = [token.lower() for token in corrected_tokens_with_sep if re.fullmatch(r'\b\w+\b', token)]


    differ = Differ()
    # Diff based on words only for identifying changes
    diff = list(differ.compare(original_words, corrected_words))

    corrections = []
    original_buffer = []
    corrected_buffer = []

    # Keep track of the index in the original_words and corrected_words lists
    original_word_index = 0
    corrected_word_index = 0


    for item in diff:
        code = item[0]
        token = item[2:] # This is a word from original_words or corrected_words

        if code == '?':
            # Skip difference markers
            continue

        if code == '-':
            original_buffer.append(token)
            original_word_index += 1
        elif code == '+':
            corrected_buffer.append(token)
            corrected_word_index += 1
        elif code == ' ':
            # If tokens are the same, process any buffered changes before this
            # Pair up buffered tokens and add to corrections
            while original_buffer or corrected_buffer:
                orig = original_buffer.pop(0) if original_buffer else ''
                corr = corrected_buffer.pop(0) if corrected_buffer else ''
                # Only add to corrections if there's a change or non-empty insertion/deletion
                if orig != corr or (orig == '' and corr != '') or (orig != '' and corr == ''):
                    # Find the index of the original word in the original_words list
                    # This is a simplification and might not be perfect for complex changes
                    try:
                        if orig:
                            # Find the index of the *last* occurrence of the original word in the original_words list before the current index
                            # This is a heuristic to try and match the change location
                            orig_index_in_words = original_word_index - len(original_buffer) - 1 if original_buffer else original_word_index - 1
                            # Ensure index is within bounds
                            orig_index_in_words = max(0, orig_index_in_words)

                            # Get original context words
                            original_context_start = max(0, orig_index_in_words - context_words)
                            original_context_end = min(len(original_words), orig_index_in_words + len([orig]) + context_words) # Include the original word in context
                            original_context = " ".join(original_words[original_context_start:original_context_end])
                        else:
                            # For insertions, context is based on the corrected text position
                            # Find the index of the *last* occurrence of the corrected word in the corrected_words list before the current index
                            corr_index_in_words = corrected_word_index - len(corrected_buffer) - 1 if corrected_buffer else corrected_word_index - 1
                            corr_index_in_words = max(0, corr_index_in_words)

                            corrected_context_start = max(0, corr_index_in_words - context_words)
                            corrected_context_end = min(len(corrected_words), corr_index_in_words + len([corr]) + context_words)
                            original_context = " ".join(corrected_words[corrected_context_start:corrected_context_end]) # Use corrected context for insertions

                    except Exception as e:
                         print(f"Error getting original context for {orig}: {e}")
                         original_context = ""


                    # Get corrected context words (based on corrected_word_index)
                    try:
                         if corr:
                              corr_index_in_words = corrected_word_index - len(corrected_buffer) - 1 if corrected_buffer else corrected_word_index - 1
                              corr_index_in_words = max(0, corr_index_in_words)

                              corrected_context_start = max(0, corr_index_in_words - context_words)
                              corrected_context_end = min(len(corrected_words), corr_index_in_words + len([corr]) + context_words)
                              corrected_context = " ".join(corrected_words[corrected_context_start:corrected_context_end])
                         else:
                             # For deletions, context is based on the original text position
                             orig_index_in_words = original_word_index - len(original_buffer) - 1 if original_buffer else original_word_index - 1
                             orig_index_in_words = max(0, orig_index_in_words)

                             original_context_start = max(0, orig_index_in_words - context_words)
                             original_context_end = min(len(original_words), orig_index_in_words + len([orig]) + context_words)
                             corrected_context = " ".join(original_words[original_context_start:original_context_end]) # Use original context for deletions

                    except Exception as e:
                         print(f"Error getting corrected context for {corr}: {e}")
                         corrected_context = ""

                    corrections.append({
                        'original_word': orig.strip(),
                        'corrected_word': corr.strip(),
                        'original_context': original_context,
                        'corrected_context': corrected_context
                    })

            # Move indices forward for the matched token
            original_word_index += 1
            corrected_word_index += 1
            # Reset buffers
            original_buffer = []
            corrected_buffer = []

    # Process any remaining buffered changes at the end
    while original_buffer or corrected_buffer:
        orig = original_buffer.pop(0) if original_buffer else ''
        corr = corrected_buffer.pop(0) if corrected_buffer else ''
        if orig != corr or (orig == '' and corr != '') or (orig != '' and corr == ''):
            try:
                if orig:
                    orig_index_in_words = original_word_index - len(original_buffer) - 1 if original_buffer else original_word_index - 1
                    orig_index_in_words = max(0, orig_index_in_words)

                    original_context_start = max(0, orig_index_in_words - context_words)
                    original_context_end = min(len(original_words), orig_index_in_words + len([orig]) + context_words)
                    original_context = " ".join(original_words[original_context_start:original_context_end])
                else:
                    corr_index_in_words = corrected_word_index - len(corrected_buffer) - 1 if corrected_buffer else corrected_word_index - 1
                    corr_index_in_words = max(0, corr_index_in_words)

                    corrected_context_start = max(0, corr_index_in_words - context_words)
                    corrected_context_end = min(len(corrected_words), corr_index_in_words + len([corr]) + context_words)
                    original_context = " ".join(corrected_words[corrected_context_start:corrected_context_end])

            except Exception as e:
                print(f"Error getting original context for {orig} at end: {e}")
                original_context = ""

            try:
                if corr:
                    corr_index_in_words = corrected_word_index - len(corrected_buffer) - 1 if corrected_buffer else corrected_word_index - 1
                    corr_index_in_words = max(0, corr_index_in_words)

                    corrected_context_start = max(0, corr_index_in_words - context_words)
                    corrected_context_end = min(len(corrected_words), corr_index_in_words + len([corr]) + context_words)
                    corrected_context = " ".join(corrected_words[corrected_context_start:corrected_context_end])
                else:
                    orig_index_in_words = original_word_index - len(original_buffer) - 1 if original_buffer else original_word_index - 1
                    orig_index_in_words = max(0, orig_index_in_words)

                    original_context_start = max(0, orig_index_in_words - context_words)
                    original_context_end = min(len(original_words), orig_index_in_words + len([orig]) + context_words)
                    corrected_context = " ".join(original_words[original_context_start:original_context_end])

            except Exception as e:
                 print(f"Error getting corrected context for {corr} at end: {e}")
                 corrected_context = ""

            corrections.append({
                'original_word': orig.strip(),
                'corrected_word': corr.strip(),
                'original_context': original_context,
                'corrected_context': corrected_context
            })

    # Final filter: remove pairs where original and corrected are the same after stripping
    cleaned_corrections = [
        corr_dict for corr_dict in corrections
        if corr_dict['original_word'] != corr_dict['corrected_word']
        or (corr_dict['original_word'] == '' and corr_dict['corrected_word'] != '')
        or (corr_dict['original_word'] != '' and corr_dict['corrected_word'] == '')
    ]


    return cleaned_corrections


def reconstruct_with_highlighting(original_content, input_type, corrected_text, corrections, original_ocr_results=None):
    """
    Reconstructs the original content with highlighted corrections at the word level.

    Args:
        original_content (str): The original content (image path for image, HTML string for HTML).
        input_type (str): The type of input ('image', 'html').
        corrected_text (str): The grammar-corrected text string.
        original_ocr_results (list, optional): For image input, a list of EasyOCR results
                                               (bbox, text, confidence). Required for 'image' type.
        corrections (list): A list of dictionaries, where each dictionary represents a change
                            and contains 'original_word' and 'corrected_word'.

    Returns:
        object or str: The reconstructed content (Pillow Image for image, BeautifulSoup object or
                       string for HTML) with corrections highlighted,
                       or None if input type is invalid. Returns original content if no corrections.
                       For image, returns a Pillow Image object.
    """
    # Explicitly handle the case where no corrections are found
    if not corrections and input_type == 'image':
        print("No corrections identified for image. Returning original image.")
        try:
            # Return the original image loaded as a Pillow object from path
            return Image.open(original_content).convert("RGB")
        except Exception as e:
            print(f"Error loading original image for return: {e}")
            return None
    elif not corrections and input_type == 'html':
         print(f"No corrections identified for {input_type}. Returning original content.")
         return original_content # Return original HTML content string if no corrections


    # Proceed with highlighting only if corrections exist
    if input_type == 'image':
        if original_ocr_results is None:
            print("Error: original_ocr_results is required for image input.")
            return None

        try:
            # Load the original image using the path
            img = Image.open(original_content).convert("RGB")
            draw = ImageDraw.Draw(img)

            # Create a set of original words that were corrected for quick lookup
            # This set includes both the original word that was changed AND empty strings for insertions
            original_corrected_words_set = {
                corr_dict['original_word'].lower()
                for corr_dict in corrections
                if corr_dict['original_word'] != corr_dict['corrected_word'] # Ensure it's a change
            }

            # Set a confidence threshold for highlighting
            confidence_threshold = 0.5 # You can adjust this value

            # Iterate through the EasyOCR results (text blocks)
            for (bbox, text, confidence) in original_ocr_results:
                 # Only consider highlighting if confidence is above threshold
                 if confidence >= confidence_threshold:
                     # Get the bounding box coordinates (x1, y1, x2, y2) as integers
                     # EasyOCR bbox is [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] for the polygon
                     # We need min/max x and y for a simple rectangle highlight
                     x_coords = [int(p[0]) for p in bbox]
                     y_coords = [int(p[1]) for p in bbox]
                     x1, y1, x2, y2 = min(x_coords), min(y_coords), max(x_coords), max(y_coords)

                     # Attempt word-level highlighting within the bounding box
                     block_text = text # Use the original text from OCR
                     block_text_lower = block_text.lower()

                     # Iterate through the original words that were corrected
                     for original_word_lower in original_corrected_words_set:
                          # Find all occurrences of the original word within the block text
                          # Use regex to find whole words
                          for match in re.finditer(r'\b' + re.escape(original_word_lower) + r'\b', block_text_lower):
                               start_index = match.start()
                               word_length = len(match.group(0))

                               # Basic approximation for word position within the block
                               # This is still a simplification and depends heavily on uniform spacing
                               block_width = x2 - x1
                               char_width_approx = block_width / len(block_text) if len(block_text) > 0 else 0

                               word_x1 = x1 + (start_index * char_width_approx)
                               word_y1 = y1
                               word_x2 = word_x1 + (word_length * char_width_approx)
                               word_y2 = y2 # Assume same height as block

                               # Draw a highlight (e.g., red rectangle border) around the approximate word bounding box
                               draw.rectangle([(word_x1, word_y1), (word_x2, word_y2)], outline='red', width=2)

            return img # Return the PIL Image object

        except Exception as e:
            print(f"Error processing image for highlighting: {e}")
            return None

    elif input_type == 'html':
        try:
            soup = BeautifulSoup(original_content, 'html.parser')

            # Get all text nodes in the document
            text_nodes = soup.find_all(string=True)

            # Create a set of original words that were corrected for quick lookup
            original_corrected_words_set = {
                corr_dict['original_word'].lower()
                for corr_dict in corrections
                if corr_dict['original_word'] != corr_dict['corrected_word'] # Only include actual changes
            }

            # Iterate through text nodes and replace corrected words with highlighting
            for text_node in text_nodes:
                original_node_text = str(text_node) # Convert NavigableString to string
                parent = text_node.parent # Keep track of the parent element

                # Avoid modifying script or style tags
                if parent and parent.name in ['script', 'style']:
                    continue

                # Tokenize the text node while keeping separators
                # This regex splits on spaces and punctuation, keeping the separators
                tokens_and_separators = re.findall(r'(\b\w+\b|\W+)', original_node_text)

                new_content = []
                modified = False
                for item in tokens_and_separators:
                    # Check if the item is a word (alphanumeric)
                    if re.fullmatch(r'\b\w+\b', item):
                        word_lower = item.lower()
                        if word_lower in original_corrected_words_set:
                            # Wrap the original word in a <u> tag for highlighting
                            new_content.append(f'<u>{item}</u>')
                            modified = True
                        else:
                            new_content.append(item) # Keep original word if no correction
                    else:
                        new_content.append(item) # Keep separators (spaces, punctuation)

                # If the text node was modified, replace the old node with the new content
                if modified:
                    modified_node_text = "".join(new_content)
                    # Parse the modified text node string into BeautifulSoup objects.
                    new_soup_content = BeautifulSoup(modified_node_text, 'html.parser')

                    # Replace the string node's content with the new parsed content
                    text_node.replace_with(new_soup_content)

            # No need to add a style tag to the head when using <u>

            # Return the modified BeautifulSoup object
            return soup

        except Exception as e:
            print(f"Error processing HTML: {e}")
            return None

    else:
        print(f"Unknown input type: {input_type}")
        return None

def generate_output(reconstructed_content, input_type, corrections):
    """
    Generates the final output, including saving the reconstructed content
    and creating a JSON output of original-corrected word pairs with context.

    Args:
        reconstructed_content: The reconstructed content (Pillow Image object,
                               BeautifulSoup object or string).
        input_type (str): The type of input ('image', 'html').
        corrections (list): A list of dictionaries, where each dictionary represents a change
                            and contains 'original_word', 'corrected_word', 'original_context',
                            and 'corrected_context'.

    Returns:
        tuple: A tuple containing:
               - content_output: Path to saved image, HTML string.
               - json_output_string: A JSON formatted string of word pairs with context.
               Returns (None, None) if input type is invalid.
    """
    content_output = None

    if input_type == 'image':
        if isinstance(reconstructed_content, Image.Image):
            # Check if there were corrections before saving a new file
            if corrections: # Only save a new image if corrections were made
                output_image_path = "corrected_image_highlighted.png" # Save with a clear name
                try:
                    reconstructed_content.save(output_image_path)
                    content_output = output_image_path
                except Exception as e:
                    print(f"Error saving image: {e}")
                    content_output = None
            else:
                 # If no corrections, the reconstructed_content is the original image object
                 # We don't need to save a new file, just indicate no changes
                 content_output = "No corrections needed for the image. Original image not saved."
        else:
            print("Error: Reconstructed content for image type is not a Pillow Image.")
            content_output = None


    elif input_type == 'html':
        if hasattr(reconstructed_content, 'prettify'): # Check if it's a BeautifulSoup object
            content_output = reconstructed_content.prettify()
        elif isinstance(reconstructed_content, str): # Handle case where reconstruction might return string
             content_output = reconstructed_content
        else:
            print("Error: Reconstructed content for html type is not a BeautifulSoup object or string.")
            content_output = None

    else:
        print(f"Unknown input type: {input_type}")
        return None, None

    # Create the list of correction dictionaries for JSON output
    # The identify_corrections function now returns the desired list of dictionaries
    json_output_list = corrections

    # Convert the list of dictionaries to a JSON formatted string
    try:
        json_output_string = json.dumps(json_output_list, indent=4)
    except Exception as e:
        print(f"Error generating JSON output: {e}")
        json_output_string = "[]" # Return empty JSON list in case of error

    return content_output, json_output_string


def process_input(input_source_path):
    """
    End-to-end script to process input from a file path, correct grammar, and generate output.

    Args:
        input_source_path (str): The path to the input file (image or HTML).

    Returns:
        tuple: A tuple containing:
               - content_output: Path to saved image, HTML string.
               - json_output_string: A JSON formatted string of word pairs with context.
               Returns (None, None) if processing fails.
    """
    # 1. Handle input
    original_content, input_type = handle_input(input_source_path)

    if original_content is None:
        print("Failed to handle input.")
        return None, None

    print(f"Input type detected: {input_type}")

    # 2. Extract text and positional info
    if input_type == 'image':
        # Pass the file path for EasyOCR
        extracted_texts, original_ocr_results = extract_text(original_content, input_type)
        # For grammar correction, join the extracted texts
        text_to_correct = " ".join(extracted_texts) if extracted_texts else ""
        original_content_for_reconstruct = original_content # Pass image path
    elif input_type == 'html':
        extracted_text, _ = extract_text(original_content, input_type)
        text_to_correct = extracted_text if extracted_text else ""
        original_ocr_results = None # Not applicable for HTML
        original_content_for_reconstruct = original_content # Pass HTML string
    else:
        print("Unsupported input type for text extraction.")
        return None, None

    if not text_to_correct:
        print("No text extracted from the input.")
        # If no text is extracted from an image, we still need to handle the image output
        if input_type == 'image':
            print("Returning original image as no text was extracted.")
            try:
                 original_img = Image.open(original_content).convert("RGB")
                 # Return the original image object and empty JSON
                 return original_img, "[]" # Return empty list JSON
            except Exception as e:
                 print(f"Error loading original image when no text extracted: {e}")
                 return None, "[]" # Return empty list JSON
        else:
            # For HTML with no extracted text, return original content and empty JSON
             return original_content, "[]" # Return empty list JSON


    print("Extracted text:")
    print(text_to_correct[:200] + "..." if len(text_to_correct) > 200 else text_to_correct)


    # 3. Correct grammar
    corrected_text = correct_grammar(text_to_correct)

    if corrected_text == "Error: Grammar correction model not loaded.":
        print(corrected_text)
        return None, None

    print("Corrected text:")
    print(corrected_text[:200] + "..." if len(corrected_text) > 200 else corrected_text)


    # 4. Identify corrections
    # For image input, use the concatenated original text for comparison
    if input_type == 'image':
         original_text_for_comparison = " ".join(extracted_texts) if extracted_texts else ""
    elif input_type == 'html':
         original_text_for_comparison = extracted_text # For HTML, it's the extracted text with structure
    else: # Should not happen with current handle_input
         original_text_for_comparison = text_to_correct


    # Identify corrections with context
    corrections = identify_corrections(original_text_for_comparison, corrected_text, context_words=3) # Increased context words to 3


    print("Identified corrections:", corrections)

    # 5. Reconstruct with highlighting (or replacement for HTML)
    reconstructed_content = reconstruct_with_highlighting(
        original_content_for_reconstruct, # Pass HTML string or image path
        input_type,
        corrected_text,
        corrections,
        original_ocr_results=original_ocr_results if input_type == 'image' else None # Pass OCR results only for image
    )

    if reconstructed_content is None and corrections: # If reconstruction failed but corrections were found
        print("Failed to reconstruct content with highlighting/replacement, but corrections were found.")
        # Still generate JSON output
        json_output_string = json.dumps(corrections, indent=4) # Use the list of dictionaries directly
        return None, json_output_string
    elif reconstructed_content is None and not corrections: # If reconstruction failed and no corrections were found
         print("Failed to reconstruct content and no corrections were found.")
         return None, "[]" # Return empty JSON list


    # 6. Generate output
    content_output, json_output_string = generate_output(reconstructed_content, input_type, corrections)

    return content_output, json_output_string

# Example Usage (for VS Code/local environment):
if __name__ == "__main__":
    # You would typically get the input file path from command-line arguments
    # or a configuration file in a real application.
    # For demonstration, replace with your file paths:
    # input_file = "./sample_image.png" # Path to your image file
    # input_file = "./sample.html"     # Path to your HTML file

    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_content, output_json = process_input(input_file)

        print("\n--- Final Output ---")
        if output_content:
            if isinstance(output_content, str) and (output_content.lower().endswith('.png') or output_content.lower().endswith('.html')):
                 print(f"Processed output saved/generated: {output_content}")
            elif isinstance(output_content, Image.Image):
                 # Save PIL Image for image output if not already saved
                 output_path = "processed_image_output.png"
                 try:
                     output_content.save(output_path)
                     print(f"Processed image output saved to: {output_path}")
                 except Exception as e:
                     print(f"Error saving processed image: {e}")
            elif isinstance(output_content, str): # Handle HTML string output
                 output_path = "processed_document_output.html"
                 try:
                     with open(output_path, "w", encoding="utf-8") as f:
                         f.write(output_content)
                     print(f"Processed HTML output saved to: {output_path}")
                 except Exception as e:
                     print(f"Error saving processed HTML: {e}")
            else:
                 print("Processed Content:\n", output_content) # Fallback print for other types
        else:
            print("No processed content generated.")

        print("\nCorrections JSON:\n", output_json)

    else:
        print("Please provide the path to your input file as a command-line argument.")
        print("Example: python your_script_name.py /path/to/your/image.png")
        print("Example: python your_script_name.py /path/to/your/document.html")

    # Note: For interactive testing in a script, you might manually set input_file
    # input_file = "/path/to/your/test_image.png"
    # output_content, output_json = process_input(input_file)
    # print("\n--- Final Output ---")
    # if isinstance(output_content, Image.Image):
    #      output_path = "processed_image_output_manual_test.png"
    #      output_content.save(output_path)
    #      print(f"Processed image output saved to: {output_path}")
    # elif isinstance(output_content, str):
    #       print("Processed Content:\n", output_content)
    # else:
    #       print("Processed Content:", output_content)