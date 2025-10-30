/**
 * API Client - Axios Configuration
 *
 * Configures Axios instance with base URL, interceptors for authentication,
 * and error handling.
 */

import axios from 'axios';
import { auth } from '../config/firebase';

// Create axios instance with base URL
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Set to true if using cookies
});

// Request interceptor - Add Firebase ID token to all requests
api.interceptors.request.use(
  async (config) => {
    // Get current user from Firebase
    const user = auth.currentUser;

    if (user) {
      try {
        // Get fresh ID token
        const token = await user.getIdToken();

        // Add token to Authorization header
        config.headers.Authorization = `Bearer ${token}`;
        console.log('✅ Added auth token to request:', config.url);
      } catch (error) {
        console.error('❌ Failed to get ID token:', error);
      }
    } else {
      console.warn('⚠️ No authenticated user for request:', config.url);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors
api.interceptors.response.use(
  (response) => {
    // Return response data directly
    return response.data;
  },
  (error) => {
    // Handle different error scenarios
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;

      switch (status) {
        case 401:
          // Unauthorized - redirect to login
          console.error('Unauthorized request - redirecting to login');
          window.location.href = '/login';
          break;

        case 402:
          // Payment required - insufficient credits
          console.error('Payment required:', data.detail);
          break;

        case 403:
          // Forbidden
          console.error('Access forbidden:', data.detail);
          break;

        case 404:
          // Not found
          console.error('Resource not found:', data.detail);
          break;

        case 429:
          // Rate limit exceeded
          console.error('Rate limit exceeded:', data.detail);
          break;

        case 500:
        case 503:
          // Server error
          console.error('Server error:', data.detail);
          break;

        default:
          console.error('API error:', data.detail || error.message);
      }

      // Return error with response data
      return Promise.reject({
        status,
        message: data.detail || data.error || error.message,
        data,
      });
    } else if (error.request) {
      // Request made but no response received
      console.error('No response from server:', error.message);
      
      // Check if it's a timeout
      if (error.code === 'ECONNABORTED') {
        return Promise.reject({
          status: 0,
          message: 'Request timeout. The server took too long to respond.',
        });
      }
      
      // Check if backend is down
      return Promise.reject({
        status: 0,
        message: 'Unable to connect to server. Please ensure the backend is running on ' + 
                 (import.meta.env.VITE_API_URL || 'http://localhost:8000'),
      });
    } else {
      // Something else happened
      console.error('Request error:', error.message);
      return Promise.reject({
        status: -1,
        message: error.message,
      });
    }
  }
);

export default api;
