import React, { useState } from 'react';
import './index.css';
import Users from './users.jsx';

export default function App() {
  const [currentPage, setCurrentPage] = useState('main');
  const [narrativeText, setNarrativeText] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  function copier() {
  // Get the text field
  var copyText = document.getElementsByClassName("codeBox");

  // Select the text field
  // copyText.select();
  // copyText.setSelectionRange(0, 99999); // For mobile devices

   // Copy the text inside the text field
  navigator.clipboard.writeText(copyText[0].textContent);

  // Alert the copied text
  console.log("Copied the text: " + copyText[0].textContent);
}
  const handleGenerateCode = async () => {
    // Clear previous results and errors.
    setGeneratedCode('');
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/generate-code', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ narrative: narrativeText }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.code) {
        setGeneratedCode(data.code);
      } else {
        setError('API response did not contain "code" key.');
      }
    } catch (e) {
      setError(`Failed to fetch: ${e.message}. Please check your backend server.`);
      console.error('There was a problem with the fetch operation:', e);
    } finally {
      setIsLoading(false);
    }
  };

  // Conditional rendering to switch between pages
  if (currentPage === 'users') {
    return <Users onGoBack={() => setCurrentPage('main')} />;
  }

  return (
    <div className="app-container">
      <div className="card">
        {/* Switch interface */}
        <div className="switch-container">
          <button onClick={() => setCurrentPage('users')} className="switch-button">
            Go to Config Page
          </button>
          <button onClick={() => setCurrentPage('main')} className="switch-button" disabled>
            Go to Main Page
          </button>
        </div>

        <h1 className="title">
          Narrative to ST Code
        </h1>
        <p className="description">
          Enter a natural language description below to generate IEC 61131 Structured Text code.
        </p>

        <div className="input-area">
          <textarea
            className="text-input"
            placeholder="e.g., If the temperature is greater than 100 degrees Celsius, then turn off the heater."
            value={narrativeText}
            onChange={(e) => setNarrativeText(e.target.value)}
          ></textarea>
        </div>

        <div className="button-container">
          <button
            onClick={handleGenerateCode}
            disabled={isLoading || !narrativeText.trim()}
            className="generate-button"
          >
            {isLoading ? 'Generating...' : 'Generate Code'}
          </button>
        </div>

        <div>
          {isLoading && (
            <p className="loading-message">
              Generating code...
            </p>
          )}

          {error && (
            <div className="error-box">
              <p className="error-title">Error:</p>
              <p className="error-message">{error}</p>
            </div>
          )}

          {generatedCode && (<>
            
            <div className="code-box">
              <h2 className="code-title">Generated IEC 61131-3 Structured Text  <button type='button' onClick={copier} className='copy-button'><img src="src\assets\copy.png" alt='Copy Button' width="20px"/></button></h2>
              <pre className="code-block">
                <code className="codeBox">{generatedCode}</code>
              </pre>
            </div>
            
            </>
          )}
        </div>
      </div>
    </div>
  );
}
