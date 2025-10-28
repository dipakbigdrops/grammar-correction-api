"""
Celery Task Tests
Tests for async task processing
"""

import pytest
from unittest.mock import Mock, patch


class TestCeleryConfiguration:
    """Tests for Celery configuration"""
    
    def test_celery_app_exists(self):
        """Test that Celery app is configured"""
        from app.celery_app import celery_app
        assert celery_app is not None
    
    def test_celery_app_name(self):
        """Test Celery app has correct name"""
        from app.celery_app import celery_app
        assert celery_app.main == 'grammar_correction'
    
    def test_celery_config(self):
        """Test Celery configuration"""
        from app.celery_app import celery_app
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'


class TestProcessGrammarCorrectionTask:
    """Tests for process_grammar_correction task"""
    
    def test_task_is_registered(self):
        """Test that task is registered"""
        from app.celery_app import celery_app
        assert 'app.tasks.process_grammar_correction' in celery_app.tasks
    
    @patch('app.tasks.get_processor')
    def test_task_executes_successfully(self, mock_get_processor, test_html_file):
        """Test task executes successfully"""
        from app.tasks import process_grammar_correction
        
        # Mock processor
        mock_processor = Mock()
        mock_processor.process_input.return_value = {
            'success': True,
            'corrections_count': 1
        }
        mock_get_processor.return_value = mock_processor
        
        # Execute task synchronously (eager mode)
        result = process_grammar_correction.apply(args=[test_html_file, '/tmp']).get()
        
        assert result['success'] is True
    
    @patch('app.tasks.get_processor')
    def test_task_handles_errors(self, mock_get_processor):
        """Test task handles errors gracefully"""
        from app.tasks import process_grammar_correction
        
        # Mock processor to raise error
        mock_processor = Mock()
        mock_processor.process_input.side_effect = Exception("Test error")
        mock_get_processor.return_value = mock_processor
        
        # Task should handle the error
        result = process_grammar_correction.apply(args=['/nonexistent/file.png', '/tmp']).get()
        
        assert result['success'] is False
        assert 'error' in result


class TestHealthCheckTask:
    """Tests for health_check task"""
    
    def test_health_check_task_exists(self):
        """Test health check task is registered"""
        from app.celery_app import celery_app
        assert 'app.tasks.health_check' in celery_app.tasks
    
    def test_health_check_returns_status(self):
        """Test health check returns status"""
        from app.tasks import health_check
        
        result = health_check.apply().get()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] == 'healthy'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])