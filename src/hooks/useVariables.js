/**
 * useVariables Hook
 * Manages variables state and CRUD operations
 */

import { useState, useCallback, useEffect } from 'react';
import { fetchVariables, saveVariables as saveVariablesApi } from '../services/variablesService';
import { ApiError } from '../services/apiClient';
import { VALIDATION } from '../config/constants';

/**
 * Generate a unique ID for a variable
 */
function generateId() {
  const uuid = crypto.randomUUID?.() || Math.random().toString(36).substr(2, 9);
  return `var-${Date.now()}-${uuid}`;
}

/**
 * Process variables from API response
 */
function processVariables(variables) {
  return variables.map((v, index) => ({
    ...v,
    id: v._id?.toString() || generateId(),
    MetaData: v.MetaData || '',
  }));
}

/**
 * Custom hook for managing variables
 * @returns {Object} Variables state and methods
 */
export function useVariables() {
  const [variables, setVariables] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  // Fetch variables from API
  const loadVariables = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchVariables();
      setVariables(processVariables(data));
      return { success: true };
    } catch (err) {
      const errorMessage = err instanceof ApiError 
        ? err.message 
        : 'Failed to load variables';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save variables to API
  const saveVariables = useCallback(async () => {
    setIsSaving(true);
    setError(null);

    try {
      const result = await saveVariablesApi(variables);
      
      if (result.status === 'ok') {
        await loadVariables();
        return { success: true, message: result.message };
      }
      
      const errorMessage = result.message || 'Failed to save variables';
      setError(errorMessage);
      return { success: false, error: errorMessage };
      
    } catch (err) {
      const errorMessage = err instanceof ApiError 
        ? err.message 
        : 'Failed to save variables';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsSaving(false);
    }
  }, [variables, loadVariables]);

  // Add a new variable
  const addVariable = useCallback((newVariable) => {
    const trimmedName = newVariable.deviceName.trim();

    // Validate device name format
    if (!VALIDATION.DEVICE_NAME_PATTERN.test(trimmedName)) {
      return { 
        success: false, 
        error: 'Device name must start with a letter or underscore and contain only alphanumeric characters' 
      };
    }

    // Check for duplicates (case-insensitive)
    const isDuplicate = variables.some(
      v => v.deviceName.toLowerCase() === trimmedName.toLowerCase()
    );

    if (isDuplicate) {
      return { 
        success: false, 
        error: `A device with the name "${trimmedName}" already exists` 
      };
    }

    const variable = {
      id: generateId(),
      ...newVariable,
      deviceName: trimmedName,
    };

    setVariables(prev => [...prev, variable]);
    return { success: true, variable };
  }, [variables]);

  // Update a variable
  const updateVariable = useCallback((id, updates) => {
    setVariables(prev => 
      prev.map(v => v.id === id ? { ...v, ...updates } : v)
    );
  }, []);

  // Remove a variable
  const removeVariable = useCallback((id) => {
    setVariables(prev => prev.filter(v => v.id !== id));
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load variables on mount
  useEffect(() => {
    loadVariables();
  }, [loadVariables]);

  return {
    variables,
    isLoading,
    isSaving,
    error,
    loadVariables,
    saveVariables,
    addVariable,
    updateVariable,
    removeVariable,
    clearError,
    setVariables,
  };
}

export default useVariables;
