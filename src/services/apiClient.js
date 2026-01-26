/**
 * API Client - Base HTTP client with error handling
 */

import { API_BASE_URL, TIMEOUTS } from '../config/constants';

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Create an AbortController with timeout
 */
function createTimeoutController(timeout = TIMEOUTS.DEFAULT) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  return { controller, timeoutId };
}

/**
 * Handle API response and extract data or throw error
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `Server error (${response.status})`;
    let errorData = null;
    
    try {
      errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      const errorText = await response.text().catch(() => '');
      if (errorText) {
        errorMessage = errorText;
      }
    }
    
    throw new ApiError(errorMessage, response.status, errorData);
  }
  
  return response.json();
}

/**
 * Base fetch wrapper with error handling and timeout
 */
async function request(endpoint, options = {}) {
  const { timeout = TIMEOUTS.DEFAULT, ...fetchOptions } = options;
  const { controller, timeoutId } = createTimeoutController(timeout);
  
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    return await handleResponse(response);
    
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out. Please try again.', 408);
    }
    
    if (error instanceof ApiError) {
      throw error;
    }
    
    if (error.message === 'Failed to fetch') {
      throw new ApiError(
        'Unable to connect to the server. Please ensure the backend is running.',
        0
      );
    }
    
    throw new ApiError(error.message || 'An unexpected error occurred', 500);
  }
}

/**
 * API Client methods
 */
export const apiClient = {
  /**
   * GET request
   */
  get: (endpoint, options = {}) => 
    request(endpoint, { 
      method: 'GET',
      ...options,
    }),

  /**
   * POST request with JSON body
   */
  post: (endpoint, data, options = {}) => 
    request(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      ...options,
    }),

  /**
   * POST request with FormData (for file uploads)
   */
  postForm: (endpoint, formData, options = {}) =>
    request(endpoint, {
      method: 'POST',
      body: formData,
      ...options,
    }),

  /**
   * DELETE request
   */
  delete: (endpoint, options = {}) =>
    request(endpoint, {
      method: 'DELETE',
      ...options,
    }),
};

export default apiClient;
