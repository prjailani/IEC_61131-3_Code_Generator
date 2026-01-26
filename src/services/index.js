/**
 * Services barrel export
 */

export { apiClient, ApiError } from './apiClient';
export { generateCode } from './codeGenerationService';
export { 
  fetchVariables, 
  saveVariables, 
  uploadVariablesFile, 
  removeDuplicates 
} from './variablesService';
