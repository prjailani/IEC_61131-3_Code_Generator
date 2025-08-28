import React, { useState } from 'react';
import './index.css';

export default function Users({ onGoBack }) {
  // Define all the data types from your specification.
  const allDataTypes = [
    // Elementary
    "BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", "UDINT", "ULINT",
    "REAL", "LREAL", "BYTE", "WORD", "DWORD", "LWORD",
    "CHAR", "WCHAR", "STRING", "WSTRING",
    "TIME", "DATE", "TIME_OF_DAY", "DATE_AND_TIME",
    // Generic
    "ANY", "ANY_DERIVED", "ANY_ELEMENTARY", "ANY_MAGNITUDE",
    "ANY_NUM", "ANY_REAL", "ANY_INT", "ANY_BIT", "ANY_STRING", "ANY_DATE",
    // Built-in Function Block Types
    "TON", "TOF", "TP", "CTU", "CTD", "CTUD", "R_TRIG", "F_TRIG",
    "PID", "PI", "PD", "MC_MOVEABSOLUTE", "MC_MOVERELATIVE", "MC_HOME", "MC_STOP", "MC_RESET",
    "TSEND", "TRCV", "TCON", "TDISCON", "READ_VAR", "WRITE_VAR"
  ];
  
  const [variables, setVariables] = useState([
    { id: Date.now().toString(), deviceName: '', dataType: allDataTypes[0], range: '' }
  ]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  // Function to add a new empty row to the form.
  const addVariableRow = () => {
    setVariables([...variables, { id: Date.now().toString(), deviceName: '', dataType: allDataTypes[0], range: '' }]);
  };

  // Function to handle changes in a specific form field.
  const handleInputChange = (id, event) => {
    const { name, value } = event.target;
    setVariables(variables.map(variable => {
      if (variable.id === id) {
        return { ...variable, [name]: value };
      }
      return variable;
    }));
  };
  
  // Function to remove a variable row.
  const removeVariableRow = (id) => {
    setVariables(variables.filter(variable => variable.id !== id));
  };

  const handleSaveVariables = async () => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage('');

    try {
      const variablesToSave = variables.filter(v => v.deviceName.trim() !== '');

      if (variablesToSave.length === 0) {
        setError("Please add at least one variable to save.");
        setIsSaving(false);
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/save-variables', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ variables: variablesToSave }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccessMessage(result.message || 'Variables saved successfully!');
    } catch (e) {
      console.error("Error saving variables: ", e);
      setError(`Failed to save variables: ${e.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="app-container">
      <div className="card">
        <div className="switch-container">
          <button onClick={onGoBack} className="switch-button">
            Go to Main Page
          </button>
          <button className="switch-button" disabled>
            Go to Users Page
          </button>
        </div>
        
        <h1 className="title">Define Device Variables</h1>
        <p className="description">
          Create a list of all your inputs, outputs, and internal variables.
        </p>

        <form onSubmit={(e) => { e.preventDefault(); handleSaveVariables(); }}>
          {variables.length > 0 ? (
            variables.map((variable) => (
              <div key={variable.id} className="variable-row">
                <input
                  type="text"
                  name="deviceName"
                  placeholder="Device Name (e.g., StartButton)"
                  value={variable.deviceName}
                  onChange={(e) => handleInputChange(variable.id, e)}
                  className="text-input-small"
                  required
                />
                <select
                  name="dataType"
                  value={variable.dataType}
                  onChange={(e) => handleInputChange(variable.id, e)}
                  className="select-input"
                >
                  {allDataTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                <input
                  type="text"
                  name="range"
                  placeholder="Range (e.g., 0..255)"
                  value={variable.range}
                  onChange={(e) => handleInputChange(variable.id, e)}
                  className="text-input-small"
                />
                <button type="button" onClick={() => removeVariableRow(variable.id)} className="remove-button">
                  &times;
                </button>
              </div>
            ))
          ) : (
            <p className="no-variables-message">No variables defined yet. Click "Add Variable" to start.</p>
          )}

          <div className="button-container-small">
            <button type="button" onClick={addVariableRow} className="add-button">
              + Add Variable
            </button>
          </div>

          <div className="button-container" style={{ marginTop: '2rem' }}>
            <button type="submit" disabled={isSaving} className="generate-button">
              {isSaving ? 'Saving...' : 'Save Variables'}
            </button>
          </div>
        </form>

        {successMessage && (
          <p className="success-message">{successMessage}</p>
        )}
        {error && (
          <div className="error-box">
            <p className="error-title">Error:</p>
            <p className="error-message">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
