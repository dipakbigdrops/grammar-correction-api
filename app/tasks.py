"""
Celery Tasks for Async Processing
"""
import logging
import os
import time

from celery import Task

from app.celery_app import celery_app
from app.processor import get_processor

logger = logging.getLogger(__name__)


class ProcessorTask(Task):
    """Base task with processor instance"""
    _processor = None

    @property
    def processor(self):
        """Get or initialize processor instance for task"""
        if self._processor is None:
            logger.info("Initializing processor in worker")
            self._processor = get_processor()
        return self._processor

    def run(self, *args, **kwargs):
        """Abstract method implementation - not used directly"""
        raise NotImplementedError("ProcessorTask.run should not be called directly")


@celery_app.task(
    bind=True,
    base=ProcessorTask,
    name='app.tasks.process_grammar_correction',
    max_retries=3,
    default_retry_delay=60
)
def process_grammar_correction(self, input_file_path: str, output_dir: str = "/tmp") -> dict:
    """
    Async task to process grammar correction

    Args:
        input_file_path: Path to input file
        output_dir: Directory for output files

    Returns:
        Processing results dictionary
    """
    try:
        logger.info("Processing task %s for file: %s", self.request.id, input_file_path)

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
            error_msg = result.get('error', 'Unknown processing error')
            raise RuntimeError(error_msg)

        logger.info("Task %s completed successfully", self.request.id)

        return result

    except (OSError, RuntimeError, FileNotFoundError) as e:
        logger.error("Task %s failed: %s", self.request.id, e, exc_info=True)

        # Retry on failure
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "success": False,
                "error": "Max retries exceeded: {}".format(str(e)),
                "task_id": self.request.id
            }


@celery_app.task(name='app.tasks.health_check')
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "timestamp": time.time()}
