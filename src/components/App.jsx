import React, { useState } from 'react';
import Users from './users.jsx';


export default function App() {
  const [currentPage, setCurrentPage] = useState('main');
  const [narrativeText, setNarrativeText] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);


  const PROGRAM = {
  rungs: [
    {
      contacts: [
        { type: "NO", label: "06:00 Timer" },
        { type: "NC", label: "19:00 Timer" }
      ],
      coil: { label: "Motor Coil" }
    },
    {
      contacts: [{ type: "NO", label: "Start PB" }],
      coil: { label: "Lamp" }
    }
  ]
};

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
    setGeneratedCode('');
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/generate-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ narrative: narrativeText }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      
      if (data.code) {
        setGeneratedCode(data.code);
      } else {
        setError('API response was successful but did not contain the expected "code" data.');
      }
    } catch (e) {
      setError(`Failed to generate code: ${e.message}. Please ensure the backend server is running and accessible.`);
      console.error('There was a problem with the fetch operation:', e);
    } finally {
      setIsLoading(false);
    }
  };

  if (currentPage === 'users') {
    return <Users onGoBack={() => setCurrentPage('main')} />;
  }

  return (
    <div className="app-container">

       <div className="card">
        <div className="switch-container">
          <button onClick={() => setCurrentPage('users')} className="btn btn-secondary">
            Go to Variables
          </button>
          <button className="btn btn-secondary" disabled>
            Go to Main Page
          </button>
        </div>

        <h1 className="title">
          IEC 61131-3 Code Generator
        </h1>
      
        <div>
         
          <textarea
            className="input-textarea"
            placeholder="e.g., If the temperature is greater than 100 degrees Celsius, then turn off the heater."
            value={narrativeText}
            onChange={(e) => setNarrativeText(e.target.value)}
          ></textarea>
        </div>

        <div className="generate-button-container">
          <button
            onClick={handleGenerateCode}
            disabled={isLoading || !narrativeText.trim()}
            className="btn btn-primary btn-generate"
          >
            {isLoading ? 'Generating...' : 'Generate Code'}
          </button>
        </div>

        <div>
          {isLoading && (
            <p className="loading-message">
              Generating code, please wait...
            </p>
          )}



          {error && (
            <div className="error-box">
              <p className="error-title">An Error Occurred</p>
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
