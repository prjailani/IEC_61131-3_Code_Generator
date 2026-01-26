/**
 * Code Generator Component
 * Main component for generating IEC 61131-3 code from natural language
 */

import React, { useState, useCallback } from 'react';
import { useCodeGeneration } from '../../hooks';
import { LoadingSpinner, ErrorDisplay } from '../shared';
import CodeInput from './CodeInput';
import CodeDisplay from './CodeDisplay';

export function CodeGenerator() {
  const [narrativeText, setNarrativeText] = useState('');
  const { generatedCode, isLoading, error, generate, clearError } = useCodeGeneration();

  const handleGenerate = useCallback(async () => {
    await generate(narrativeText);
  }, [generate, narrativeText]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && e.ctrlKey && !isLoading && narrativeText.trim()) {
      handleGenerate();
    }
  }, [handleGenerate, isLoading, narrativeText]);

  const canGenerate = !isLoading && narrativeText.trim().length > 0;

  return (
    <>
      <CodeInput
        value={narrativeText}
        onChange={(value) => {
          setNarrativeText(value);
          if (error) clearError();
        }}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
      />

      <div className="generate-button-container">
        <button
          onClick={handleGenerate}
          disabled={!canGenerate}
          className="btn btn-primary btn-generate"
          aria-label={isLoading ? 'Generating code...' : 'Generate IEC 61131-3 code'}
        >
          {isLoading ? 'Generating...' : 'Generate Code'}
        </button>
      </div>

      <div className="code-output-section">
        {isLoading && (
          <LoadingSpinner message="Generating code, please wait..." />
        )}

        {error && !isLoading && (
          <ErrorDisplay 
            title="Generation Error" 
            message={error} 
          />
        )}

        {generatedCode && !isLoading && (
          <CodeDisplay code={generatedCode} />
        )}

        {!isLoading && !error && !generatedCode && (
          <div className="empty-state">
            <p className="empty-state-text">
              Enter a natural language description above and click "Generate Code" 
              to create IEC 61131-3 Structured Text.
            </p>
          </div>
        )}
      </div>
    </>
  );
}

export default CodeGenerator;
