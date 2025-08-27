import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading

# Configure logging
logger = logging.getLogger(__name__)

class ProgressManager:
    """Simple in-memory progress tracking for document processing"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.progress_data: Dict[str, Dict[str, Any]] = {}
        self.data_lock = threading.Lock()
        self._initialized = True
        logger.info("ProgressManager initialized")
    
    def update_progress(self, doc_id: str, task: str, percentage: int, progress_info: str = None):
        """Update progress for a document"""
        with self.data_lock:
            if doc_id not in self.progress_data:
                self.progress_data[doc_id] = {}
            
            self.progress_data[doc_id].update({
                'task': task,
                'percentage': percentage,
                'progress_info': progress_info,
                'last_updated': datetime.now().isoformat(),
                'status': 'processing'
            })
            
        logger.info(f"Updated progress for {doc_id}: {task} {percentage}%")
    
    def get_progress(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a document"""
        with self.data_lock:
            return self.progress_data.get(doc_id)
    
    def set_status(self, doc_id: str, status: str, error_message: str = None):
        """Set processing status for a document"""
        with self.data_lock:
            if doc_id not in self.progress_data:
                self.progress_data[doc_id] = {}
            
            self.progress_data[doc_id].update({
                'status': status,
                'last_updated': datetime.now().isoformat()
            })
            
            if error_message:
                self.progress_data[doc_id]['error_message'] = error_message
            elif 'error_message' in self.progress_data[doc_id]:
                del self.progress_data[doc_id]['error_message']
                
        logger.info(f"Set status for {doc_id}: {status}")
    
    def clear_progress(self, doc_id: str):
        """Clear progress data for a document"""
        with self.data_lock:
            if doc_id in self.progress_data:
                del self.progress_data[doc_id]
        logger.debug(f"Cleared progress for {doc_id}")
    
    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress data for all documents (for debugging)"""
        with self.data_lock:
            return self.progress_data.copy()

# Global progress manager instance
progress_manager = ProgressManager()