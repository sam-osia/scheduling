from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from pathlib import Path

# Import API routers
from .api.documents import router as documents_router
from .api.parsing import router as parsing_router
from .api.extraction import router as extraction_router

# Import database to ensure initialization
from .database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="PDF OCR and Information Extraction API",
    description="API for uploading PDF documents, performing OCR, and extracting structured information",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
    "http://localhost:3001",  # Alternative React port
    "http://127.0.0.1:3001",
    "http://10.2.54.201:3000",  # Network access
    "http://10.2.54.201:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents_router)
app.include_router(parsing_router)
app.include_router(extraction_router)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting PDF OCR API server...")
    
    # Ensure required directories exist
    backend_path = Path(__file__).parent.parent
    required_dirs = [
        backend_path / "uploads",
        backend_path / "outputs", 
        backend_path / "database"
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")
    
    # Initialize database
    try:
        stats = db.get_database_stats()
        logger.info(f"Database initialized with {stats['total_documents']} documents")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    logger.info("API server startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down PDF OCR API server...")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": "PDF OCR and Information Extraction API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        stats = db.get_database_stats()
        
        return {
            "status": "healthy",
            "database": "connected",
            "documents_count": stats.get("total_documents", 0),
            "timestamp": "2024-01-01T00:00:00Z"  # You might want to use actual timestamp
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "error",
                "error": str(e)
            }
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # This allows running the app directly with: python -m app.main
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )