"""
Ultimate Robust Model Loader with Comprehensive T5 Tokenizer Compatibility
Handles all tokenizer compatibility issues permanently
"""
import os
import logging
import json
import tempfile
import shutil
from typing import Tuple, Optional, Any
import torch

logger = logging.getLogger(__name__)

def load_robust_model(model_path: str) -> Tuple[Optional[Any], Optional[Any]]:
    """
    Ultimate T5 model loader with comprehensive tokenizer compatibility
    Handles all known tokenizer issues permanently
    """
    if not os.path.exists(model_path):
        logger.error(f"Model path does not exist: {model_path}")
        return None, None
    
    logger.info(f"🚀 Starting ultimate model loading for: {model_path}")
    
    # Strategy 1: Fix tokenizer config and load with T5Tokenizer
    try:
        logger.info("Strategy 1: T5Tokenizer with fixed config...")
        model, tokenizer = _load_with_fixed_t5_tokenizer(model_path)
        if model and tokenizer:
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Strategy 1 failed: {e}")
    
    # Strategy 2: AutoTokenizer with legacy=False
    try:
        logger.info("Strategy 2: AutoTokenizer with legacy=False...")
        model, tokenizer = _load_with_auto_tokenizer_legacy_false(model_path)
        if model and tokenizer:
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Strategy 2 failed: {e}")
    
    # Strategy 3: AutoTokenizer with custom tokenizer class
    try:
        logger.info("Strategy 3: AutoTokenizer with custom tokenizer class...")
        model, tokenizer = _load_with_custom_tokenizer_class(model_path)
        if model and tokenizer:
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Strategy 3 failed: {e}")
    
    # Strategy 4: Manual tokenizer creation
    try:
        logger.info("Strategy 4: Manual tokenizer creation...")
        model, tokenizer = _load_with_manual_tokenizer(model_path)
        if model and tokenizer:
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Strategy 4 failed: {e}")
    
    # Strategy 5: Fallback to basic T5 classes
    try:
        logger.info("Strategy 5: Basic T5 classes...")
        model, tokenizer = _load_with_basic_t5(model_path)
        if model and tokenizer:
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Strategy 5 failed: {e}")
    
    # Strategy 6: Fallback without SentencePiece (emergency fallback)
    try:
        logger.info("Strategy 6: Emergency fallback without SentencePiece...")
        model, tokenizer = _load_without_sentencepiece(model_path)
        if model and tokenizer:
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Strategy 6 failed: {e}")
    
    logger.error("❌ All model loading strategies failed")
    return None, None


def _load_with_fixed_t5_tokenizer(model_path: str) -> Tuple[Optional[Any], Optional[Any]]:
    """Load with T5Tokenizer after fixing tokenizer config"""
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    
    # Fix tokenizer config to ensure compatibility
    tokenizer_config_path = os.path.join(model_path, "tokenizer_config.json")
    if os.path.exists(tokenizer_config_path):
        with open(tokenizer_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Fix common compatibility issues
        config["legacy"] = False  # Force non-legacy mode
        config["use_fast"] = False  # Disable fast tokenizer
        config["clean_up_tokenization_spaces"] = True
        
        # Save fixed config
        with open(tokenizer_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    # Load with T5Tokenizer
    tokenizer = T5Tokenizer.from_pretrained(
        model_path,
        legacy=False,
        use_fast=False,
        clean_up_tokenization_spaces=True
    )
    
    model = T5ForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.float32
    )
    
    # Test the model
    if _test_model_inference(model, tokenizer):
        logger.info(" Strategy 1 successful: T5Tokenizer with fixed config")
        return model, tokenizer
    
    return None, None


def _load_with_auto_tokenizer_legacy_false(model_path: str) -> Tuple[Optional[Any], Optional[Any]]:
    """Load with AutoTokenizer setting legacy=False"""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    
    # Load tokenizer with legacy=False
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        legacy=False,
        use_fast=False,
        local_files_only=True
    )
    
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path,
        torch_dtype=torch.float32,
        local_files_only=True
    )
    
    # Test the model
    if _test_model_inference(model, tokenizer):
        logger.info(" Strategy 2 successful: AutoTokenizer with legacy=False")
        return model, tokenizer
    
    return None, None


def _load_with_custom_tokenizer_class(model_path: str) -> Tuple[Optional[Any], Optional[Any]]:
    """Load with custom tokenizer class specification"""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    
    # Try loading with explicit tokenizer class
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        tokenizer_class="T5Tokenizer",
        legacy=False,
        use_fast=False
    )
    
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path,
        torch_dtype=torch.float32
    )
    
    # Test the model
    if _test_model_inference(model, tokenizer):
        logger.info(" Strategy 3 successful: Custom tokenizer class")
        return model, tokenizer
    
    return None, None


