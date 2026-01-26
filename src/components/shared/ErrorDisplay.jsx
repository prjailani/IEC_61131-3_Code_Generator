/**
 * Error Display Component
 * Displays error messages with optional retry action
 */

import React from 'react';

export function ErrorDisplay({ 
  title = 'An Error Occurred', 
  message, 
  onRetry,
  retryText = 'Retry',
}) {
  return (
    <div className="error-box" role="alert">
      <p className="error-title">{title}</p>
      <p className="error-message">{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry} 
          className="btn btn-secondary" 
          style={{ marginTop: '1rem' }}
        >
          {retryText}
        </button>
      )}
    </div>
  );
}

export default ErrorDisplay;
