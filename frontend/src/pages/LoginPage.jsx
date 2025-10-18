/**
 * Login Page Component
 * 
 * A modern, clean login page for the Smart Scheduling application.
 * Features a centered login form with gradient background and professional styling.
 * 
 * Features:
 * - Soft blue-to-white gradient background
 * - Centered login card with shadow
 * - App logo and branding
 * - Email and password input fields
 * - Full-width login button
 * - Forgot password and sign up links
 * 
 * @component
 * @returns {JSX.Element} The login page
 */
import React, { useState } from 'react';
import Button from '../components/ui/Button.jsx';
import InputField from '../components/ui/InputField.jsx';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Handle login logic here
    console.log('Login attempt:', formData);
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
            Effortless Workforce Planning
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Field */}
            <InputField
              label="Email Address"
              type="email"
              name="email"
              placeholder="Email Address"
              value={formData.email}
              onChange={handleInputChange}
              required
            />

            {/* Password Field */}
            <InputField
              label="Password"
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleInputChange}
              required
            />

            {/* Login Button */}
            <button
              type="submit"
              className="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
            >
              Login
            </button>

            {/* Forgot Password Link */}
            <div className="text-center">
              <a 
                href="#" 
                className="text-blue-500 hover:text-blue-600 text-sm transition-colors duration-200"
              >
                Forgot password?
              </a>
            </div>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
            </div>

            {/* Sign Up Link */}
            <div className="text-center">
              <a 
                href="#" 
                className="text-blue-500 hover:text-blue-600 text-sm transition-colors duration-200"
              >
                Sign up
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