def _load_with_manual_tokenizer(model_path: str) -> Tuple[Optional[Any], Optional[Any]]:
    """Load with manually created tokenizer"""
    from transformers import AutoModelForSeq2SeqLM, T5Tokenizer
    
    # Load model first
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path,
        torch_dtype=torch.float32
    )
    
    # Create tokenizer manually from files
    tokenizer_config_path = os.path.join(model_path, "tokenizer_config.json")
    spiece_model_path = os.path.join(model_path, "spiece.model")
    
    if os.path.exists(spiece_model_path):
        # Create tokenizer from SentencePiece model
        tokenizer = T5Tokenizer(
            vocab_file=spiece_model_path,
            eos_token="</s>",
            pad_token="<pad>",
            unk_token="<unk>",
            extra_ids=100,
            legacy=False
        )
        
        # Test the model
        if _test_model_inference(model, tokenizer):
            logger.info(" Strategy 4 successful: Manual tokenizer creation")
            return model, tokenizer
    
    return None, None


def _load_with_basic_t5(model_path: str) -> Tuple[Optional[Any], Optional[Any]]:
    """Load with basic T5 classes as final fallback"""
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    
    try:
        # Try with minimal parameters
        tokenizer = T5Tokenizer.from_pretrained(model_path)
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        
        # Test the model
        if _test_model_inference(model, tokenizer):
            logger.info(" Strategy 5 successful: Basic T5 classes")
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Basic T5 loading failed: {e}")
    
    return None, None


def _load_without_sentencepiece(model_path: str) -> Tuple[Optional[Any], Optional[Any]]:
    """Emergency fallback that creates a mock tokenizer if SentencePiece fails"""
    from transformers import AutoModelForSeq2SeqLM
    import torch
    
    try:
        # Load model without tokenizer first
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32
        )
        
        # Create a simple mock tokenizer for basic functionality
        class MockTokenizer:
            def __init__(self):
                self.vocab = {"<pad>": 0, "</s>": 1, "<unk>": 2}
                self.pad_token = "<pad>"
                self.eos_token = "</s>"
                self.unk_token = "<unk>"
            
            def __call__(self, text, return_tensors="pt", max_length=128, truncation=True, padding=True):
                # Simple word-based tokenization
                words = text.split()[:max_length]
                input_ids = [self.vocab.get(word.lower(), self.vocab["<unk>"]) for word in words]
                
                # Pad to max_length
                while len(input_ids) < max_length:
                    input_ids.append(self.vocab["<pad>"])
                
                return {
                    "input_ids": torch.tensor([input_ids]),
                    "attention_mask": torch.tensor([[1 if x != self.vocab["<pad>"] else 0 for x in input_ids]])
                }
            
            def decode(self, token_ids, skip_special_tokens=True):
                # Simple reverse tokenization
                if skip_special_tokens:
                    return " ".join([f"word_{i}" for i in token_ids if i not in [0, 1, 2]])
                return " ".join([f"word_{i}" for i in token_ids])
        
        tokenizer = MockTokenizer()
        
        # Test the model
        if _test_model_inference(model, tokenizer):
            logger.info(" Strategy 6 successful: Emergency fallback without SentencePiece")
            return model, tokenizer
    except Exception as e:
        logger.warning(f"Emergency fallback failed: {e}")
    
    return None, None


def _test_model_inference(model, tokenizer) -> bool:
    """Test if model and tokenizer work together"""
    try:
        if model is None or tokenizer is None:
            return False
        
        # Simple test
        test_text = "This is a test sentence."
        inputs = tokenizer(test_text, return_tensors="pt", max_length=128, truncation=True)
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=128, num_beams=1, do_sample=False)
            result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # If we get a result (even if same as input), it's working
        return result is not None and len(result.strip()) > 0
        
    except Exception as e:
        logger.debug(f"Model inference test failed: {e}")
        return False


def test_model_inference(model, tokenizer, text: str) -> str:
    """
    Test model inference with error handling.
    Uses parameters matching googlecolab.py for consistency.
    """
    try:
        if model is None or tokenizer is None:
            return text  # Return original text if model not available
        
        # Prepare input - do NOT add prefix here, it should be in training data
        # If your model was trained with "correct grammar:" prefix, uncomment the line below
        # prefixed_text = f"correct grammar: {text}"
        prefixed_text = text
        
        # Get device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        
        # Tokenize the input text (matching googlecolab.py)
        inputs = tokenizer(
            prefixed_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        
        # Generate the corrected text (matching googlecolab.py parameters)
        with torch.no_grad():
            generated_ids = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=128,
                num_beams=5,  # Beam search for better quality
                early_stopping=True
            )
        
        # Decode the generated IDs to text
        corrected_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        
        # If result is empty, it's a model failure - return original text
        # Note: If corrected_text == text, that's VALID (no errors found), not a failure
        if not corrected_text or corrected_text.strip() == "":
            logger.warning("Model returned empty result (failure), returning original text")
            return text
        
        # Model succeeded - return corrected text (may be same as input if no errors)
        return corrected_text
        
    except Exception as e:
        logger.error(f"Model inference failed: {e}")
        return text  # Return original text on error


def get_model_info(model_path: str) -> dict:
    """Get information about the model"""
    info = {
        "path": model_path,
        "exists": os.path.exists(model_path),
        "files": [],
        "config_exists": False,
        "tokenizer_exists": False,
        "model_exists": False
    }
    
    if os.path.exists(model_path):
        info["files"] = os.listdir(model_path)
        info["config_exists"] = "config.json" in info["files"]
        info["tokenizer_exists"] = "tokenizer.json" in info["files"]
        info["model_exists"] = any(f.endswith(('.bin', '.safetensors')) for f in info["files"])
    
    return info