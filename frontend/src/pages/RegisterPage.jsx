/**
 * Register Page Component
 * 
 * A modern, clean registration page for the Smart Scheduling application.
 * Features a centered registration form with gradient background and professional styling.
 * 
 * Features:
 * - Soft blue-to-white gradient background
 * - Centered registration card with shadow
 * - App logo and branding
 * - Full name, email, password, and confirm password fields
 * - Full-width register button
 * - Login link for existing users
 * 
 * @component
 * @returns {JSX.Element} The registration page
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import InputField from '../components/ui/InputField.jsx';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [errors, setErrors] = useState({});

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
        <div className="text-center mb-8">
          {/* App Logo/Icon */}
          <div className="mb-6">
            <svg 
              width="80" 
              height="80" 
              viewBox="0 0 120 120" 
              fill="none" 
              xmlns="http://www.w3.org/2000/svg"
              className="mx-auto"
            >
              <g transform="translate(16,16)">
                <rect x="0" y="6" rx="14" ry="14" width="88" height="88" fill="#ffffff" stroke="#2563eb" strokeWidth="2"/>
                <rect x="0" y="6" rx="14" ry="14" width="88" height="24" fill="#2563eb"/>
                <g fill="#ffffff">
                  <rect x="18" y="0" width="10" height="16" rx="3" ry="3"/>
                  <rect x="60" y="0" width="10" height="16" rx="3" ry="3"/>
                </g>
                <g stroke="#e2e8f0" strokeWidth="1">
                  <line x1="12" y1="40" x2="76" y2="40"/>
                  <line x1="12" y1="56" x2="76" y2="56"/>
                  <line x1="12" y1="72" x2="76" y2="72"/>
                  <line x1="28" y1="24" x2="28" y2="88"/>
                  <line x1="48" y1="24" x2="48" y2="88"/>
                  <line x1="68" y1="24" x2="68" y2="88"/>
                </g>
                <circle cx="58" cy="68" r="12" fill="none" stroke="#1d4ed8" strokeWidth="3"/>
                <path d="M51 68 l4 4 l10 -10" fill="none" stroke="#1d4ed8" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
              </g>
            </svg>
          </div>
          
          {/* App Name */}
          <h1 className="text-4xl font-bold text-blue-700 mb-2">
            Smart Scheduling
          </h1>
          
          {/* Subtitle */}
          <p className="text-lg text-blue-500 font-light">
            Create Your Account
          </p>
        </div>

        {/* Registration Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Full Name Field */}
            <InputField
              label="Full Name"
              type="text"
              name="fullName"
              placeholder="Enter your full name"
              value={formData.fullName}
              onChange={handleInputChange}
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
              onChange={handleInputChange}
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
              onChange={handleInputChange}
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
              onChange={handleInputChange}
              error={errors.confirmPassword}
              required
            />

            {/* Register Button */}
            <button
              type="submit"
              className="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
            >
              Create Account
            </button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
            </div>

            {/* Login Link */}
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link 
                  to="/login" 
                  className="text-blue-500 hover:text-blue-600 font-medium transition-colors duration-200"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
