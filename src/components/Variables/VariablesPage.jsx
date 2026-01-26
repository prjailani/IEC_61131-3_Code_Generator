/**
 * Variables Page Component
 * Main page for managing device variables
 */

import React, { useState, useCallback } from 'react';
import { useVariables, useToast } from '../../hooks';
import { Toast, ConfirmModal, LoadingSpinner, ErrorDisplay } from '../shared';
import VariableForm from './VariableForm';
import VariableTable from './VariableTable';

export function VariablesPage({ onGoBack }) {
  const {
    variables,
    isLoading,
    isSaving,
    error,
    loadVariables,
    saveVariables,
    addVariable,
    updateVariable,
    removeVariable,
    clearError,
  } = useVariables();

  const { toast, showSuccess, showError, showInfo, hideToast } = useToast();
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Handle adding a new variable
  const handleAdd = useCallback((variableData) => {
    const result = addVariable(variableData);
    
    if (result.success) {
      showSuccess(`Variable "${variableData.deviceName}" added.`);
    }
    
    return result;
  }, [addVariable, showSuccess]);

  // Handle delete request (show confirmation)
  const handleDeleteRequest = useCallback((id, deviceName) => {
    setDeleteConfirm({ id, deviceName });
  }, []);

  // Confirm delete
  const confirmDelete = useCallback(() => {
    if (deleteConfirm) {
      removeVariable(deleteConfirm.id);
      showSuccess(`Variable "${deleteConfirm.deviceName}" removed.`);
      setDeleteConfirm(null);
    }
  }, [deleteConfirm, removeVariable, showSuccess]);

  // Cancel delete
  const cancelDelete = useCallback(() => {
    setDeleteConfirm(null);
  }, []);

  // Handle save all
  const handleSaveAll = useCallback(async () => {
    const result = await saveVariables();
    
    if (result.success) {
      showSuccess(result.message || 'Variables saved successfully!');
    } else {
      showError(result.error || 'Failed to save variables.');
    }
  }, [saveVariables, showSuccess, showError]);

  // Handle form validation errors
  const handleFormError = useCallback((message) => {
    showError(message);
  }, [showError]);

  return (
    <div className="app-container">
      {/* Toast notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}

      {/* Delete confirmation modal */}
      <ConfirmModal
        isOpen={!!deleteConfirm}
        onClose={cancelDelete}
        onConfirm={confirmDelete}
        title="Confirm Delete"
        message={`Are you sure you want to delete "${deleteConfirm?.deviceName}"?`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmVariant="danger"
      />

      <div className="card">
        <div className="switch-container">
          <button 
            onClick={onGoBack} 
            className="btn btn-secondary" 
            aria-label="Return to main page"
          >
            Go to Main Page
          </button>
        </div>

        <h1 className="title">Config Variables</h1>

        {error && (
          <ErrorDisplay
            title="Connection Error"
            message={error}
            onRetry={() => {
              clearError();
              loadVariables();
            }}
          />
        )}

        <VariableForm 
          onAdd={handleAdd} 
          onError={handleFormError} 
        />

        {isLoading ? (
          <LoadingSpinner message="Loading variables..." />
        ) : (
          <>
            <VariableTable
              variables={variables}
              onUpdate={updateVariable}
              onDelete={handleDeleteRequest}
              onSaveInfo={showInfo}
            />

            {variables.length > 0 && (
              <div className="save-all-container">
                <button
                  type="button"
                  onClick={handleSaveAll}
                  className="btn btn-primary"
                  disabled={isSaving}
                  aria-label={isSaving ? 'Saving...' : 'Save all changes'}
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

export default VariablesPage;
