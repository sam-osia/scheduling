import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  ButtonGroup,
  Button,
  Divider
} from '@mui/material';
import { PictureAsPdf, TextSnippet } from '@mui/icons-material';
import DocumentRawViewComponent from './DocumentRawViewComponent';
import DocumentParsedView from './DocumentParsedView';

const DocumentViewer = ({ document, onParseDocument }) => {
  const [viewMode, setViewMode] = useState('raw');

  if (!document) {
    return (
      <Box sx={{ 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        p: 3
      }}>
        <Typography variant="h6" color="text.secondary">
          Select a document from the list to view
        </Typography>
      </Box>
    );
  }

  const handleParseClick = () => {
    onParseDocument(document.id);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ 
        p: 2, 
        borderBottom: 1, 
        borderColor: 'divider',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'grey.50'
      }}>
        <Typography variant="h6" noWrap sx={{ flex: 1, mr: 2 }}>
          {document.filename}
        </Typography>
        
        <ButtonGroup variant="outlined" size="small">
          <Button 
            variant={viewMode === 'raw' ? 'contained' : 'outlined'}
            onClick={() => setViewMode('raw')}
            startIcon={<PictureAsPdf />}
          >
            Raw PDF
          </Button>
          <Button 
            variant={viewMode === 'parsed' ? 'contained' : 'outlined'}
            onClick={() => setViewMode('parsed')}
            disabled={document.status === 'uploaded'}
            startIcon={<TextSnippet />}
          >
            Parsed Content
          </Button>
        </ButtonGroup>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {viewMode === 'raw' ? (
          <DocumentRawViewComponent document={document} />
        ) : (
          <DocumentParsedView 
            document={document} 
            onParseDocument={handleParseClick}
          />
        )}
      </Box>
    </Box>
  );
};

export default DocumentViewer;