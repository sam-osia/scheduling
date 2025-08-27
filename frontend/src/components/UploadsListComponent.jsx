import React, { useRef, useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  LinearProgress,
  Divider,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import {
  CloudUpload,
  PlayArrow,
  Delete,
  Description,
  Refresh,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';
import { documentService, parsingService } from '../services/ApiService';

const UploadsListComponent = ({ 
  documents, 
  selectedDocumentId, 
  onDocumentUpload, 
  onDocumentSelect, 
  onParseAll,
  onDocumentStatusUpdate,
  onDocumentDelete 
}) => {
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [progressData, setProgressData] = useState({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState(null);

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    event.target.value = '';
    
    if (files.length === 0) return;
    
    setIsUploading(true);
    setUploadError(null);
    
    try {
      // Call API to upload files
      const response = await documentService.uploadDocuments(files);
      
      // Check if there were any errors
      if (response.errors && response.errors.length > 0) {
        setUploadError(`Some files failed to upload: ${response.errors.map(e => e.error).join(', ')}`);
      }
      
      // If successful uploads, notify parent component
      if (response.uploaded_documents && response.uploaded_documents.length > 0) {
        // Transform API response to match frontend format
        const uploadedDocs = response.uploaded_documents.map(doc => ({
          id: doc.id,
          filename: doc.filename,
          status: doc.status,
          uploadDate: doc.upload_date,
          file: null // API manages files, no need for file objects
        }));
        
        onDocumentUpload(uploadedDocs);
      }
      
    } catch (error) {
      console.error('Upload error:', error);
      setUploadError(
        error.response?.data?.detail || 
        error.message || 
        'Failed to upload files. Please try again.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleDeleteClick = (document, event) => {
    event.stopPropagation();
    setDocumentToDelete(document);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (documentToDelete) {
      await onDocumentDelete(documentToDelete.id);
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDocumentToDelete(null);
  };

  // Progress polling effect
  useEffect(() => {
    const parsingDocuments = documents.filter(doc => doc.status === 'parsing');
    
    if (parsingDocuments.length === 0) {
      return; // No documents being parsed
    }
    
    const pollProgress = async () => {
      const progressPromises = parsingDocuments.map(async (doc) => {
        try {
          const progress = await parsingService.getParsingProgress(doc.id);
          return { docId: doc.id, progress };
        } catch (error) {
          console.error(`Error fetching progress for ${doc.id}:`, error);
          return { docId: doc.id, progress: null };
        }
      });
      
      const results = await Promise.all(progressPromises);
      const newProgressData = {};
      
      results.forEach(({ docId, progress }) => {
        if (progress) {
          newProgressData[docId] = progress;
          
          // Check if document status has changed to completed and needs database update
          const currentDoc = documents.find(doc => doc.id === docId);
          if (currentDoc && 
              currentDoc.status === 'parsing' && 
              (progress.status === 'completed' || progress.status === 'error') &&
              onDocumentStatusUpdate) {
            // Update document status to match progress status
            const newStatus = progress.status === 'completed' ? 'parsed' : 'error';
            onDocumentStatusUpdate(docId, newStatus, progress.error_message);
          }
        }
      });
      
      setProgressData(newProgressData);
    };
    
    // Poll immediately
    pollProgress();
    
    // Set up polling interval
    const interval = setInterval(pollProgress, 1000); // Poll every second
    
    return () => clearInterval(interval);
  }, [documents]);

  const getStatusChip = (status) => {
    const statusConfig = {
      uploaded: { icon: <Description />, color: 'default', label: 'Uploaded' },
      parsing: { icon: <Refresh />, color: 'warning', label: 'Parsing' },
      parsed: { icon: <CheckCircle />, color: 'success', label: 'Parsed' },
      error: { icon: <ErrorIcon />, color: 'error', label: 'Error' }
    };
    
    const config = statusConfig[status] || statusConfig.uploaded;
    
    return (
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        size="small"
        variant="outlined"
      />
    );
  };

  const unparsedCount = documents.filter(doc => doc.status === 'uploaded').length;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
      {/* Combined Documents Section */}
      <Paper elevation={1} sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 2, pb: 1 }}>
          <Typography variant="h6" gutterBottom>
            Documents
          </Typography>
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf"
            multiple
            style={{ display: 'none' }}
          />
          
          <Button
            variant="outlined"
            fullWidth
            startIcon={<CloudUpload />}
            onClick={handleUploadClick}
            disabled={isUploading}
            sx={{ mb: 1 }}
          >
            {isUploading ? 'Uploading...' : 'Choose PDF Files'}
          </Button>
          
          {uploadError && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {uploadError}
            </Alert>
          )}
          
          {unparsedCount > 0 && (
            <Button
              variant="contained"
              fullWidth
              startIcon={<PlayArrow />}
              onClick={onParseAll}
              color="success"
              sx={{ mt: 1 }}
            >
              Parse All Documents ({unparsedCount})
            </Button>
          )}
        </Box>
        <Divider />
        
        {documents.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" style={{ fontStyle: 'italic' }}>
              No documents uploaded yet
            </Typography>
          </Box>
        ) : (
          <List sx={{ flex: 1, overflow: 'auto', p: 0 }}>
            {documents.map((document) => (
              <React.Fragment key={document.id}>
                <ListItem
                  button
                  onClick={() => onDocumentSelect(document.id)}
                  selected={selectedDocumentId === document.id}
                  sx={{
                    py: 1.5,
                    '&.Mui-selected': {
                      backgroundColor: 'primary.50',
                      borderRight: 3,
                      borderRightColor: 'primary.main'
                    }
                  }}
                >
                  <ListItemText
                    primary={
                      <Typography variant="subtitle2" noWrap>
                        {document.filename}
                      </Typography>
                    }
                    secondary={
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                          {getStatusChip(document.status)}
                        </Box>
                        
                        {/* Progress display for parsing documents */}
                        {document.status === 'parsing' && progressData[document.id] && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              {progressData[document.id].task || 'Processing...'}
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={progressData[document.id].percentage || 0}
                              sx={{ mt: 0.5, mb: 0.5 }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {progressData[document.id].percentage || 0}%
                              {progressData[document.id].progress_info && (
                                <span> ({progressData[document.id].progress_info})</span>
                              )}
                            </Typography>
                          </Box>
                        )}
                        
                        <Typography variant="caption" color="text.secondary" display="block">
                          {new Date(document.uploadDate).toLocaleDateString()}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={(e) => handleDeleteClick(document, e)}
                      color="error"
                      size="small"
                      sx={{
                        '&:hover': {
                          backgroundColor: 'error.50'
                        }
                      }}
                    >
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Delete Document
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete "{documentToDelete?.filename}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UploadsListComponent;