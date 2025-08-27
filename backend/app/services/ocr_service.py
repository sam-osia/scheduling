import os
import sys
import re
import logging
import threading
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Marker library imports
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser

# Import progress manager
from .progress_manager import progress_manager

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configure marker
openai_config = {
    'output_format': 'html',
    'use_llm': True,
    'llm_service': 'marker.services.openai.OpenAIService',
    'openai_api_key': os.getenv('OPENAI_API_KEY')
}

azure_config = {
    'output_format': 'html',
    'use_llm': True,
    'llm_service': "marker.services.azure_openai.AzureOpenAIService",
    'azure_endpoint': os.getenv('AZURE_ENDPOINT'),
    'azure_api_key': os.getenv('AZURE_API_KEY'),
    'azure_api_version': '2024-12-01-preview',
    'deployment_name': 'gpt-4o',
}

# Initialize marker components
config_parser = ConfigParser(azure_config)
artifact_dict = create_model_dict()

converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=artifact_dict,
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service()
)

class ProgressCapture:
    """Capture and parse marker progress output"""
    
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        # Flexible patterns to match various tqdm/marker progress bar formats
        self.progress_patterns = [
            # Main pattern - handles both ASCII and Unicode progress bars with flexible spacing
            re.compile(r'^(.+?):\s*(\d+)%\|[^|]*\|\s*(\d+/\d+)\s*\[.+\]'),
            # Fallback pattern - more permissive, focuses on key elements
            re.compile(r'^(.+?):\s*(\d+)%.*?(\d+/\d+)'),
            # Minimal pattern - just task and percentage
            re.compile(r'^(.+?):\s*(\d+)%')
        ]
        
    def parse_progress_line(self, line: str):
        """Parse a single line for progress information with fallback patterns"""
        line = line.strip()
        if not line:
            return None
            
        # Debug: log the line we're trying to parse
        if '%|' in line or '%' in line:
            logger.debug(f"Attempting to parse progress line: {line}")
        
        # Try each pattern in order of specificity
        for i, pattern in enumerate(self.progress_patterns):
            match = pattern.match(line)
            if match:
                task_name = match.group(1).strip()
                percentage = int(match.group(2))
                
                # Extract progress info if available (pattern dependent)
                progress_info = None
                if len(match.groups()) >= 3:
                    progress_info = match.group(3)
                
                logger.debug(f"Successfully parsed with pattern {i}: task='{task_name}', percentage={percentage}, info='{progress_info}'")
                
                # Update progress manager
                progress_manager.update_progress(
                    self.doc_id, 
                    task_name, 
                    percentage, 
                    progress_info
                )
                
                return {
                    'task': task_name,
                    'percentage': percentage,
                    'progress': progress_info
                }
        
        # Log unmatched lines that look like progress for debugging
        if '%' in line and any(char in line for char in ['|', '[', ']']):
            logger.warning(f"Failed to parse potential progress line: {line}")
        
        return None

class OutputCapture:
    """Capture stdout/stderr and extract progress information"""
    
    def __init__(self, doc_id: str, original_stream):
        self.progress_capture = ProgressCapture(doc_id)
        self.original_stream = original_stream
        
    def write(self, text: str):
        # Parse each line for progress
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                self.progress_capture.parse_progress_line(line)
        
        # Also write to original stream for logging
        self.original_stream.write(text)
    
    def flush(self):
        self.original_stream.flush()

def process_pdf_to_markdown_sync(pdf_path: str, output_path: str, doc_id: str = None) -> str:
    """
    Convert PDF to markdown using pre-loaded marker OCR models with progress tracking (synchronous)
    This is the original function for cases where isolation isn't needed.
    
    Args:
        pdf_path: Path to input PDF file
        output_path: Path where markdown file should be saved
        doc_id: Document ID for progress tracking (optional)
        
    Returns:
        Extracted markdown text
    """
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Set up progress tracking if doc_id provided
    if doc_id:
        progress_manager.set_status(doc_id, 'processing')
        
        # Capture progress during processing
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            stdout_capture = OutputCapture(doc_id, original_stdout)
            stderr_capture = OutputCapture(doc_id, original_stderr)
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Process PDF using pre-loaded converter
            rendered = converter(pdf_path)
            
        finally:
            # Restore original streams
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    else:
        # Process without progress tracking
        rendered = converter(pdf_path)
    
    text, _, images = text_from_rendered(rendered)
    
    # Save output html to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    if doc_id:
        progress_manager.set_status(doc_id, 'completed')
    
    logger.info(f"PDF processed successfully, saved to: {output_path}")
    
    return text

def process_pdf_to_markdown(pdf_path: str, output_path: str, doc_id: str = None, database=None) -> None:
    """
    Convert PDF to markdown using background thread with file-based output capture
    
    Args:
        pdf_path: Path to input PDF file
        output_path: Path where markdown file should be saved
        doc_id: Document ID for progress tracking (optional)
        database: Database instance for updating document status (optional)
    """
    logger.info(f"Starting threaded PDF processing: {pdf_path}")
    
    if doc_id:
        progress_manager.set_status(doc_id, 'processing')
    
    def run_ocr_thread():
        """Run OCR processing in background thread with isolated output capture"""
        try:
            # Create temporary file to capture stdout/stderr
            with tempfile.NamedTemporaryFile(mode='w+', delete=True, suffix='.log') as capture_file:
                # Store original streams
                original_stdout = sys.stdout
                original_stderr = sys.stderr
                
                try:
                    # Set up progress capture that writes to temp file
                    if doc_id:
                        stdout_capture = OutputCapture(doc_id, capture_file)
                        stderr_capture = OutputCapture(doc_id, capture_file)
                        sys.stdout = stdout_capture
                        sys.stderr = stderr_capture
                    else:
                        # If no doc_id, just redirect to temp file to avoid FastAPI interference
                        sys.stdout = capture_file
                        sys.stderr = capture_file
                    
                    # Process PDF using pre-loaded converter
                    rendered = converter(pdf_path)
                    
                finally:
                    # Always restore original streams
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr
                
                # Extract text from rendered result
                text, _, images = text_from_rendered(rendered)
                
                # Save output to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                if doc_id:
                    progress_manager.set_status(doc_id, 'completed')
                    # Update database status if database instance provided
                    if database:
                        database.update_document_status(doc_id, 'parsed')
                
                logger.info(f"PDF processed successfully, saved to: {output_path}")
                
        except Exception as e:
            error_msg = f"OCR processing failed: {str(e)}"
            logger.error(error_msg)
            if doc_id:
                progress_manager.set_status(doc_id, 'error', error_msg)
                # Update database status if database instance provided
                if database:
                    database.update_document_status(doc_id, 'error', error_msg)
    
    # Run in background thread to avoid blocking FastAPI
    ocr_thread = threading.Thread(target=run_ocr_thread, daemon=True)
    ocr_thread.start()
    
    logger.info(f"OCR processing started in background thread for doc_id: {doc_id}")