/**
 * Variable Form Component
 * Form for adding new variables
 */

import React, { useState, useCallback } from 'react';
import { IEC_DATA_TYPES, VALIDATION } from '../../config/constants';

const INITIAL_FORM_STATE = {
  deviceName: '',
  dataType: 'BOOL',
  range: '',
  MetaData: '',
};

export function VariableForm({ onAdd, onError }) {
  const [formData, setFormData] = useState(INITIAL_FORM_STATE);

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }, []);

  const handleBlur = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value.trim() }));
  }, []);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    
    const trimmedName = formData.deviceName.trim();

    if (!trimmedName) {
      onError?.('Device Name cannot be empty.');
      return;
    }

    if (!VALIDATION.DEVICE_NAME_PATTERN.test(trimmedName)) {
      onError?.('Device Name must start with a letter or underscore and contain only alphanumeric characters.');
      return;
    }

    const result = onAdd({
      ...formData,
      deviceName: trimmedName,
    });

    if (result?.success) {
      setFormData(INITIAL_FORM_STATE);
    } else if (result?.error) {
      onError?.(result.error);
    }
  }, [formData, onAdd, onError]);

  return (
    <div className="add-variable-container">
      <form className="add-variable-form" onSubmit={handleSubmit}>
        <input
          type="text"
          name="deviceName"
          placeholder="Device Name"
          value={formData.deviceName}
          onChange={handleChange}
          onBlur={handleBlur}
          className="input-base"
          aria-label="Device name"
          pattern="[A-Za-z_][A-Za-z0-9_]*"
          title="Must start with a letter or underscore"
          maxLength={VALIDATION.DEVICE_NAME_MAX_LENGTH}
        />
        <select
          name="dataType"
          value={formData.dataType}
          onChange={handleChange}
          className="input-base"
          aria-label="Data type"
        >
          {IEC_DATA_TYPES.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        <input
          type="text"
          name="range"
          placeholder="Range (e.g., 0-100)"
          value={formData.range}
          onChange={handleChange}
          onBlur={handleBlur}
          className="input-base"
          aria-label="Value range"
          title="Specify the valid range for this variable"
        />
        <input
          type="text"
          name="MetaData"
          placeholder="Description / Additional Info"
          value={formData.MetaData}
          onChange={handleChange}
          onBlur={handleBlur}
          className="input-base"
          aria-label="Additional metadata"
          title="Add any additional information"
        />
        <button type="submit" className="btn btn-primary" aria-label="Add new variable">
          Add Variable
        </button>
      </form>
    </div>
  );
}

export default VariableForm;
