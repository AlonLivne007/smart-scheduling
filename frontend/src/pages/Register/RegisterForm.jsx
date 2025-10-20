/**
 * RegisterForm Component
 * 
 * Handles the main registration form with full name, email, password, and confirm password fields.
 * Manages form state, validation, and submission logic for user registration.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Object} props.formData - Current form data state
 * @param {Object} props.errors - Current form validation errors
 * @param {Function} props.onInputChange - Handler for input field changes
 * @param {Function} props.onSubmit - Handler for form submission
 * @returns {JSX.Element} The registration form
 */
import React from 'react';
import InputField from '../../components/ui/InputField.jsx';
import Button from '../../components/ui/Button.jsx';

function RegisterForm({ formData, errors, onInputChange, onSubmit }) {
  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {/* Full Name Field */}
      <InputField
        label="Full Name"
        type="text"
        name="fullName"
        placeholder="Enter your full name"
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
        placeholder="Enter your email address"
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
        placeholder="Create a password"
        value={formData.password}
        onChange={onInputChange}
        error={errors.password}
        required
      />

      {/* Confirm Password Field */}
      <InputField
        label="Confirm Password"
        type="password"
        name="confirmPassword"
        placeholder="Confirm your password"
        value={formData.confirmPassword}
        onChange={onInputChange}
        error={errors.confirmPassword}
        required
      />

      {/* Register Button */}
      <Button type="submit" variant="primary" className="w-full">
        Create Account
      </Button>
    </form>
  );
}

export default RegisterForm;
