/**
 * App Component
 * Main application component with page routing
 */

import React, { useState } from 'react';
import { CodeGenerator } from './CodeGenerator';
import { VariablesPage } from './Variables';

// Page constants
const PAGES = {
  MAIN: 'main',
  VARIABLES: 'variables',
};

export default function App() {
  const [currentPage, setCurrentPage] = useState(PAGES.MAIN);

  // Navigate to Variables page
  if (currentPage === PAGES.VARIABLES) {
    return <VariablesPage onGoBack={() => setCurrentPage(PAGES.MAIN)} />;
  }

  // Main code generator page
  return (
    <div className="app-container">
      <div className="card">
        <div className="switch-container">
          <button 
            onClick={() => setCurrentPage(PAGES.VARIABLES)} 
            className="btn btn-secondary"
            aria-label="Navigate to Variables configuration"
          >
            Go to Variables
          </button>
        </div>

        <h1 className="title">
          IEC 61131-3 Code Generator
        </h1>
        
        <CodeGenerator />
      </div>
    </div>
  );
}
