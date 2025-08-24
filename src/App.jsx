import React, { useState } from 'react';

// The main application component
export default function App() {
  const [narrativeText, setNarrativeText] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);


  const handleGenerateCode = async () => {
    // Clear previous results and errors.
    setGeneratedCode('');
    setError(null);
    setIsLoading(true);

    try {
      // Send a POST request to the FastAPI backend.
      // IMPORTANT: Replace the URL below with the actual URL of your friend's FastAPI backend.
      // The backend should have an endpoint that accepts a JSON body with a "narrative" key.
      const response = await fetch('http://127.0.0.1:8000/generate-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Send the user's narrative in the request body.
        body: JSON.stringify({ narrative: narrativeText }),
      });

      // Check if the response was successful.
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Parse the JSON response.
      const data = await response.json();
      
      // The backend should return the generated code in a "code" key.
      if (data.code) {
        setGeneratedCode(data.code);
      } else {
        setError('API response did not contain "code" key.');
      }
    } catch (e) {
      // Catch and display any network or API-related errors.
      setError(`Failed to fetch: ${e.message}. Please check your backend server.`);
      console.error('There was a problem with the fetch operation:', e);
    } finally {
      // Always set loading to false, regardless of success or failure.
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Container for the entire application, centered with a max-width */}
      <div className="card">
        {/* Title and description */}
        <h1 className="title">
          Narrative to ST Code
        </h1>
        <p className="description">
          Enter a natural language description below to generate IEC 61131 Structured Text code.
        </p>

        {/* Input area */}
        <div className="input-area">
          <textarea
            className="text-input"
            placeholder="e.g., If the temperature is greater than 100 degrees Celsius, then turn off the heater."
            value={narrativeText}
            onChange={(e) => setNarrativeText(e.target.value)}
          ></textarea>
        </div>

        {/* Button to trigger code generation */}
        <div className="button-container">
          <button
            onClick={handleGenerateCode}
            disabled={isLoading || !narrativeText.trim()}
            className="generate-button"
          >
            {isLoading ? 'Generating...' : 'Generate Code'}
          </button>
        </div>

        {/* Display area for output and messages */}
        <div>
          {/* Display loading message */}
          {isLoading && (
            <p className="loading-message">
              Generating code...
            </p>
          )}

          {/* Display error message */}
          {error && (
            <div className="error-box">
              <p className="error-title">Error:</p>
              <p className="error-message">{error}</p>
            </div>
          )}

          {/* Display the generated code */}
          {generatedCode && (
            <div className="code-box">
              <h2 className="code-title">Generated IEC 61131-3 Structured Text</h2>
              <pre className="code-block">
                <code className="code">{generatedCode}</code>
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
