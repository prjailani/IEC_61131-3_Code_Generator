/**
 * Variable Row Component
 * Single row in the variables table
 */

import React, { useCallback } from 'react';
import { IEC_DATA_TYPES } from '../../config/constants';

export function VariableRow({ 
  variable, 
  isEditing, 
  onEdit, 
  onSave, 
  onChange, 
  onDelete 
}) {
  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    onChange(variable.id, { [name]: value });
  }, [variable.id, onChange]);

  const handleBlur = useCallback((e) => {
    const { name, value } = e.target;
    onChange(variable.id, { [name]: value.trim() });
  }, [variable.id, onChange]);

  const handleEditSave = useCallback(() => {
    if (isEditing) {
      onSave(variable.id);
    } else {
      onEdit(variable.id);
    }
  }, [isEditing, variable.id, onEdit, onSave]);

  const handleDelete = useCallback(() => {
    onDelete(variable.id, variable.deviceName);
  }, [variable.id, variable.deviceName, onDelete]);

  return (
    <tr>
      <td>
        <input
          type="text"
          name="deviceName"
          value={variable.deviceName}
          onChange={handleChange}
          onBlur={handleBlur}
          className="table-input"
          disabled={!isEditing}
          aria-label={`Device name for ${variable.deviceName}`}
        />
      </td>
      <td>
        <select
          name="dataType"
          value={variable.dataType}
          onChange={handleChange}
          className="table-input"
          disabled={!isEditing}
          aria-label={`Data type for ${variable.deviceName}`}
        >
          {IEC_DATA_TYPES.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
      </td>
      <td>
        <input
          type="text"
          name="range"
          value={variable.range || ''}
          onChange={handleChange}
          onBlur={handleBlur}
          className="table-input"
          disabled={!isEditing}
          aria-label={`Range for ${variable.deviceName}`}
        />
      </td>
      <td>
        <input
          type="text"
          name="MetaData"
          value={variable.MetaData || ''}
          onChange={handleChange}
          onBlur={handleBlur}
          className="table-input"
          disabled={!isEditing}
          aria-label={`Description for ${variable.deviceName}`}
        />
      </td>
      <td>
        <div className="table-actions">
          <button
            onClick={handleEditSave}
            className="btn btn-primary btn-table"
            aria-label={isEditing ? `Save ${variable.deviceName}` : `Edit ${variable.deviceName}`}
          >
            {isEditing ? 'Save' : 'Edit'}
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className="btn btn-danger btn-table"
            aria-label={`Delete ${variable.deviceName}`}
          >
            Delete
          </button>
        </div>
      </td>
    </tr>
  );
}

export default VariableRow;
