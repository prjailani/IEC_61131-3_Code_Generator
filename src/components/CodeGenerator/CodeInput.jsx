/**
 * Code Input Component
 * Textarea for entering natural language descriptions
 */

import React from 'react';
import { VALIDATION } from '../../config/constants';

export function CodeInput({ 
  value, 
  onChange, 
  onKeyDown,
  disabled = false,
  placeholder = "e.g., If the temperature is greater than 100 degrees Celsius, then turn off the heater.",
}) {
  const charCount = value.length;
  const maxLength = VALIDATION.NARRATIVE_MAX_LENGTH;
  const isNearLimit = charCount > maxLength * 0.9;

  return (
    <div className="code-input-container">
      <textarea
        className="input-textarea"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        disabled={disabled}
        maxLength={maxLength}
        aria-label="Enter your natural language instruction"
      />
      <div className="input-footer">
        <p className="input-hint">
          Press Ctrl+Enter to generate, or click the button below.
        </p>
        <span className={`char-count ${isNearLimit ? 'char-count-warning' : ''}`}>
          {charCount} / {maxLength}
        </span>
      </div>
    </div>
  );
}

export default CodeInput;
