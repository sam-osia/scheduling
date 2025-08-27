from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import logging
from pathlib import Path
import shutil

from ..database import db
from ..services.ocr_service import process_pdf_to_markdown
from ..services.progress_manager import progress_manager

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parsing", tags=["parsing"])

def get_database():
    """Dependency to get database instance"""
    return db

def background_parse_document(doc_id: str, raw_copy_path: str, html_path: str, database):
    """Background task to process document with progress tracking"""
    try:
        # Process the document with progress tracking - now handles database updates internally
        process_pdf_to_markdown(raw_copy_path, html_path, doc_id, database)
        
        logger.info(f"Successfully parsed document {doc_id}")
        
    except Exception as ocr_error:
        error_message = f"OCR processing failed: {str(ocr_error)}"
        database.update_document_status(doc_id, 'error', error_message)
        progress_manager.set_status(doc_id, 'error', error_message)
        logger.error(f"OCR failed for document {doc_id}: {ocr_error}")

@router.post("/parse/{doc_id}")
async def parse_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    database = Depends(get_database)
) -> JSONResponse:
    """
    Parse a single document using OCR
    
    Args:
        doc_id: Document ID to parse
        database: Database instance
        
    Returns:
        JSON response with parsing results
    """
    try:
        # Get document from database
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document is already being processed
        if document['status'] == 'parsing':
            return JSONResponse(
                content={
                    "message": "Document is already being parsed",
                    "doc_id": doc_id,
                    "status": "parsing"
                },
                status_code=202
            )
        
        # Check if document is already parsed
        if document['status'] == 'parsed':
            return JSONResponse(
                content={
                    "message": "Document is already parsed",
                    "doc_id": doc_id,
                    "status": "parsed"
                },
                status_code=200
            )
        
        # Update status to parsing
        database.update_document_status(doc_id, 'parsing')
        logger.info(f"Starting to parse document {doc_id}")
        
        # Get file paths
        raw_copy_path = document['raw_copy_path']
        html_path = document['html_path']
        
        # Ensure raw copy exists
        if not Path(raw_copy_path).exists():
            # Copy from upload path if raw copy doesn't exist
            upload_path = document['upload_path']
            if Path(upload_path).exists():
                shutil.copy2(upload_path, raw_copy_path)
                logger.info(f"Copied file from {upload_path} to {raw_copy_path}")
            else:
                database.update_document_status(doc_id, 'error', 'Source file not found')
                raise HTTPException(status_code=500, detail="Source file not found")
        
        # Start background processing
        background_tasks.add_task(
            background_parse_document,
            doc_id,
            raw_copy_path,
            html_path,
            database
        )
        
        # Return immediately with accepted status
        return JSONResponse(
            content={
                "message": "Document parsing started",
                "doc_id": doc_id,
                "status": "parsing"
            },
            status_code=202  # Accepted - processing in background
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing document {doc_id}: {e}")
        database.update_document_status(doc_id, 'error', str(e))
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

@router.post("/parse-batch")
async def parse_multiple_documents(
    doc_ids: List[str],
    database = Depends(get_database)
) -> JSONResponse:
    """
    Parse multiple documents in batch
    
    Args:
        doc_ids: List of document IDs to parse
        database: Database instance
        
    Returns:
        JSON response with batch parsing results
    """
    try:
        results = {
            "total_requested": len(doc_ids),
            "processed": [],
            "already_parsed": [],
            "failed": [],
            "not_found": []
        }
        
        logger.info(f"Starting batch parsing for {len(doc_ids)} documents")
        
        for doc_id in doc_ids:
            try:
                # Get document
                document = database.get_document(doc_id)
                if not document:
                    results["not_found"].append(doc_id)
                    continue
                
                # Skip if already parsed
                if document['status'] == 'parsed':
                    results["already_parsed"].append(doc_id)
                    continue
                
                # Skip if currently parsing
                if document['status'] == 'parsing':
                    continue
                
                # Update status to parsing
                database.update_document_status(doc_id, 'parsing')
                
                # Get file paths
                raw_copy_path = document['raw_copy_path']
                html_path = document['html_path']
                
                # Ensure raw copy exists
                if not Path(raw_copy_path).exists():
                    upload_path = document['upload_path']
                    if Path(upload_path).exists():
                        shutil.copy2(upload_path, raw_copy_path)
                    else:
                        database.update_document_status(doc_id, 'error', 'Source file not found')
                        results["failed"].append({"doc_id": doc_id, "error": "Source file not found"})
                        continue
                
                # Process the document
                try:
                    process_pdf_to_markdown(raw_copy_path, html_path, doc_id, database)
                    results["processed"].append({
                        "doc_id": doc_id,
                        "status": "parsed"
                    })
                    logger.info(f"Successfully parsed document {doc_id} in batch")
                    
                except Exception as ocr_error:
                    error_message = f"OCR processing failed: {str(ocr_error)}"
                    database.update_document_status(doc_id, 'error', error_message)
                    results["failed"].append({"doc_id": doc_id, "error": str(ocr_error)})
                    logger.error(f"OCR failed for document {doc_id}: {ocr_error}")
                
            except Exception as e:
                database.update_document_status(doc_id, 'error', str(e))
                results["failed"].append({"doc_id": doc_id, "error": str(e)})
                logger.error(f"Error processing document {doc_id}: {e}")
        
        # Calculate success rate
        total_processed = len(results["processed"]) + len(results["already_parsed"])
        success_rate = (total_processed / len(doc_ids)) * 100 if doc_ids else 0
        
        results["summary"] = {
            "total_processed": total_processed,
            "success_rate": round(success_rate, 2)
        }
        
        logger.info(f"Batch parsing completed. Success rate: {success_rate}%")
        
        return JSONResponse(content=results, status_code=200)
        
    except Exception as e:
        logger.error(f"Error in batch parsing: {e}")
        raise HTTPException(status_code=500, detail=f"Batch parsing failed: {str(e)}")

@router.get("/status/{doc_id}")
async def get_parsing_status(
    doc_id: str,
    database = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get parsing status for a document
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        Document parsing status information
    """
    try:
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Build status response
        status_info = {
            "doc_id": doc_id,
            "filename": document["original_filename"],
            "status": document["status"],
            "upload_date": document["upload_date"].isoformat() if document["upload_date"] else None,
            "last_modified": document["last_modified"].isoformat() if document["last_modified"] else None,
            "error_message": document.get("error_message")
        }
        
        # Add file information if parsed
        if document["status"] == "parsed":
            html_path = document["html_path"]
            if Path(html_path).exists():
                status_info["html_available"] = True
                status_info["html_size"] = Path(html_path).stat().st_size
            else:
                status_info["html_available"] = False
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document status")

@router.get("/progress/{doc_id}")
async def get_parsing_progress(
    doc_id: str,
    database = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get real-time parsing progress for a document
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        Progress information including current task and percentage
    """
    try:
        # Check if document exists
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get progress from progress manager
        progress_data = progress_manager.get_progress(doc_id)
        
        if not progress_data:
            # No progress data - return based on document status
            return {
                "doc_id": doc_id,
                "status": document["status"],
                "task": None,
                "percentage": 0,
                "progress_info": None,
                "last_updated": None
            }
        
        return {
            "doc_id": doc_id,
            "status": progress_data.get("status", document["status"]),
            "task": progress_data.get("task"),
            "percentage": progress_data.get("percentage", 0),
            "progress_info": progress_data.get("progress_info"),
            "last_updated": progress_data.get("last_updated"),
            "error_message": progress_data.get("error_message")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get parsing progress")

@router.get("/{doc_id}/content")
async def get_parsed_content(
    doc_id: str,
    database = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get parsed markdown content for a document
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        Parsed content or error message
    """
    try:
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document["status"] != "parsed":
            raise HTTPException(
                status_code=400, 
                detail=f"Document not parsed yet. Current status: {document['status']}"
            )
        
        html_path = document["html_path"]
        if not Path(html_path).exists():
            raise HTTPException(status_code=500, detail="Parsed content file not found")
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "doc_id": doc_id,
            "filename": document["original_filename"],
            "content": content,
            "content_length": len(content),
            "last_modified": document["last_modified"].isoformat() if document["last_modified"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document content")