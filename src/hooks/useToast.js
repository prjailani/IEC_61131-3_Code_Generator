/**
 * useToast Hook
 * Manages toast notification state
 */

import { useState, useCallback } from 'react';
import { UI, TOAST_TYPES } from '../config/constants';

/**
 * Custom hook for managing toast notifications
 * @returns {Object} Toast state and methods
 */
export function useToast() {
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type = TOAST_TYPES.SUCCESS) => {
    setToast({ message, type });
  }, []);

  const hideToast = useCallback(() => {
    setToast(null);
  }, []);

  const showSuccess = useCallback((message) => {
    showToast(message, TOAST_TYPES.SUCCESS);
  }, [showToast]);

  const showError = useCallback((message) => {
    showToast(message, TOAST_TYPES.ERROR);
  }, [showToast]);

  const showInfo = useCallback((message) => {
    showToast(message, TOAST_TYPES.INFO);
  }, [showToast]);

  const showWarning = useCallback((message) => {
    showToast(message, TOAST_TYPES.WARNING);
  }, [showToast]);

  return {
    toast,
    showToast,
    hideToast,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    toastDuration: UI.TOAST_DURATION,
  };
}

export default useToast;
