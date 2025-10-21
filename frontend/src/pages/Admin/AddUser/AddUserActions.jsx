/**
 * AddUserActions Component
 * 
 * Displays action buttons for the add user form including:
 * - Create User button (primary action)
 * - Cancel/Reset button (secondary action)
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Function} props.onCreateUser - Handler for create user action
 * @param {Function} props.onCancel - Handler for cancel action
 * @param {boolean} props.isLoading - Whether form is in loading state
 * @returns {JSX.Element} The add user action buttons
 */
import React from 'react';
import Button from '../../../components/ui/Button.jsx';

function AddUserActions({ onCreateUser, onCancel, isLoading = false }) {
  return (
    <div className="flex gap-4 justify-end">
      {/* Cancel Button */}
      <Button 
        variant="secondarySolid" 
        onClick={onCancel}
        disabled={isLoading}
      >
        Cancel
      </Button>
      
      {/* Create User Button */}
      <Button 
        variant="primary" 
        onClick={onCreateUser}
        disabled={isLoading}
        className="min-w-[120px]"
      >
        {isLoading ? 'Creating...' : 'Create User'}
      </Button>
    </div>
  );
}

export default AddUserActions;
