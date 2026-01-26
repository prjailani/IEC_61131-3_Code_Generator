/**
 * Application-wide constants and configuration
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// API Endpoints
export const API_ENDPOINTS = {
  GENERATE_CODE: '/generate-code',
  GET_VARIABLES: '/get-variables',
  SAVE_VARIABLES: '/save-variables',
  UPLOAD_VARIABLES: '/upload-variables-json',
  REMOVE_DUPLICATES: '/remove-duplicates',
  HEALTH: '/',
};

// Request timeouts (in milliseconds)
export const TIMEOUTS = {
  DEFAULT: 30000,
  CODE_GENERATION: 60000,
  FILE_UPLOAD: 30000,
};

// IEC 61131-3 Data Types
export const IEC_DATA_TYPES = [
  'BOOL',
  'SINT', 'INT', 'DINT', 'LINT',
  'USINT', 'UINT', 'UDINT', 'ULINT',
  'REAL', 'LREAL',
  'BYTE', 'WORD', 'DWORD', 'LWORD',
  'STRING',
  'TIME', 'DATE', 'TIME_OF_DAY', 'DATE_AND_TIME',
];

// Validation patterns
export const VALIDATION = {
  DEVICE_NAME_PATTERN: /^[A-Za-z_][A-Za-z0-9_]*$/,
  DEVICE_NAME_MAX_LENGTH: 100,
  NARRATIVE_MAX_LENGTH: 5000,
};

// UI Constants
export const UI = {
  TOAST_DURATION: 3000,
  DEBOUNCE_DELAY: 300,
  COPY_SUCCESS_DURATION: 2000,
};

// Toast types
export const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  INFO: 'info',
  WARNING: 'warning',
};
