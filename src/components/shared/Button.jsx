/**
 * Button Component
 * Reusable button with variants
 */

import React from 'react';

export function Button({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  type = 'button',
  onClick,
  className = '',
  ...props
}) {
  const sizeClass = {
    small: 'btn-sm',
    medium: '',
    large: 'btn-lg',
  }[size];

  const variantClass = `btn-${variant}`;

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`btn ${variantClass} ${sizeClass} ${className}`.trim()}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}

export default Button;
