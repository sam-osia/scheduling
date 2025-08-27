import axios from 'axios';

// Create an instance of axios with default configuration
const ApiService = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://0.0.0.0:8000/api', // Base URL for your API
    timeout: 400000, // Set a timeout for the request (optional)
    headers: {
        'Content-Type': 'application/json',
        // You can add other default headers here
    },
});

// Authorization interceptor
ApiService.interceptors.request.use(
    (config) => {
        // Add authorization token to headers
        const token = localStorage.getItem('idToken');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        // Handle errors before request is sent
        return Promise.reject(error);
    }
);

// You can add response interceptors as well
ApiService.interceptors.response.use(
    (response) => {
        // Perform actions on successful response
        return response;
    },
    (error) => {
        // Handle errors
        if (error.response && error.response.status === 401) {
            // Handle unauthorized access (e.g., redirect to log in)
        }
        return Promise.reject(error);
    }
);

// Document management methods
export const documentService = {
    // Upload multiple documents
    uploadDocuments: async (files) => {
        const formData = new FormData();
        
        // Add each file to the form data
        files.forEach((file) => {
            formData.append('files', file);
        });
        
        // Configure for file upload
        const config = {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 60000, // 60 seconds for file uploads
        };
        
        const response = await ApiService.post('/documents/upload', formData, config);
        return response.data;
    },
    
    // Get all documents
    getAllDocuments: async (status = null) => {
        const params = status ? { status } : {};
        const response = await ApiService.get('/documents/', { params });
        return response.data;
    },
    
    // Get specific document
    getDocument: async (docId) => {
        const response = await ApiService.get(`/documents/${docId}`);
        return response.data;
    },
    
    // Delete document
    deleteDocument: async (docId) => {
        const response = await ApiService.delete(`/documents/${docId}`);
        return response.data;
    },
    
    // Get database stats
    getDatabaseStats: async () => {
        const response = await ApiService.get('/documents/stats/overview');
        return response.data;
    }
};

// Parsing service methods
export const parsingService = {
    // Parse single document
    parseDocument: async (docId) => {
        const response = await ApiService.post(`/parsing/parse/${docId}`);
        return response.data;
    },
    
    // Parse multiple documents
    parseMultipleDocuments: async (docIds) => {
        const response = await ApiService.post('/parsing/parse-batch', docIds);
        return response.data;
    },
    
    // Get parsing status
    getParsingStatus: async (docId) => {
        const response = await ApiService.get(`/parsing/status/${docId}`);
        return response.data;
    },
    
    // Get parsed content
    getParsedContent: async (docId) => {
        const response = await ApiService.get(`/parsing/${docId}/content`);
        return response.data;
    },
    
    // Get parsing progress
    getParsingProgress: async (docId) => {
        const response = await ApiService.get(`/parsing/progress/${docId}`);
        return response.data;
    }
};

// Extraction service methods
export const extractionService = {
    // Extract information from document
    extractInformation: async (docId) => {
        const response = await ApiService.post(`/extraction/extract/${docId}`);
        return response.data;
    },
    
    // Get extracted information
    getExtractedInformation: async (docId) => {
        const response = await ApiService.get(`/extraction/extracted/${docId}`);
        return response.data;
    }
};

export default ApiService;