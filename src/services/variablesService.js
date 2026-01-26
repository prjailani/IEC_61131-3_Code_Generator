/**
 * Variables Service
 * Handles all variable-related API interactions
 */

import apiClient from './apiClient';
import { API_ENDPOINTS, TIMEOUTS } from '../config/constants';

/**
 * Fetch all variables from the database
 * @returns {Promise<Array>} List of variables
 */
export async function fetchVariables() {
  const data = await apiClient.get(API_ENDPOINTS.GET_VARIABLES);
  
  if (!data.variables || !Array.isArray(data.variables)) {
    throw new Error('Invalid response format from server');
  }
  
  return data.variables;
}

/**
 * Save variables to the database
 * @param {Array} variables - List of variables to save
 * @returns {Promise<{status: string, message: string}>}
 */
export async function saveVariables(variables) {
  const variablesToSend = variables.map(({ id, ...rest }) => ({
    ...rest,
    deviceName: rest.deviceName.trim(),
    range: rest.range ? rest.range.trim() : '',
    MetaData: rest.MetaData ? rest.MetaData.trim() : '',
  }));
  
  return apiClient.post(API_ENDPOINTS.SAVE_VARIABLES, { variables: variablesToSend });
}

/**
 * Upload variables from a JSON file
 * @param {File} file - JSON file to upload
 * @returns {Promise<{status: string, message: string}>}
 */
export async function uploadVariablesFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  return apiClient.postForm(
    API_ENDPOINTS.UPLOAD_VARIABLES, 
    formData,
    { timeout: TIMEOUTS.FILE_UPLOAD }
  );
}

/**
 * Remove duplicate variables from the database
 * @returns {Promise<{status: string, message: string}>}
 */
export async function removeDuplicates() {
  return apiClient.delete(API_ENDPOINTS.REMOVE_DUPLICATES);
}

export default {
  fetchVariables,
  saveVariables,
  uploadVariablesFile,
  removeDuplicates,
};
