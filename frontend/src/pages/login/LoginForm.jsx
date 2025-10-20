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
import Button from '../../components/ui/Button.jsx';

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
      <Button type="submit" variant="primary" className="w-full">
        Login
      </Button>
    </form>
  );
}

export default LoginForm;
