/**
 * Loading Spinner Component
 * Displays loading state with optional message
 */

import React from 'react';

export function LoadingSpinner({ message = 'Loading...', size = 'medium' }) {
  const sizeClass = {
    small: 'loading-spinner-sm',
    medium: '',
    large: 'loading-spinner-lg',
  }[size];

  return (
    <div className="loading-container" role="status" aria-live="polite">
      <div 
        className={`loading-spinner ${sizeClass}`} 
        aria-hidden="true"
      />
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
}

export default LoadingSpinner;
