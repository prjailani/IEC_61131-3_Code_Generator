/**
 * Variable Table Component
 * Displays variables in a searchable, editable table
 */

import React, { useState, useMemo, useCallback } from 'react';
import VariableRow from './VariableRow';

export function VariableTable({ 
  variables, 
  onUpdate, 
  onDelete,
  onSaveInfo,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [editingId, setEditingId] = useState(null);

  // Filter variables based on search
  const filteredVariables = useMemo(() => {
    const search = searchTerm.toLowerCase();
    return variables.filter(variable =>
      variable.deviceName.toLowerCase().includes(search) ||
      variable.dataType.toLowerCase().includes(search) ||
      (variable.MetaData && variable.MetaData.toLowerCase().includes(search))
    );
  }, [variables, searchTerm]);

  const handleEdit = useCallback((id) => {
    setEditingId(id);
  }, []);

  const handleSave = useCallback((id) => {
    setEditingId(null);
    onSaveInfo?.('Changes saved locally. Click "Save All Changes" to persist to database.');
  }, [onSaveInfo]);

  const handleChange = useCallback((id, updates) => {
    onUpdate(id, updates);
  }, [onUpdate]);

  const clearSearch = useCallback(() => {
    setSearchTerm('');
  }, []);

  return (
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
            onClick={clearSearch}
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
            {filteredVariables.length > 0 ? (
              filteredVariables.map(variable => (
                <VariableRow
                  key={variable.id}
                  variable={variable}
                  isEditing={editingId === variable.id}
                  onEdit={handleEdit}
                  onSave={handleSave}
                  onChange={handleChange}
                  onDelete={onDelete}
                />
              ))
            ) : (
              <tr>
                <td colSpan="5">
                  <p className="no-variables-message">
                    {variables.length === 0
                      ? 'No variables found. Add one above to get started.'
                      : 'No variables match your search.'}
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="table-info">
        <span>
          {filteredVariables.length} of {variables.length} variables shown
        </span>
      </div>
    </>
  );
}

export default VariableTable;
