import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  CircularProgress,
  Alert,
  Button,
  Typography,
  Container,
  AppBar,
  Toolbar
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import UploadsListComponent from '../components/UploadsListComponent';
import DocumentViewer from '../components/DocumentViewer';
import ExtractedInformation from '../components/ExtractedInformation';
import { documentService, parsingService } from '../services/ApiService';

const HomePage = () => {
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const selectedDocument = documents.find(doc => doc.id === selectedDocumentId);

  // Load existing documents on component mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const documentsData = await documentService.getAllDocuments();
      
      // Transform API response to match frontend format
      const transformedDocs = documentsData.map(doc => ({
        id: doc.id,
        filename: doc.filename,
        status: doc.status,
        uploadDate: doc.upload_date,
        lastModified: doc.last_modified,
        errorMessage: doc.error_message,
        hasExtractedInfo: doc.has_extracted_info,
        file: null // API manages files
      }));
      
      setDocuments(transformedDocs);
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents. Please refresh the page.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDocumentUpload = (uploadedDocuments) => {
    // Add uploaded documents to the state
    setDocuments(prev => [...prev, ...uploadedDocuments]);
    
    // Auto-select the first uploaded document if none selected
    if (!selectedDocumentId && uploadedDocuments.length > 0) {
      setSelectedDocumentId(uploadedDocuments[0].id);
    }
  };

  const handleDocumentSelect = (documentId) => {
    setSelectedDocumentId(documentId);
  };

  const handleParseDocument = async (documentId) => {
    try {
      // Update UI to show parsing status
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId 
          ? { ...doc, status: 'parsing' }
          : doc
      ));

      // Call backend to parse document
      const response = await parsingService.parseDocument(documentId);
      
      // Update document status based on response
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId 
          ? { ...doc, status: response.status || 'parsed' }
          : doc
      ));

      console.log('Parse successful:', response);
      
    } catch (error) {
      console.error('Parse failed:', error);
      
      // Update status to error
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId 
          ? { 
              ...doc, 
              status: 'error',
              errorMessage: error.response?.data?.detail || error.message || 'Parse failed'
            }
          : doc
      ));
    }
  };

  const handleParseAll = async () => {
    try {
      // Get all uploaded document IDs
      const uploadedDocs = documents.filter(doc => doc.status === 'uploaded');
      const docIds = uploadedDocs.map(doc => doc.id);
      
      if (docIds.length === 0) {
        return; // No documents to parse
      }

      // Update UI to show parsing status for all uploaded docs
      setDocuments(prev => prev.map(doc => 
        doc.status === 'uploaded' 
          ? { ...doc, status: 'parsing' }
          : doc
      ));

      // Call backend to parse all documents
      const response = await parsingService.parseMultipleDocuments(docIds);
      
      // Update document statuses based on batch response
      setDocuments(prev => prev.map(doc => {
        if (!docIds.includes(doc.id)) return doc;
        
        // Check if this document was processed successfully
        const wasProcessed = response.processed?.some(p => p.doc_id === doc.id);
        const wasFailed = response.failed?.some(f => f.doc_id === doc.id);
        const wasAlreadyParsed = response.already_parsed?.includes(doc.id);
        
        if (wasProcessed || wasAlreadyParsed) {
          return { ...doc, status: 'parsed' };
        } else if (wasFailed) {
          const failedDoc = response.failed.find(f => f.doc_id === doc.id);
          return { 
            ...doc, 
            status: 'error', 
            errorMessage: failedDoc?.error || 'Parse failed'
          };
        }
        
        return doc;
      }));

      console.log('Batch parse completed:', response);
      
    } catch (error) {
      console.error('Batch parse failed:', error);
      
      // Reset parsing status for failed batch
      setDocuments(prev => prev.map(doc => 
        doc.status === 'parsing' 
          ? { 
              ...doc, 
              status: 'error',
              errorMessage: 'Batch parse failed'
            }
          : doc
      ));
    }
  };

  const handleDocumentStatusUpdate = (documentId, newStatus, errorMessage = null) => {
    console.log(`Updating document ${documentId} status to ${newStatus}`);
    setDocuments(prev => prev.map(doc => 
      doc.id === documentId 
        ? { 
            ...doc, 
            status: newStatus,
            errorMessage: errorMessage || (newStatus === 'error' ? 'Processing failed' : null)
          }
        : doc
    ));
  };

  const handleDocumentDelete = async (documentId) => {
    try {
      // Call backend to delete document
      await documentService.deleteDocument(documentId);
      
      // Remove document from state
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      
      // Clear selection if the deleted document was selected
      if (selectedDocumentId === documentId) {
        setSelectedDocumentId(null);
      }
      
      console.log(`Document ${documentId} deleted successfully`);
      
    } catch (error) {
      console.error('Delete failed:', error);
      // Could add error state handling here if needed
      alert('Failed to delete document. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={60} />
          <Typography variant="h6" color="text.secondary">
            Loading documents...
          </Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, maxWidth: 400 }}>
          <Alert severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={loadDocuments}
          >
            Retry
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar 
        position="static" 
        elevation={2}
        sx={{ 
          backgroundColor: '#1c2a58',
          zIndex: 1200,
          borderRadius: 0,
          width: '100%',
          left: 0,
          right: 0
        }}
      >
        <Toolbar sx={{ minHeight: '64px !important', px: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box
            component="img"
            src="/images/UHN-Logo-RGB_KO-Primary-scaled.png"
            alt="UHN Research Logo"
            sx={{
              height: '40px',
              width: 'auto',
            }}
          />
          
          <Typography 
            variant="h5" 
            component="h1" 
            sx={{ 
              fontFamily: 'Montserrat',
              color: 'white',
              position: 'absolute',
              left: '50%',
              transform: 'translateX(-50%)',
            }}

          >
            Referral Assistant
          </Typography>

          <Box sx={{ width: '40px' }} />
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ 
        flex: 1, 
        backgroundColor: 'grey.50', 
        display: 'flex',
        overflow: 'hidden'
      }}>
        <Box sx={{ 
          display: 'flex', 
          width: '100%', 
          height: '100%', 
          gap: 1, 
          p: 1 
        }}>
          {/* Upload Panel - 1/5 of page (20%) */}
          <Box sx={{ width: '20%', height: '100%' }}>
            <Paper elevation={2} sx={{ height: '100%', overflow: 'hidden' }}>
              <UploadsListComponent
                documents={documents}
                selectedDocumentId={selectedDocumentId}
                onDocumentUpload={handleDocumentUpload}
                onDocumentSelect={handleDocumentSelect}
                onParseAll={handleParseAll}
                onDocumentStatusUpdate={handleDocumentStatusUpdate}
                onDocumentDelete={handleDocumentDelete}
              />
            </Paper>
          </Box>
          
          {/* Document Viewer - Center space (55%) */}
          <Box sx={{ flex: 1, height: '100%' }}>
            <Paper elevation={2} sx={{ height: '100%', overflow: 'hidden' }}>
              <DocumentViewer
                document={selectedDocument}
                onParseDocument={handleParseDocument}
              />
            </Paper>
          </Box>
          
          {/* Extracted Information - 1/4 of page (25%) */}
          <Box sx={{ width: '25%', height: '100%' }}>
            <Paper elevation={2} sx={{ height: '100%', overflow: 'hidden' }}>
              <ExtractedInformation
                document={selectedDocument}
                onParseDocument={handleParseDocument}
              />
            </Paper>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default HomePage;