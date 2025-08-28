import React from 'react';
import {
  Box,
  Typography,
  Link
} from '@mui/material';
import ApiService from '../services/ApiService';

const DocumentRawViewComponent = ({ document }) => {
  if (!document) {
    return (
      <Box sx={{ 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        p: 3
      }}>
        <Typography variant="body1" color="text.secondary">
          No document selected
        </Typography>
      </Box>
    );
  }

  // Generate API URL for the PDF file using ApiService baseURL
  const fileUrl = document.id ? `${ApiService.defaults.baseURL}/documents/${document.id}/raw` : null;

  return (
    <Box sx={{ height: '100%', p: 1 }}>
      {fileUrl ? (
        <Box
          component="iframe"
          src={fileUrl}
          title={document.filename}
          sx={{
            width: '100%',
            height: '100%',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            backgroundColor: 'white'
          }}
        />
      ) : (
        <Box sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          p: 3,
          textAlign: 'center'
        }}>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            PDF preview not available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            File: {document.filename}
          </Typography>
          {fileUrl && (
            <Link 
              href={fileUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              sx={{ mt: 2 }}
            >
              Download PDF
            </Link>
          )}
        </Box>
      )}
    </Box>
  );
};

export default DocumentRawViewComponent;