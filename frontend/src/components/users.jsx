import React, { useState, useEffect } from 'react';

export default function Users({ onGoBack }) {
  const [variables, setVariables] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const [newVariableForm, setNewVariableForm] = useState({
    name: '',
    dataType: 'BOOL',
    min: '',
    max: '',
    description: '',
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
        description: v.description || '',
        min: v.min || '',
        max: v.max || ''
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
    
    const variablesToSend = variables.map(({ id, ...rest }) => ({
      ...rest,
      name: rest.name.trim(),
      min: rest.min ? rest.min.trim() : '',
      max: rest.max ? rest.max.trim() : '',
      description: rest.description ? rest.description.trim() : '',
    }));

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
        fetchVariables(); 
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

  const handleNewVariableBlur = (event) => {
    const { name, value } = event.target;
    setNewVariableForm((prev) => ({ ...prev, [name]: value.trim() }));
  };

  const addVariableRow = () => {
    const trimmedName = newVariableForm.name.trim();

    if (!trimmedName) {
        alert("Device Name cannot be empty.");
        return;
    }

    const isDuplicate = variables.some(
      variable => variable.name.toLowerCase() === trimmedName.toLowerCase()
    );

    if (isDuplicate) {
      alert(`A device with the name "${trimmedName}" already exists. Please use a unique name.`);
      return; 
    }

    setVariables([...variables, { 
      id: Date.now().toString(), 
      ...newVariableForm,
      name: trimmedName, 
    }]);
    setNewVariableForm({ name: '', dataType: 'BOOL', min: '', max: '', description: '' });
  };
  
  const handleInputChange = (id, event) => {
    const { name, value } = event.target;
    setVariables(variables.map(v => v.id === id ? { ...v, [name]: value } : v));
  };
  
  const handleTableInputBlur = (id, event) => {
    const { name, value } = event.target;
    setVariables(variables.map(v => v.id === id ? { ...v, [name]: value.trim() } : v));
  };
  
  const removeVariableRow = (id) => {
    setVariables(variables.filter(v => v.id !== id));
  };
  
  const handleEditSave = (variable) => {
    if (editingId === variable.id) {
        setEditingId(null); 
    } else {
        setEditingId(variable.id); 
    }
  }

  const filteredVariables = variables.filter(variable =>
    variable.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="app-container">
      <div className="card">
        <div className="switch-container">
          <button onClick={onGoBack} className="btn btn-secondary">
            Go to Main Page
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
                    name="name"
                    placeholder="Device Name"
                    value={newVariableForm.name}
                    onChange={handleNewVariableInputChange}
                    onBlur={handleNewVariableBlur} 
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
                    name="min"
                    placeholder="Min"
                    value={newVariableForm.min}
                    onChange={handleNewVariableInputChange}
                    onBlur={handleNewVariableBlur} 
                    className="input-base"
                />
                <input
                    type="text"
                    name="max"
                    placeholder="Max"
                    value={newVariableForm.max}
                    onChange={handleNewVariableInputChange}
                    onBlur={handleNewVariableBlur} 
                    className="input-base"
                />
                <input
                    type="text"
                    name="description"
                    placeholder="Description"
                    value={newVariableForm.description}
                    onChange={handleNewVariableInputChange}
                    onBlur={handleNewVariableBlur} 
                    className="input-base"
                />
                <button type="submit" className="btn btn-primary">
                    Add Variable
                </button>
            </form>
        </div>

        {isLoading ? <p className="loading-message">Loading variables...</p> : (
          <>
            <div className="search-container">
              <input
                type="text"
                placeholder="Search by Device Name..."
                className="input-base search-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <div className="table-container">
              <table className="variables-table">
                <thead>
                  <tr>
                    <th>Device Name</th>
                    <th>Data Type</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Description</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVariables.length > 0 ? filteredVariables.map((variable) => (
                    <tr key={variable.id}>
                      <td>
                        <input
                          type="text" name="name"
                          value={variable.name}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          onBlur={(e) => handleTableInputBlur(variable.id, e)}
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
                          type="text" name="min"
                          value={variable.min}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          onBlur={(e) => handleTableInputBlur(variable.id, e)} 
                          className="table-input"
                          disabled={editingId !== variable.id}
                        />
                      </td>
                      <td>
                        <input
                          type="text" name="max"
                          value={variable.max}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          onBlur={(e) => handleTableInputBlur(variable.id, e)} 
                          className="table-input"
                          disabled={editingId !== variable.id}
                        />
                      </td>
                      <td>
                        <input
                          type="text" name="description"
                          value={variable.description}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          onBlur={(e) => handleTableInputBlur(variable.id, e)} 
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
                      <td colSpan="7">
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

