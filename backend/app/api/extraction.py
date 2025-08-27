from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from pathlib import Path

from ..database import db
from ..services.extraction_service import extract_information_from_document
from ..models.schemas import ExtractedInformation

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extraction", tags=["extraction"])

def get_database():
    """Dependency to get database instance"""
    return db

@router.post("/extract/{doc_id}")
async def extract_document_information(
    doc_id: str,
    database = Depends(get_database)
) -> JSONResponse:
    """
    Extract structured information from a parsed document using LLM
    
    Args:
        doc_id: Document ID to extract information from
        database: Database instance
        
    Returns:
        JSON response with extracted information
    """
    try:
        # Get document from database
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document is parsed
        if document['status'] != 'parsed':
            raise HTTPException(
                status_code=400, 
                detail=f"Document must be parsed first. Current status: {document['status']}"
            )
        
        # Get HTML file path
        html_path = document['html_path']
        if not Path(html_path).exists():
            raise HTTPException(status_code=500, detail="Parsed HTML file not found")
        
        logger.info(f"Starting information extraction for document {doc_id}")
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract information using LLM service
        try:
            extracted_info = extract_information_from_document(html_content)
            
            # Store extracted information in document metadata
            database.update_extracted_info(doc_id, extracted_info.model_dump())
            
            logger.info(f"Successfully extracted information from document {doc_id}")
            
            return JSONResponse(
                content={
                    "message": "Information extracted successfully",
                    "doc_id": doc_id,
                    "extracted_information": extracted_info.model_dump()
                },
                status_code=200
            )
            
        except Exception as extraction_error:
            error_message = f"Information extraction failed: {str(extraction_error)}"
            logger.error(f"Extraction failed for document {doc_id}: {extraction_error}")
            
            raise HTTPException(
                status_code=500,
                detail=f"Information extraction failed: {str(extraction_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting information from document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract information: {str(e)}")

@router.get("/extracted/{doc_id}")
async def get_extracted_information(
    doc_id: str,
    database = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get previously extracted information for a document
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        Extracted information or error message
    """
    try:
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        extracted_info = document.get('extracted_info')
        if not extracted_info:
            raise HTTPException(
                status_code=404, 
                detail="No extracted information found. Run extraction first."
            )
        
        return {
            "doc_id": doc_id,
            "filename": document["original_filename"],
            "extracted_information": extracted_info,
            "last_modified": document["last_modified"].isoformat() if document["last_modified"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting extracted information for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get extracted information")