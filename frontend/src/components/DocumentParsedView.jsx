import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Paper
} from '@mui/material';
import { Refresh, PlayArrow } from '@mui/icons-material';
import { parsingService } from '../services/ApiService';

const DocumentParsedView = ({ document, onParseDocument }) => {
  const [parsedContent, setParsedContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch parsed content when document is parsed
  useEffect(() => {
    if (document && document.status === 'parsed') {
      fetchParsedContent();
    } else {
      setParsedContent(null);
      setError(null);
    }
  }, [document]);

  const fetchParsedContent = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await parsingService.getParsedContent(document.id);
      setParsedContent(response.content);
    } catch (err) {
      console.error('Error fetching parsed content:', err);
      setError('Failed to load parsed content');
    } finally {
      setIsLoading(false);
    }
  };

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

  if (document.status === 'uploaded') {
    return (
      <Box sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center',
        p: 3,
        gap: 2
      }}>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          Document has not been parsed
        </Typography>
        <Button 
          variant="contained" 
          onClick={() => onParseDocument(document.id)}
          startIcon={<PlayArrow />}
        >
          Parse Document
        </Button>
      </Box>
    );
  }

  if (document.status === 'parsing') {
    return (
      <Box sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center',
        p: 3,
        gap: 2
      }}>
        <CircularProgress size={48} />
        <Typography variant="body1" color="text.secondary">
          Parsing document...
        </Typography>
      </Box>
    );
  }

  if (document.status === 'error') {
    return (
      <Box sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center',
        p: 3,
        gap: 2
      }}>
        <Alert severity="error" sx={{ mb: 1 }}>
          Error parsing document
        </Alert>
        <Button 
          variant="contained" 
          onClick={() => onParseDocument(document.id)}
          startIcon={<Refresh />}
          color="error"
        >
          Retry Parsing
        </Button>
      </Box>
    );
  }

  // Show parsed content
  if (document.status === 'parsed') {
    if (isLoading) {
      return (
        <Box sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          p: 3,
          gap: 2
        }}>
          <CircularProgress size={48} />
          <Typography variant="body1" color="text.secondary">
            Loading parsed content...
          </Typography>
        </Box>
      );
    }

    if (error) {
      return (
        <Box sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          p: 3,
          gap: 2
        }}>
          <Alert severity="error" sx={{ mb: 1 }}>
            {error}
          </Alert>
          <Button 
            variant="outlined" 
            onClick={fetchParsedContent}
            startIcon={<Refresh />}
          >
            Retry
          </Button>
        </Box>
      );
    }

    return (
      <Box sx={{ height: '100%', overflow: 'hidden', p: 1 }}>
        {parsedContent ? (
          <Paper
            elevation={0}
            sx={{
              height: '100%',
              overflow: 'auto',
              p: 3,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              backgroundColor: 'white',
              '& *': {
                maxWidth: '100% !important',
              },
              '& img': {
                maxWidth: '100%',
                height: 'auto',
              },
              '& table': {
                width: '100%',
                borderCollapse: 'collapse',
                '& td, & th': {
                  border: 1,
                  borderColor: 'divider',
                  p: 1,
                  fontSize: '0.875rem',
                },
              },
            }}
            dangerouslySetInnerHTML={{ __html: parsedContent }}
          />
        ) : (
          <Box sx={{ 
            height: '100%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            p: 3
          }}>
            <Typography variant="body1" color="text.secondary">
              No parsed content available
            </Typography>
          </Box>
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      p: 3
    }}>
      <Typography variant="body1" color="text.secondary">
        Document not parsed yet
      </Typography>
    </Box>
  );
};

export default DocumentParsedView;