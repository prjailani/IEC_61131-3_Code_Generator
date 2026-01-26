/**
 * useCopyToClipboard Hook
 * Manages clipboard copy functionality with feedback
 */

import { useState, useCallback } from 'react';
import { UI } from '../config/constants';

/**
 * Custom hook for clipboard copy functionality
 * @param {number} resetDelay - Delay before resetting success state
 * @returns {Object} Copy state and methods
 */
export function useCopyToClipboard(resetDelay = UI.COPY_SUCCESS_DURATION) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  const copy = useCallback(async (text) => {
    if (!text) {
      setError('Nothing to copy');
      return false;
    }

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setError(null);
      
      // Reset after delay
      setTimeout(() => setCopied(false), resetDelay);
      return true;
      
    } catch (err) {
      // Fallback for older browsers
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        setCopied(true);
        setError(null);
        setTimeout(() => setCopied(false), resetDelay);
        return true;
        
      } catch (fallbackErr) {
        setError('Failed to copy to clipboard');
        return false;
      }
    }
  }, [resetDelay]);

  const reset = useCallback(() => {
    setCopied(false);
    setError(null);
  }, []);

  return {
    copied,
    error,
    copy,
    reset,
  };
}

export default useCopyToClipboard;
