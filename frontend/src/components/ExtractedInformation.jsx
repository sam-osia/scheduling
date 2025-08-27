import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Divider,
  Stack
} from '@mui/material';
import { PlayArrow, Refresh, AutoAwesome } from '@mui/icons-material';
import { extractionService } from '../services/ApiService';

const ExtractedInformation = ({ document, onParseDocument }) => {
  const [extractedInfo, setExtractedInfo] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState(null);

  // Load extracted information when document changes
  useEffect(() => {
    if (document && document.status === 'parsed') {
      loadExtractedInformation();
    } else {
      setExtractedInfo(null);
      setExtractionError(null);
    }
  }, [document]);

  const loadExtractedInformation = async () => {
    try {
      const response = await extractionService.getExtractedInformation(document.id);
      setExtractedInfo(response.extracted_information);
      setExtractionError(null);
    } catch (error) {
      // No extracted information yet - not an error
      setExtractedInfo(null);
    }
  };

  const handleExtractInformation = async () => {
    setIsExtracting(true);
    setExtractionError(null);
    
    try {
      const response = await extractionService.extractInformation(document.id);
      setExtractedInfo(response.extracted_information);
    } catch (error) {
      setExtractionError(error.response?.data?.detail || 'Failed to extract information');
    } finally {
      setIsExtracting(false);
    }
  };

  if (!document) {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Extracted Information
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ 
          flex: 1,
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
        }}>
          <Typography variant="body1" color="text.secondary" textAlign="center">
            Select a document to view extracted information
          </Typography>
        </Box>
      </Box>
    );
  }

  if (document.status === 'uploaded') {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Extracted Information
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ 
          flex: 1,
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
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
      </Box>
    );
  }

  if (document.status === 'parsing') {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Extracted Information
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ 
          flex: 1,
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          gap: 2
        }}>
          <CircularProgress size={48} />
          <Typography variant="body1" color="text.secondary">
            Parsing document...
          </Typography>
        </Box>
      </Box>
    );
  }

  if (document.status === 'error') {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Extracted Information
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ 
          flex: 1,
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          gap: 2
        }}>
          <Alert severity="error" sx={{ width: '100%' }}>
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
      </Box>
    );
  }

  // Show extraction interface for parsed documents
  if (document.status === 'parsed') {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Extracted Information
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Box sx={{ flex: 1, overflow: 'auto', pt: 1 }}>
          {!extractedInfo && !isExtracting && (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center', 
              justifyContent: 'center',
              gap: 2,
              height: '200px'
            }}>
              <Typography variant="body1" color="text.secondary" textAlign="center">
                Information not extracted yet
              </Typography>
              <Button 
                variant="contained" 
                onClick={handleExtractInformation}
                startIcon={<AutoAwesome />}
              >
                Extract Information
              </Button>
            </Box>
          )}

          {isExtracting && (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center', 
              justifyContent: 'center',
              gap: 2,
              height: '200px'
            }}>
              <CircularProgress size={48} />
              <Typography variant="body1" color="text.secondary">
                Extracting information...
              </Typography>
            </Box>
          )}

          {extractionError && (
            <Box sx={{ mb: 2 }}>
              <Alert severity="error" sx={{ mb: 2 }}>
                {extractionError}
              </Alert>
              <Button 
                variant="outlined" 
                onClick={handleExtractInformation}
                startIcon={<Refresh />}
                fullWidth
              >
                Retry Extraction
              </Button>
            </Box>
          )}

          {extractedInfo && (
            <Box sx={{ pr: 1 }}>
              <Stack spacing={2}>
                <TextField
                  label="Patient Name"
                  value={extractedInfo.patient_name || ''}
                  placeholder="Not extracted"
                  InputProps={{ readOnly: true }}
                  variant="outlined"
                  fullWidth
                  size="small"
                />

                <TextField
                  label="Date of Birth"
                  value={extractedInfo.date_of_birth ? 
                    `${extractedInfo.date_of_birth.month}/${extractedInfo.date_of_birth.day}/${extractedInfo.date_of_birth.year}` : 
                    ''}
                  placeholder="Not extracted"
                  InputProps={{ readOnly: true }}
                  variant="outlined"
                  fullWidth
                  size="small"
                />

                <TextField
                  label="Phone Number"
                  value={extractedInfo.phone_number || ''}
                  placeholder="Not extracted"
                  InputProps={{ readOnly: true }}
                  variant="outlined"
                  fullWidth
                  size="small"
                />

                <TextField
                  label="Referring Physician"
                  value={extractedInfo.referring_physician_name || ''}
                  placeholder="Not extracted"
                  InputProps={{ readOnly: true }}
                  variant="outlined"
                  fullWidth
                  size="small"
                />

                <TextField
                  label="Reason for Referral"
                  value={extractedInfo.reason_for_referral || ''}
                  placeholder="Not extracted"
                  InputProps={{ readOnly: true }}
                  variant="outlined"
                  fullWidth
                  multiline
                  rows={6}
                  size="small"
                />

                <Button 
                  variant="outlined" 
                  onClick={handleExtractInformation}
                  startIcon={<Refresh />}
                  fullWidth
                  sx={{ mt: 2 }}
                >
                  Re-extract Information
                </Button>
              </Stack>
            </Box>
          )}
        </Box>
      </Box>
    );
  }

  return null;
};

export default ExtractedInformation;