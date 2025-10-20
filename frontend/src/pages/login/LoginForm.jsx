/**
 * LoginForm Component
 * 
 * Handles the main login form with email and password fields.
 * Manages form state and submission logic for user authentication.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Object} props.formData - Current form data state
 * @param {Function} props.onInputChange - Handler for input field changes
 * @param {Function} props.onSubmit - Handler for form submission
 * @returns {JSX.Element} The login form
 */
import React from 'react';
import InputField from '../../components/ui/InputField.jsx';

function LoginForm({ formData, onInputChange, onSubmit }) {
  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {/* Email Field */}
      <InputField
        label="Email Address"
        type="email"
        name="email"
        placeholder="Email Address"
        value={formData.email}
        onChange={onInputChange}
        required
      />

      {/* Password Field */}
      <InputField
        label="Password"
        type="password"
        name="password"
        placeholder="Password"
        value={formData.password}
        onChange={onInputChange}
        required
      />

      {/* Login Button */}
      <button
        type="submit"
        className="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
      >
        Login
      </button>
    </form>
  );
}

export default LoginForm;
