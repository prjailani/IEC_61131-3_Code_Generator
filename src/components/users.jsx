import React, { useState, useEffect, useCallback, useMemo } from 'react';

// API base URL - uses environment variable or falls back to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Toast notification component
function Toast({ message, type, onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`toast toast-${type}`} role="alert">
      <span>{message}</span>
      <button onClick={onClose} className="toast-close" aria-label="Close notification">×</button>
    </div>
  );
}

export default function Users({ onGoBack }) {
  const [variables, setVariables] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [toast, setToast] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const [newVariableForm, setNewVariableForm] = useState({
    deviceName: '',
    dataType: 'BOOL',
    range: '',
    MetaData: '',
  });

  const allDataTypes = useMemo(() => [
    "BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", "UDINT", "ULINT",
    "REAL", "LREAL", "BYTE", "WORD", "DWORD", "LWORD", "STRING", "TIME", "DATE"
  ], []);

  // Show toast notification
  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
  }, []);

  const fetchVariables = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(`${API_BASE_URL}/get-variables`, {
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Failed to fetch: ${response.statusText} - ${errorData}`);
      }
      
      const data = await response.json();
      
      if (!data.variables || !Array.isArray(data.variables)) {
        throw new Error('Invalid response format from server');
      }
      
      const variablesWithId = data.variables.map((v, index) => ({ 
        ...v, 
        id: v._id?.toString() || `var-${Date.now()}-${index}-${crypto.randomUUID?.() || Math.random().toString(36).substr(2, 9)}`,
        MetaData: v.MetaData || ''
      }));
      setVariables(variablesWithId);
    } catch (e) {
      if (e.name === 'AbortError') {
        setError('Request timed out. Please check your connection.');
      } else if (e.message === 'Failed to fetch') {
        setError('Unable to connect to the server. Please ensure the backend is running.');
      } else {
        setError(e.message);
      }
      console.error("Fetch error:", e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveVariables = useCallback(async () => {
    setIsSaving(true);
    setError(null);
    
    const variablesToSend = variables.map(({ id, ...rest }) => ({
      ...rest,
      deviceName: rest.deviceName.trim(),
      range: rest.range ? rest.range.trim() : '',
      MetaData: rest.MetaData ? rest.MetaData.trim() : '',
    }));

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(`${API_BASE_URL}/save-variables`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variables: variablesToSend }),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.status === 'ok') {
        showToast('Variables successfully saved!', 'success');
        fetchVariables(); 
      } else {
        setError(data.message || 'Failed to save variables.');
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        setError('Save request timed out. Please try again.');
      } else {
        setError(`Failed to save data: ${e.message}`);
      }
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  }, [variables, fetchVariables, showToast]);

  useEffect(() => {
    fetchVariables();
  }, [fetchVariables]);

  const handleNewVariableInputChange = useCallback((event) => {
    const { name, value } = event.target;
    setNewVariableForm((prev) => ({ ...prev, [name]: value }));
  }, []);

  const handleNewVariableBlur = useCallback((event) => {
    const { name, value } = event.target;
    setNewVariableForm((prev) => ({ ...prev, [name]: value.trim() }));
  }, []);

  const addVariableRow = useCallback(() => {
    const trimmedDeviceName = newVariableForm.deviceName.trim();

    if (!trimmedDeviceName) {
      showToast("Device Name cannot be empty.", 'error');
      return;
    }

    // Validate device name format (alphanumeric and underscore only)
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(trimmedDeviceName)) {
      showToast("Device Name must start with a letter or underscore and contain only alphanumeric characters.", 'error');
      return;
    }

    const isDuplicate = variables.some(
      variable => variable.deviceName.toLowerCase() === trimmedDeviceName.toLowerCase()
    );

    if (isDuplicate) {
      showToast(`A device with the name "${trimmedDeviceName}" already exists.`, 'error');
      return; 
    }

    const newId = `var-${Date.now()}-${crypto.randomUUID?.() || Math.random().toString(36).substr(2, 9)}`;
    
    setVariables(prev => [...prev, { 
      id: newId, 
      ...newVariableForm,
      deviceName: trimmedDeviceName, 
    }]);
    setNewVariableForm({ deviceName: '', dataType: 'BOOL', range: '', MetaData: '' });
    showToast(`Variable "${trimmedDeviceName}" added.`, 'success');
  }, [newVariableForm, variables, showToast]);
  
  const handleInputChange = useCallback((id, event) => {
    const { name, value } = event.target;
    setVariables(prev => prev.map(v => v.id === id ? { ...v, [name]: value } : v));
  }, []);
  
  const handleTableInputBlur = useCallback((id, event) => {
    const { name, value } = event.target;
    setVariables(prev => prev.map(v => v.id === id ? { ...v, [name]: value.trim() } : v));
  }, []);
  
  const removeVariableRow = useCallback((id, deviceName) => {
    setDeleteConfirm({ id, deviceName });
  }, []);

  const confirmDelete = useCallback(() => {
    if (deleteConfirm) {
      setVariables(prev => prev.filter(v => v.id !== deleteConfirm.id));
      showToast(`Variable "${deleteConfirm.deviceName}" removed.`, 'success');
      setDeleteConfirm(null);
    }
  }, [deleteConfirm, showToast]);

  const cancelDelete = useCallback(() => {
    setDeleteConfirm(null);
  }, []);
  
  const handleEditSave = useCallback((variable) => {
    if (editingId === variable.id) {
      setEditingId(null);
      showToast('Changes saved locally. Click "Save All Changes" to persist to database.', 'info');
    } else {
      setEditingId(variable.id);
    }
  }, [editingId, showToast]);

  // Memoized filtered variables with debounce effect
  const filteredVariables = useMemo(() => {
    const searchLower = searchTerm.toLowerCase();
    return variables.filter(variable =>
      variable.deviceName.toLowerCase().includes(searchLower) ||
      variable.dataType.toLowerCase().includes(searchLower) ||
      (variable.MetaData && variable.MetaData.toLowerCase().includes(searchLower))
    );
  }, [variables, searchTerm]);

  return (
    <div className="app-container">
      {/* Toast notifications */}
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}

      {/* Delete confirmation modal */}
      {deleteConfirm && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-content">
            <h3 className="modal-title">Confirm Delete</h3>
            <p>Are you sure you want to delete "{deleteConfirm.deviceName}"?</p>
            <div className="modal-actions">
              <button onClick={cancelDelete} className="btn btn-secondary">Cancel</button>
              <button onClick={confirmDelete} className="btn btn-danger">Delete</button>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="switch-container">
          <button onClick={onGoBack} className="btn btn-secondary" aria-label="Return to main page">
            Go to Main Page
          </button>
        </div>

        <h1 className="title">Config Variables</h1>
        
        {error && (
          <div className="error-box" role="alert">
            <p className="error-title">Connection Error</p>
            <p className="error-message">{error}</p>
            <button onClick={fetchVariables} className="btn btn-secondary" style={{ marginTop: '1rem' }}>
              Retry
            </button>
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
              onBlur={handleNewVariableBlur} 
              className="input-base"
              aria-label="Device name"
              pattern="[A-Za-z_][A-Za-z0-9_]*"
              title="Must start with a letter or underscore, followed by alphanumeric characters"
            />
            <select
              name="dataType"
              value={newVariableForm.dataType}
              onChange={handleNewVariableInputChange}
              className="input-base"
              aria-label="Data type"
            >
              {allDataTypes.map(type => <option key={type} value={type}>{type}</option>)}
            </select>
            <input
              type="text"
              name="range"
              placeholder="Range (e.g., 0-100)"
              value={newVariableForm.range}
              onChange={handleNewVariableInputChange}
              onBlur={handleNewVariableBlur} 
              className="input-base"
              aria-label="Value range"
              title="Specify the valid range for this variable (e.g., 0-100)"
            />
            <input
              type="text"
              name="MetaData"
              placeholder="Description / Additional Info"
              value={newVariableForm.MetaData}
              onChange={handleNewVariableInputChange}
              onBlur={handleNewVariableBlur} 
              className="input-base"
              aria-label="Additional metadata"
              title="Add any additional information or description for this variable"
            />
            <button type="submit" className="btn btn-primary" aria-label="Add new variable">
              Add Variable
            </button>
          </form>
        </div>

        {isLoading ? (
          <div className="loading-container">
            <div className="loading-spinner" aria-hidden="true"></div>
            <p className="loading-message">Loading variables...</p>
          </div>
        ) : (
          <>
            <div className="search-container">
              <input
                type="text"
                placeholder="Search by Device Name, Type, or Description..."
                className="input-base search-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                aria-label="Search variables"
              />
              {searchTerm && (
                <button 
                  className="search-clear" 
                  onClick={() => setSearchTerm('')}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}
            </div>
            
            <div className="table-container">
              <table className="variables-table">
                <thead>
                  <tr>
                    <th scope="col">Device Name</th>
                    <th scope="col">Data Type</th>
                    <th scope="col">Range</th>
                    <th scope="col">Description</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVariables.length > 0 ? filteredVariables.map((variable) => (
                    <tr key={variable.id}>
                      <td>
                        <input
                          type="text" 
                          name="deviceName"
                          value={variable.deviceName}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          onBlur={(e) => handleTableInputBlur(variable.id, e)}
                          className="table-input"
                          disabled={editingId !== variable.id}
                          aria-label={`Device name for ${variable.deviceName}`}
                        />
                      </td>
                      <td>
                        <select
                          name="dataType"
                          value={variable.dataType}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          className="table-input"
                          disabled={editingId !== variable.id}
                          aria-label={`Data type for ${variable.deviceName}`}
                        >
                          {allDataTypes.map(type => <option key={type} value={type}>{type}</option>)}
                        </select>
                      </td>
                      <td>
                        <input
                          type="text" 
                          name="range"
                          value={variable.range}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          onBlur={(e) => handleTableInputBlur(variable.id, e)} 
                          className="table-input"
                          disabled={editingId !== variable.id}
                          aria-label={`Range for ${variable.deviceName}`}
                        />
                      </td>
                      <td>
                        <input
                          type="text" 
                          name="MetaData"
                          value={variable.MetaData}
                          onChange={(e) => handleInputChange(variable.id, e)}
                          onBlur={(e) => handleTableInputBlur(variable.id, e)} 
                          className="table-input"
                          disabled={editingId !== variable.id}
                          aria-label={`Description for ${variable.deviceName}`}
                        />
                      </td>
                      <td>
                        <div className="table-actions">
                          <button 
                            onClick={() => handleEditSave(variable)} 
                            className="btn btn-primary btn-table"
                            aria-label={editingId === variable.id ? `Save changes for ${variable.deviceName}` : `Edit ${variable.deviceName}`}
                          >
                            {editingId === variable.id ? 'Save' : 'Edit'}
                          </button>
                          <button 
                            type="button" 
                            onClick={() => removeVariableRow(variable.id, variable.deviceName)} 
                            className="btn btn-danger btn-table"
                            aria-label={`Delete ${variable.deviceName}`}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan="5">
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

            <div className="table-info">
              <span>{filteredVariables.length} of {variables.length} variables shown</span>
            </div>

            {variables.length > 0 && (
              <div className="save-all-container">
                <button 
                  type="button" 
                  onClick={saveVariables} 
                  className="btn btn-primary"
                  disabled={isSaving}
                  aria-label={isSaving ? 'Saving changes...' : 'Save all changes to database'}
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
