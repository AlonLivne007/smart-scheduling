/**
 * AddUserForm Component
 * 
 * Handles the main user creation form with all required fields.
 * Manages form state, validation, and submission logic for admin user creation.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Object} props.formData - Current form data state
 * @param {Object} props.errors - Current form validation errors
 * @param {Function} props.onInputChange - Handler for input field changes
 * @param {Function} props.onSubmit - Handler for form submission
 * @returns {JSX.Element} The add user form
 */
import React from 'react';
import InputField from '../../../components/ui/InputField.jsx';

function AddUserForm({ formData, errors, onInputChange, onSubmit }) {

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {/* Full Name Field */}
      <InputField
        label="Full Name"
        type="text"
        name="fullName"
        placeholder="Enter user's full name"
        value={formData.fullName}
        onChange={onInputChange}
        error={errors.fullName}
        required
      />

      {/* Email Field */}
      <InputField
        label="Email Address"
        type="email"
        name="email"
        placeholder="Enter user's email address"
        value={formData.email}
        onChange={onInputChange}
        error={errors.email}
        required
      />

      {/* Password Field */}
      <InputField
        label="Password"
        type="password"
        name="password"
        placeholder="Create a secure password"
        value={formData.password}
        onChange={onInputChange}
        error={errors.password}
        required
      />

      {/* Role Field */}
      <InputField
        label="Role"
        type="text"
        name="role"
        placeholder="Enter user's role (e.g., Developer, Manager, Analyst)"
        value={formData.role}
        onChange={onInputChange}
        error={errors.role}
        required
      />

      {/* Manager Checkbox */}
      <div className="space-y-2">
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            name="is_manager"
            checked={formData.is_manager}
            onChange={onInputChange}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
          />
          <span className="text-sm font-medium text-gray-700">
            Manager privileges
          </span>
        </label>
        {errors.is_manager && (
          <p className="text-sm text-red-600">{errors.is_manager}</p>
        )}
        <p className="text-xs text-gray-500">
          Check this box if the user should have administrative privileges
        </p>
      </div>

    </form>
  );
}

export default AddUserForm;
