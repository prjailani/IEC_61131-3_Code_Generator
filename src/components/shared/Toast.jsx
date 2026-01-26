/**
 * Toast Notification Component
 * Displays temporary notification messages
 */

import React, { useEffect } from 'react';
import { UI } from '../../config/constants';

export function Toast({ 
  message, 
  type = 'success', 
  onClose, 
  duration = UI.TOAST_DURATION 
}) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [onClose, duration]);

  return (
    <div className={`toast toast-${type}`} role="alert" aria-live="polite">
      <span className="toast-message">{message}</span>
      <button 
        onClick={onClose} 
        className="toast-close" 
        aria-label="Close notification"
      >
        ×
      </button>
    </div>
  );
}

export default Toast;
