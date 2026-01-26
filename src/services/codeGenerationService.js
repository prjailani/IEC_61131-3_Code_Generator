/**
 * Code Generation Service
 * Handles all code generation API interactions
 */

import apiClient from './apiClient';
import { API_ENDPOINTS, TIMEOUTS } from '../config/constants';

/**
 * Generate IEC 61131-3 code from natural language
 * @param {string} narrative - Natural language description
 * @returns {Promise<{code: string} | {error: string}>}
 */
export async function generateCode(narrative) {
  const data = await apiClient.post(
    API_ENDPOINTS.GENERATE_CODE,
    { narrative: narrative.trim() },
    { timeout: TIMEOUTS.CODE_GENERATION }
  );
  
  // Check for "no device found" response
  if (data.NO_DEVICE_FOUND) {
    return {
      error: 'No matching device found for your query. Please check the available variables.',
    };
  }
  
  if (data.code) {
    return { code: data.code };
  }
  
  return {
    error: 'The server response did not contain the expected code data.',
  };
}

export default {
  generateCode,
};
