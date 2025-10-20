/**
 * RegisterPage Component
 * 
 * Main container component for the registration page that orchestrates all sub-components.
 * Manages the overall layout, form state, validation, and coordinates between child components.
 * 
 * Features:
 * - Soft blue-to-white gradient background
 * - Centered registration card with shadow
 * - Modular component structure for maintainability
 * - Form validation with error handling
 * 
 * @component
 * @returns {JSX.Element} The complete registration page
 */
import React, { useState } from 'react';
import RegisterHeader from './RegisterHeader.jsx';
import RegisterForm from './RegisterForm.jsx';
import RegisterLinks from './RegisterLinks.jsx';

export default function RegisterPage() {
  // Form state management
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  // Error state management
  const [errors, setErrors] = useState({});

  /**
   * Handles input field changes and updates form state
   * Clears validation errors when user starts typing
   * @param {Event} e - Input change event
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  /**
   * Validates the registration form and sets error messages
   * @returns {boolean} True if form is valid, false otherwise
   */
  const validateForm = () => {
    const newErrors = {};

    // Full name validation
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = 'Full name must be at least 2 characters';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handles form submission for registration
   * Validates form before processing
   * @param {Event} e - Form submit event
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      // Handle registration logic here
      console.log('Registration attempt:', formData);
      // You would typically send this data to your backend API
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header Section - Logo and App Name */}
        <RegisterHeader />

        {/* Registration Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Registration Form */}
          <RegisterForm 
            formData={formData}
            errors={errors}
            onInputChange={handleInputChange}
            onSubmit={handleSubmit}
          />

          {/* Navigation Links */}
          <RegisterLinks />
        </div>
      </div>
    </div>
  );
}
