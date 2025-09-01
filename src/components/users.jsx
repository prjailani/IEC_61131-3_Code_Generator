import React, { useState, useEffect } from 'react';
// import './index.css';

export default function Users({ onGoBack }) {
  const [variables, setVariables] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [editingId, setEditingId] = useState(null);

  // --- NEW: State for the search term ---
  const [searchTerm, setSearchTerm] = useState('');

  const [newVariableForm, setNewVariableForm] = useState({
    deviceName: '',
    dataType: 'BOOL',
    range: '',
    initialValue: '',
  });

  const allDataTypes = [
    "BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", "UDINT", "ULINT",
    "REAL", "LREAL", "BYTE", "WORD", "DWORD", "LWORD", "STRING", "TIME", "DATE"
  ];
  
  const fetchVariables = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/get-variables');
      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Failed to fetch: ${response.statusText} - ${errorData}`);
      }
      const data = await response.json();
      const variablesWithId = data.variables.map(v => ({ 
        ...v, 
        id: v._id ? v._id.toString() : Date.now() + Math.random(),
        initialValue: v.initialValue || ''
      }));
      setVariables(variablesWithId);
    } catch (e) {
      setError(e.message);
      console.error("Fetch error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const saveVariables = async () => {
    setIsSaving(true);
    setError(null);
    const variablesToSend = variables.map(({ id, ...rest }) => rest);

    try {
      const response = await fetch('http://127.0.0.1:8000/save-variables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variables: variablesToSend }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.status === 'ok') {
        alert('Variables successfully saved!');
        fetchVariables(); // Refresh data from server
      } else {
        setError(data.message || 'Failed to save variables.');
      }
    } catch (e) {
      setError(`Failed to save data: ${e.message}`);
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    fetchVariables();
  }, []);

  const handleNewVariableInputChange = (event) => {
    const { name, value } = event.target;
    setNewVariableForm((prev) => ({ ...prev, [name]: value }));
  };

  const addVariableRow = () => {
    if (!newVariableForm.deviceName) {
        alert("Device Name cannot be empty.");
        return;
    }
    setVariables([...variables, { 
      id: Date.now().toString(), 
      ...newVariableForm,
    }]);
    setNewVariableForm({ deviceName: '', dataType: 'BOOL', range: '', initialValue: '' });
  };
  
  const handleInputChange = (id, event) => {
    const { name, value } = event.target;
    setVariables(variables.map(v => v.id === id ? { ...v, [name]: value } : v));
  };
  
  const removeVariableRow = (id) => {
    setVariables(variables.filter(v => v.id !== id));
  };
  
  const handleEditSave = (variable) => {
    if (editingId === variable.id) {
        setEditingId(null); // Exit edit mode
    } else {
        setEditingId(variable.id); // Enter edit mode
    }
  }

  // --- NEW: Filter variables based on the search term before rendering ---
  const filteredVariables = variables.filter(variable =>
    variable.deviceName.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="app-container">
      <div className="card">
        <div className="switch-container">
          <button onClick={onGoBack} className="btn btn-secondary">
            Go to Main Page
          </button>
          <button className="btn btn-secondary" disabled>
            Go to Variables
          </button>
        </div>

        <h1 className="title">Config Variables</h1>
        {error && (
          <div className="error-box">
            <p className="error-title">Connection Error</p>
            <p className="error-message">{error}</p>
          </div>
        )}

        <div className="add-variable-container">
            <form className="add-variable-form" onSubmit={(e) => { e.preventDefault(); addVariableRow(); }}>
                <input
                    type="text"
                    name="deviceName"
                    placeholder="Device Name"
                    value={newVariableForm.deviceName}
                    onChange={handleNewVariableInputChange}
                    className="input-base"
                />
                <select
                    name="dataType"
                    value={newVariableForm.dataType}
                    onChange={handleNewVariableInputChange}
                    className="input-base"
                >
                    {allDataTypes.map(type => <option key={type} value={type}>{type}</option>)}
                </select>
                <input
                    type="text"
                    name="range"
                    placeholder="Range"
                    value={newVariableForm.range}
                    onChange={handleNewVariableInputChange}
                    className="input-base"
                />
                <input
                    type="text"
                    name="initialValue"
                    placeholder="Additional"
                    value={newVariableForm.initialValue}
                    onChange={handleNewVariableInputChange}
                    className="input-base"
                />
                <button type="submit" className="btn btn-primary">
                    Add Variable
                </button>
            </form>
        </div>

        {isLoading ? <p className="loading-message">Loading variables...</p> : (
          <>
            {/* --- NEW: Search Bar --- */}
            <div className="search-container">
              <input
                type="text"
                placeholder="Search by Device Name..."
                className="input-base search-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            {/* --- MODIFIED: Added scrollable container --- */}
            <div className="table-container">
              <table className="variables-table">
                <thead>
                  <tr>
                    <th>Device Name</th>
                    <th>Data Type</th>
                    <th>Range</th>
                    <th>Additional</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {/* --- MODIFIED: Map over filteredVariables instead of variables --- */}
                  {filteredVariables.length > 0 ? filteredVariables.map((variable) => (
                    <tr key={variable.id}>
                      <td>
                        <input
                          type="text" name="deviceName"
                          value={variable.deviceName}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          className="table-input"
                          disabled={editingId !== variable.id}
                        />
                      </td>
                      <td>
                        <select
                          name="dataType"
                          value={variable.dataType}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          className="table-input"
                          disabled={editingId !== variable.id}
                        >
                          {allDataTypes.map(type => <option key={type} value={type}>{type}</option>)}
                        </select>
                      </td>
                      <td>
                        <input
                          type="text" name="range"
                          value={variable.range}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          className="table-input"
                          disabled={editingId !== variable.id}
                        />
                      </td>
                      <td>
                        <input
                          type="text" name="initialValue"
                          value={variable.initialValue}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          className="table-input"
                          disabled={editingId !== variable.id}
                        />
                      </td>
                      <td>
                        <div className="table-actions">
                            <button onClick={() => handleEditSave(variable)} className="btn btn-primary btn-table">
                                {editingId === variable.id ? 'Save' : 'Edit'}
                            </button>
                            <button type="button" onClick={() => removeVariableRow(variable.id)} className="btn btn-danger btn-table">
                                Delete
                            </button>
                        </div>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan="5">
                        {/* --- MODIFIED: Smarter message for no results --- */}
                        <p className="no-variables-message">
                          {variables.length === 0 
                            ? "No variables found. Add one above to get started." 
                            : "No variables match your search."}
                        </p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {variables.length > 0 && (
                <div className="save-all-container">
                    <button 
                        type="button" 
                        onClick={saveVariables} 
                        className="btn btn-primary"
                        disabled={isSaving}
                    >
                        {isSaving ? 'Saving...' : 'Save All Changes to DB'}
                    </button>
                </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}