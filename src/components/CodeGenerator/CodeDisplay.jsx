/**
 * Code Display Component
 * Displays generated code with copy functionality
 */

import React, { useRef } from 'react';
import { IoCopyOutline, IoCheckmarkOutline } from 'react-icons/io5';
import { useCopyToClipboard } from '../../hooks';

export function CodeDisplay({ code, title = 'Generated IEC 61131-3 Structured Text' }) {
  const codeRef = useRef(null);
  const { copied, copy } = useCopyToClipboard();

  const handleCopy = () => {
    if (codeRef.current) {
      copy(codeRef.current.textContent);
    }
  };

  if (!code) return null;

  return (
    <div className="code-box">
      <h2 className="code-title">
        {title}
        <button 
          type="button" 
          onClick={handleCopy} 
          className="btn-primary btn-copy"
          aria-label={copied ? 'Copied!' : 'Copy code to clipboard'}
          title={copied ? 'Copied!' : 'Copy to clipboard'}
        >
          {copied ? <IoCheckmarkOutline /> : <IoCopyOutline />}
        </button>
      </h2>
      <pre className="code-block">
        <code ref={codeRef} className="codeBox">{code}</code>
      </pre>
    </div>
  );
}

export default CodeDisplay;
