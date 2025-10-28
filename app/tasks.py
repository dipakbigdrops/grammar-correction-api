"""
Celery Tasks for Async Processing
"""
from celery import Task
from app.celery_app import celery_app
from app.processor import get_processor
import logging
import os
import time

logger = logging.getLogger(__name__)


class ProcessorTask(Task):
    """Base task with processor instance"""
    _processor = None
    
    @property
    def processor(self):
        if self._processor is None:
            logger.info("Initializing processor in worker")
            self._processor = get_processor()
        return self._processor


@celery_app.task(
    bind=True,
    base=ProcessorTask,
    name='app.tasks.process_grammar_correction',
    max_retries=3,
    default_retry_delay=60
)
def process_grammar_correction(self, input_file_path: str, output_dir: str = "/tmp"):
    """
    Async task to process grammar correction
    
    Args:
        input_file_path: Path to input file
        output_dir: Directory for output files
        
    Returns:
        Processing results dictionary
    """
    try:
        logger.info(f"Processing task {self.request.id} for file: {input_file_path}")
        
        # Update task state
        self.update_state(
            state='STARTED',
            meta={'status': 'Processing file...', 'progress': 10}
        )
        
        # Check if file exists
        if not os.path.exists(input_file_path):
            raise FileNotFoundError(f"Input file not found: {input_file_path}")
        
        # Process the file
        result = self.processor.process_input(input_file_path, output_dir=output_dir)
        
        if not result.get('success', False):
            raise Exception(result.get('error', 'Unknown processing error'))
        
        logger.info(f"Task {self.request.id} completed successfully")
        
        return result
    
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {e}", exc_info=True)
        
        # Retry on failure
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "success": False,
                "error": f"Max retries exceeded: {str(e)}",
                "task_id": self.request.id
            }


@celery_app.task(name='app.tasks.health_check')
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "timestamp": time.time()}