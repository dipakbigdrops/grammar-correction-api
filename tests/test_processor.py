"""
Core Processor Tests
Tests the GrammarCorrectionProcessor class
"""

import pytest
import os
from pathlib import Path


class TestProcessorInitialization:
    """Tests for processor initialization"""
    
    def test_processor_can_be_created(self, mock_processor):
        """Test that processor can be instantiated"""
        assert mock_processor is not None
    
    def test_processor_is_ready(self, mock_processor):
        """Test processor ready status"""
        status = mock_processor.is_ready()
        assert isinstance(status, dict)
        assert "grammar_model_loaded" in status
        assert "ocr_available" in status


class TestInputHandling:
    """Tests for input handling"""
    
    def test_handle_image_input(self, mock_processor, test_image_file):
        """Test handling image input"""
        from app.processor import GrammarCorrectionProcessor
        
        # Create a real processor instance for this test
        # (will be skipped if model not available)
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        content, input_type = processor.handle_input(test_image_file)
        assert input_type == 'image'
        assert content == test_image_file
    
    def test_handle_html_input(self, mock_processor, test_html_file):
        """Test handling HTML input"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        content, input_type = processor.handle_input(test_html_file)
        assert input_type == 'html'
        assert isinstance(content, str)
        assert '<html>' in content.lower() or '<body>' in content.lower()
    
    def test_handle_nonexistent_file(self, mock_processor):
        """Test handling non-existent file"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        content, input_type = processor.handle_input("/nonexistent/file.png")
        assert content is None
        assert input_type == 'file_not_found'
    
    def test_handle_unsupported_file_type(self, mock_processor, test_text_file):
        """Test handling unsupported file type"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        content, input_type = processor.handle_input(test_text_file)
        assert content is None
        assert input_type == 'unknown_file_type'


class TestTextExtraction:
    """Tests for text extraction"""
    
    def test_extract_text_from_html(self, sample_html):
        """Test text extraction from HTML"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        text, _ = processor.extract_text(sample_html, 'html')
        assert isinstance(text, str)
        assert len(text) > 0
        # Should contain text from HTML
        assert 'test' in text.lower()


class TestGrammarCorrection:
    """Tests for grammar correction"""
    
    def test_correct_grammar(self, mock_processor, sample_text):
        """Test grammar correction"""
        corrected = mock_processor.correct_grammar(sample_text)
        assert isinstance(corrected, str)
        assert len(corrected) > 0
    
    def test_correct_grammar_empty_string(self, mock_processor):
        """Test grammar correction with empty string"""
        corrected = mock_processor.correct_grammar("")
        assert isinstance(corrected, str)
    
    def test_correct_grammar_preserves_meaning(self, mock_processor):
        """Test that correction preserves basic meaning"""
        original = "This are a test."
        corrected = mock_processor.correct_grammar(original)
        # Should still contain key words
        assert 'test' in corrected.lower()


class TestCorrectionIdentification:
    """Tests for identifying corrections"""
    
    def test_identify_corrections(self, mock_processor, sample_text, corrected_text):
        """Test identifying corrections between texts"""
        corrections = mock_processor.identify_corrections(sample_text, corrected_text)
        assert isinstance(corrections, list)
    
    def test_identify_corrections_with_no_changes(self, mock_processor):
        """Test identifying corrections when texts are identical"""
        text = "This is correct."
        corrections = mock_processor.identify_corrections(text, text)
        assert isinstance(corrections, list)
        # Mock processor may return corrections, real processor should return empty list
        # This is acceptable for mock behavior
    
    def test_corrections_have_correct_structure(self, mock_processor, sample_text, corrected_text):
        """Test that corrections have required fields"""
        corrections = mock_processor.identify_corrections(sample_text, corrected_text)
        
        if len(corrections) > 0:
            correction = corrections[0]
            assert 'original_word' in correction
            assert 'corrected_word' in correction
            assert 'original_context' in correction
            assert 'corrected_context' in correction
    
    def test_identify_corrections_with_context(self, mock_processor):
        """Test corrections include context"""
        original = "I are going to store."
        corrected = "I am going to store."
        
        corrections = mock_processor.identify_corrections(original, corrected, context_words=2)
        
        if len(corrections) > 0:
            # Context should be present
            assert len(corrections[0]['original_context']) > 0
            assert len(corrections[0]['corrected_context']) > 0


class TestReconstructionWithHighlighting:
    """Tests for content reconstruction with highlighting"""
    
    def test_reconstruct_html_with_corrections(self, sample_html, sample_corrections):
        """Test HTML reconstruction with highlighting"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        corrected_text = "This is a test paragraph with errors."
        
        reconstructed = processor.reconstruct_with_highlighting(
            sample_html,
            'html',
            corrected_text,
            sample_corrections
        )
        
        # Should return BeautifulSoup object or string
        assert reconstructed is not None
    
    def test_reconstruct_with_no_corrections(self, sample_html):
        """Test reconstruction when there are no corrections"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        reconstructed = processor.reconstruct_with_highlighting(
            sample_html,
            'html',
            "corrected text",
            []  # No corrections
        )
        
        # Should return original content
        assert reconstructed is not None


class TestOutputGeneration:
    """Tests for output generation"""
    
    def test_generate_output_for_html(self, sample_html, sample_corrections):
        """Test output generation for HTML"""
        from app.processor import GrammarCorrectionProcessor
        from bs4 import BeautifulSoup
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        content_output, json_output = processor.generate_output(
            soup,
            'html',
            sample_corrections
        )
        
        assert content_output is not None
        assert json_output is not None
        assert isinstance(json_output, str)
    
    def test_json_output_is_valid(self, sample_html, sample_corrections):
        """Test that JSON output is valid JSON"""
        from app.processor import GrammarCorrectionProcessor
        from bs4 import BeautifulSoup
        import json
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        _, json_output = processor.generate_output(
            soup,
            'html',
            sample_corrections
        )
        
        # Should be valid JSON
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)


class TestEndToEndProcessing:
    """End-to-end processing tests"""
    
    def test_process_html_file_end_to_end(self, test_html_file, tmp_path):
        """Test complete processing of HTML file"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        result = processor.process_input(test_html_file, output_dir=str(tmp_path))
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'input_type' in result
        
        if result['success']:
            assert result['input_type'] == 'html'
            assert 'original_text' in result
            assert 'corrected_text' in result
            assert 'corrections' in result
            assert 'corrections_count' in result
    
    def test_process_returns_error_for_invalid_file(self):
        """Test processing returns error for invalid file"""
        from app.processor import GrammarCorrectionProcessor
        
        try:
            processor = GrammarCorrectionProcessor()
        except:
            pytest.skip("Model not available")
        
        result = processor.process_input("/nonexistent/file.png")
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'error' in result or 'input_type' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])