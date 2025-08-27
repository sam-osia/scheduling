import pandas as pd
import pickle
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentDatabase:
    """Simple class for managing document database using pandas DataFrame"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.db_path = Path(__file__).parent.parent / "database"
        self.pickle_file = self.db_path / "documents_db.pkl"
        self.backup_file = self.db_path / "documents_db_backup.pkl"
        
        # Ensure database directory exists
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize DataFrame with schema
        self.df_columns = [
            'id',                    # UUID string
            'original_filename',     # User's original filename
            'upload_date',          # Upload timestamp
            'status',               # uploaded/parsing/parsed/error
            'upload_path',          # Path to raw file in uploads/
            'output_folder',        # Path to outputs/{uid}/ folder
            'raw_copy_path',        # Path to raw copy in outputs/{uid}/
            'html_path',            # Path to .html file in outputs/{uid}/
            'extracted_info_path',  # Path to extracted info JSON
            'metadata_path',        # Path to metadata JSON
            'extracted_info',       # Cached extracted info dict
            'error_message',        # Error details if failed
            'last_modified'         # Last modification timestamp
        ]
        
        # Load existing data or create new DataFrame
        self._load_database()
        self._initialized = True
        
        logger.info(f"DocumentDatabase initialized with {len(self.df)} records")
    
    def _load_database(self):
        """Load database from pickle file or create new DataFrame"""
        try:
            if self.pickle_file.exists():
                with open(self.pickle_file, 'rb') as f:
                    self.df = pickle.load(f)
                logger.info(f"Loaded database from {self.pickle_file}")
                
                # Validate DataFrame structure and handle column migration
                missing_cols = set(self.df_columns) - set(self.df.columns)
                if missing_cols:
                    logger.warning(f"Adding missing columns: {missing_cols}")
                    for col in missing_cols:
                        self.df[col] = None
                
                # Handle migration from markdown_path to html_path
                if 'markdown_path' in self.df.columns and 'html_path' not in self.df.columns:
                    logger.info("Migrating markdown_path to html_path")
                    self.df['html_path'] = self.df['markdown_path'].str.replace('.md', '.html')
                    self.df.drop('markdown_path', axis=1, inplace=True)
                    self._save_database()
                    logger.info("Migration completed")
                        
            else:
                # Create new DataFrame
                self.df = pd.DataFrame(columns=self.df_columns)
                self.df.set_index('id', inplace=True)
                logger.info("Created new database DataFrame")
                
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            # Try backup file
            if self.backup_file.exists():
                try:
                    with open(self.backup_file, 'rb') as f:
                        self.df = pickle.load(f)
                    logger.info("Loaded database from backup file")
                except Exception as backup_error:
                    logger.error(f"Error loading backup: {backup_error}")
                    self._create_empty_dataframe()
            else:
                self._create_empty_dataframe()
    
    def _create_empty_dataframe(self):
        """Create empty DataFrame with proper schema"""
        self.df = pd.DataFrame(columns=self.df_columns)
        self.df.set_index('id', inplace=True)
        logger.info("Created empty DataFrame")
    
    def _save_database(self):
        """Save DataFrame to pickle file with backup"""
        try:
            # Create backup of existing file
            if self.pickle_file.exists():
                self.pickle_file.replace(self.backup_file)
            
            # Save current DataFrame
            with open(self.pickle_file, 'wb') as f:
                pickle.dump(self.df, f)
            
            logger.debug("Database saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            raise
    
    def add_document(self, original_filename: str, upload_path: str) -> str:
        """Add new document to database and return document ID"""
        doc_id = str(uuid.uuid4())
        
        # Create output folder structure
        output_folder = Path(__file__).parent.parent / "outputs" / doc_id
        output_folder.mkdir(exist_ok=True)
        
        # Define paths for all files in output folder
        raw_copy_path = output_folder / original_filename
        html_path = output_folder / f"{Path(original_filename).stem}.html"
        extracted_info_path = output_folder / "extracted_info.json"
        metadata_path = output_folder / "metadata.json"
        
        # Create document record
        document_data = {
            'original_filename': original_filename,
            'upload_date': datetime.now(),
            'status': 'uploaded',
            'upload_path': upload_path,
            'output_folder': str(output_folder),
            'raw_copy_path': str(raw_copy_path),
            'html_path': str(html_path),
            'extracted_info_path': str(extracted_info_path),
            'metadata_path': str(metadata_path),
            'extracted_info': None,
            'error_message': None,
            'last_modified': datetime.now()
        }
        
        # Add to DataFrame
        self.df.loc[doc_id] = document_data
        
        # Save to pickle file
        self._save_database()
        
        logger.info(f"Added document {doc_id}: {original_filename}")
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        if doc_id in self.df.index:
            doc_data = self.df.loc[doc_id].to_dict()
            doc_data['id'] = doc_id
            return doc_data
        return None
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents as list of dictionaries"""
        documents = []
        for doc_id, row in self.df.iterrows():
            doc_data = row.to_dict()
            doc_data['id'] = doc_id
            documents.append(doc_data)
        return documents
    
    def update_document_status(self, doc_id: str, status: str, error_message: str = None):
        """Update document status"""
        if doc_id in self.df.index:
            self.df.loc[doc_id, 'status'] = status
            self.df.loc[doc_id, 'last_modified'] = datetime.now()
            if error_message:
                self.df.loc[doc_id, 'error_message'] = error_message
            self._save_database()
            logger.info(f"Updated document {doc_id} status to {status}")
    
    def update_extracted_info(self, doc_id: str, extracted_info: Dict[str, Any]):
        """Update extracted information for document"""
        if doc_id in self.df.index:
            # Use .at for setting complex data to avoid indexing issues
            self.df.at[doc_id, 'extracted_info'] = extracted_info
            self.df.at[doc_id, 'last_modified'] = datetime.now()
            self._save_database()
            logger.info(f"Updated extracted info for document {doc_id}")
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document from database"""
        if doc_id in self.df.index:
            self.df.drop(doc_id, inplace=True)
            self._save_database()
            logger.info(f"Deleted document {doc_id}")
            return True
        return False
    
    def get_documents_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get documents filtered by status"""
        filtered_df = self.df[self.df['status'] == status]
        documents = []
        for doc_id, row in filtered_df.iterrows():
            doc_data = row.to_dict()
            doc_data['id'] = doc_id
            documents.append(doc_data)
        return documents
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        total_docs = len(self.df)
        status_counts = self.df['status'].value_counts().to_dict()
        
        return {
            'total_documents': total_docs,
            'status_counts': status_counts,
            'database_file': str(self.pickle_file),
            'last_backup': str(self.backup_file) if self.backup_file.exists() else None
        }

# Global database instance
db = DocumentDatabase()