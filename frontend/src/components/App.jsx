import React, { useState } from 'react';
import Users from './users.jsx';
import { IoCopyOutline } from "react-icons/io5";

// import {AuthContainer}  from "./LoginRegister.jsx"
// import {Logo} from "./../../public/logo.png"
export default function App() {
  const [currentPage, setCurrentPage] = useState('main');
  const [narrativeText, setNarrativeText] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Default example program structure
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
  var copyText = document.getElementsByClassName("codeBox");
  navigator.clipboard.writeText(copyText[0].textContent);
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
      setError(`Failed to generate code: ${e.message.split(':').pop().trim()}`);
      console.log(e.message.split(':').pop().trim())
      console.error('There was a problem with the fetch operation:', );
    } finally {
      setIsLoading(false);
    }
  };

  if (currentPage === 'users') {
    return <Users onGoBack={() => setCurrentPage('main')} />;
  }
 const handleLogout = () => {
    if (onLogout) {
      onLogout();
    }
  };
  return (
    <div className="app-container">
      {/* <img src ={Logo}  alt ="Logo"/> */}
     
       <div className="card">
        <div className="switch-container">
          <button onClick={() => setCurrentPage('users')} className="btn btn-secondary">

            Go to Variables
          </button>

                          <button onClick={handleLogout}  className="btn btn-secondary">Logout</button>

        </div>

        <h1 className="title">
         Txt2PLC -  IEC 61131-3 Code Generator
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
              <h2 className="code-title">Generated IEC 61131-3 Structured Text  <button type='button' onClick={copier} className='btn-primary btn-copy'><IoCopyOutline /></button></h2>
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
