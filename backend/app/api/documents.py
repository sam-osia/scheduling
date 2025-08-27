from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any
import os
import shutil
from pathlib import Path
import json
import logging
from datetime import datetime

from ..database import db

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Define upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

def get_database():
    """Dependency to get database instance"""
    return db

@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    database = Depends(get_database)
) -> JSONResponse:
    """
    Upload multiple PDF documents
    
    Args:
        files: List of uploaded PDF files
        database: Database instance
        
    Returns:
        JSON response with uploaded document information
    """
    uploaded_documents = []
    errors = []
    
    for file in files:
        try:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                errors.append({
                    "filename": file.filename,
                    "error": "Only PDF files are allowed"
                })
                continue
            
            # Validate file size (50MB limit)
            file_content = await file.read()
            if len(file_content) > 50 * 1024 * 1024:  # 50MB
                errors.append({
                    "filename": file.filename,
                    "error": "File size exceeds 50MB limit"
                })
                continue
            
            # Save file to uploads directory
            upload_path = UPLOAD_DIR / file.filename
            
            # Handle duplicate filenames by appending timestamp
            if upload_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = Path(file.filename).stem
                suffix = Path(file.filename).suffix
                new_filename = f"{stem}_{timestamp}{suffix}"
                upload_path = UPLOAD_DIR / new_filename
                logger.info(f"Renamed duplicate file {file.filename} to {new_filename}")
            
            # Write file to uploads directory
            with open(upload_path, "wb") as buffer:
                buffer.write(file_content)
            
            # Add document to database
            doc_id = database.add_document(
                original_filename=file.filename,
                upload_path=str(upload_path)
            )
            
            # Copy raw file to output folder
            document = database.get_document(doc_id)
            if document:
                raw_copy_path = Path(document['raw_copy_path'])
                shutil.copy2(upload_path, raw_copy_path)
                
                # Create initial metadata.json
                await _create_metadata_file(document)
                
                logger.info(f"Successfully uploaded and processed {file.filename} as {doc_id}")
            
            uploaded_documents.append({
                "id": doc_id,
                "filename": file.filename,
                "size": len(file_content),
                "upload_date": document['upload_date'].isoformat() if document else None,
                "status": "uploaded"
            })
            
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {str(e)}")
            errors.append({
                "filename": file.filename,
                "error": f"Upload failed: {str(e)}"
            })
    
    # Prepare response
    response_data = {
        "uploaded_documents": uploaded_documents,
        "upload_count": len(uploaded_documents),
        "error_count": len(errors)
    }
    
    if errors:
        response_data["errors"] = errors
    
    status_code = 200 if uploaded_documents else 400
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

@router.get("/")
async def list_documents(
    status: str = None,
    database = Depends(get_database)
) -> List[Dict[str, Any]]:
    """
    List all documents, optionally filtered by status
    
    Args:
        status: Optional status filter (uploaded/parsing/parsed/error)
        database: Database instance
        
    Returns:
        List of document information
    """
    try:
        if status:
            documents = database.get_documents_by_status(status)
        else:
            documents = database.get_all_documents()
        
        # Format response data
        formatted_documents = []
        for doc in documents:
            formatted_doc = {
                "id": doc["id"],
                "filename": doc["original_filename"],
                "upload_date": doc["upload_date"].isoformat() if doc["upload_date"] else None,
                "status": doc["status"],
                "last_modified": doc["last_modified"].isoformat() if doc["last_modified"] else None,
                "error_message": doc["error_message"],
                "has_extracted_info": doc["extracted_info"] is not None
            }
            formatted_documents.append(formatted_doc)
        
        return formatted_documents
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    database = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get specific document information
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        Document information
    """
    try:
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Format response
        formatted_doc = {
            "id": document["id"],
            "filename": document["original_filename"],
            "upload_date": document["upload_date"].isoformat() if document["upload_date"] else None,
            "status": document["status"],
            "last_modified": document["last_modified"].isoformat() if document["last_modified"] else None,
            "error_message": document["error_message"],
            "extracted_info": document["extracted_info"],
            "file_paths": {
                "raw_copy": document["raw_copy_path"],
                "html": document["html_path"],
                "extracted_info": document["extracted_info_path"],
                "metadata": document["metadata_path"]
            }
        }
        
        return formatted_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    database = Depends(get_database)
) -> Dict[str, str]:
    """
    Delete document and associated files
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        Deletion confirmation
    """
    try:
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete files from filesystem
        files_to_delete = [
            document["upload_path"],
            document["output_folder"]  # This will delete the entire output folder
        ]
        
        for file_path in files_to_delete:
            if file_path and Path(file_path).exists():
                if Path(file_path).is_dir():
                    shutil.rmtree(file_path)
                    logger.info(f"Deleted directory: {file_path}")
                else:
                    Path(file_path).unlink()
                    logger.info(f"Deleted file: {file_path}")
        
        # Delete from database
        success = database.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete from database")
        
        return {"message": f"Document {doc_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.get("/{doc_id}/raw")
async def get_raw_document(
    doc_id: str,
    database = Depends(get_database)
) -> FileResponse:
    """
    Serve raw PDF file for viewing
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        PDF file response for browser viewing
    """
    try:
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get the raw copy path
        raw_copy_path = document.get("raw_copy_path")
        if not raw_copy_path:
            raise HTTPException(status_code=404, detail="Raw document path not found")
        
        # Check if file exists
        file_path = Path(raw_copy_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found on disk")
        
        # Return file response with appropriate headers for PDF viewing
        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            filename=document["original_filename"],
            headers={
                "Content-Disposition": f"inline; filename={document['original_filename']}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving raw document {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve document")

@router.get("/stats/overview")
async def get_database_stats(
    database = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get database statistics and overview
    
    Args:
        database: Database instance
        
    Returns:
        Database statistics
    """
    try:
        stats = database.get_database_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

async def _create_metadata_file(document: Dict[str, Any]):
    """
    Create metadata.json file for document
    
    Args:
        document: Document data from database
    """
    try:
        metadata = {
            "document_id": document["id"],
            "original_filename": document["original_filename"],
            "upload_date": document["upload_date"].isoformat() if document["upload_date"] else None,
            "status": document["status"],
            "created_at": datetime.now().isoformat(),
            "file_paths": {
                "raw_copy": document["raw_copy_path"],
                "html": document["html_path"],
                "extracted_info": document["extracted_info_path"],
                "metadata": document["metadata_path"]
            }
        }
        
        metadata_path = Path(document["metadata_path"])
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.debug(f"Created metadata file: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Error creating metadata file: {str(e)}")
        raise

@router.get("/{doc_id}/raw")
async def get_raw_document(
    doc_id: str,
    database = Depends(get_database)
):
    """
    Serve the raw PDF file for viewing
    
    Args:
        doc_id: Document ID
        database: Database instance
        
    Returns:
        PDF file response
    """
    try:
        document = database.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Use the raw copy in outputs folder, fall back to uploads folder
        raw_copy_path = Path(document['raw_copy_path'])
        if raw_copy_path.exists():
            file_path = raw_copy_path
        else:
            upload_path = Path(document['upload_path'])
            if upload_path.exists():
                file_path = upload_path
            else:
                raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            path=str(file_path),
            media_type='application/pdf',
            headers={
                "Content-Disposition": "inline"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving raw document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve document")