● Project Summary: PDF OCR and Information Extraction Webapp

  Overall Goal

  A web application where users can upload PDF documents, run OCR to extract text, and automatically extract structured information fields (Name, Date of Birth,
  Phone Number, Referring Physician, Reason for Referral) - specifically designed for medical document processing.

  Architecture Implemented

  Frontend (React)

  - Three-column layout: Upload list (left) | Document viewer (center) | Extracted info (right)
  - Document management: Upload multiple PDFs, view status, select documents
  - Dual view modes: Raw PDF display and parsed markdown content
  - Real-time status updates: uploaded → parsing → parsed/error
  - Batch operations: "Parse All" button for multiple documents

  Backend (FastAPI + Python)

  - Document API: Upload, list, get, delete endpoints with file serving
  - Parsing API: Single/batch OCR processing with status tracking
  - OCR Integration: Uses marker library with OpenAI LLM for enhanced text extraction
  - File Management: UUID-based folder structure in outputs/{uid}/

  Database (Pandas DataFrame)

  - Singleton pattern: Single source of truth for document metadata
  - Pickle persistence: Simple file-based storage (single-user focused)
  - No threading: Simplified for prototype use
  - Schema: Tracks file paths, status, timestamps, extracted info

  Current File Structure

  backend/
  ├── uploads/              # Raw uploaded PDFs
  ├── outputs/{uid}/        # Per-document folders containing:
  │   ├── original.pdf      # Copy of uploaded file
  │   ├── document.md       # OCR-extracted markdown
  │   ├── extracted_info.json  # Structured field data
  │   └── metadata.json     # Document metadata
  ├── database/             # DataFrame pickle files
  └── app/                  # FastAPI application code

  Key Features Working

  ✅ Upload: Multi-file PDF upload with validation✅ Storage: Organized file system with UUID folders✅ OCR Processing: PDF → Markdown conversion using marker✅
  PDF Display: Inline viewing via backend file serving✅ Parsed Content: Markdown display from API✅ Status Tracking: Real-time parsing status updates✅ Database 
  Operations: CRUD with automatic persistence✅ Batch Processing: Parse multiple documents sequentially

  Technical Decisions Made

  - Single-user focus: Removed threading complexity
  - Simple persistence: Pandas + pickle instead of SQL database
  - Synchronous processing: No background workers/queues
  - API-first: Frontend fetches all data via REST endpoints
  - File serving: Backend serves PDFs directly for browser display
