/**
 * useCodeGeneration Hook
 * Manages code generation state and logic
 */

import { useState, useCallback } from 'react';
import { generateCode } from '../services/codeGenerationService';
import { ApiError } from '../services/apiClient';

/**
 * Custom hook for code generation functionality
 * @returns {Object} Code generation state and methods
 */
export function useCodeGeneration() {
  const [generatedCode, setGeneratedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = useCallback(async (narrative) => {
    if (!narrative?.trim()) {
      setError('Please enter a description');
      return { success: false };
    }

    setGeneratedCode('');
    setError(null);
    setIsLoading(true);

    try {
      const result = await generateCode(narrative);
      
      if (result.error) {
        setError(result.error);
        return { success: false, error: result.error };
      }
      
      if (result.code) {
        setGeneratedCode(result.code);
        return { success: true, code: result.code };
      }
      
      setError('No code generated');
      return { success: false };
      
    } catch (err) {
      const errorMessage = err instanceof ApiError 
        ? err.message 
        : 'An unexpected error occurred';
      setError(errorMessage);
      return { success: false, error: errorMessage };
      
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCode = useCallback(() => {
    setGeneratedCode('');
  }, []);

  const reset = useCallback(() => {
    setGeneratedCode('');
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    generatedCode,
    isLoading,
    error,
    generate,
    clearError,
    clearCode,
    reset,
  };
}

export default useCodeGeneration;
