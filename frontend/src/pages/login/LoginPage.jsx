/**
 * LoginPage Component
 * 
 * Main container component for the login page that orchestrates all sub-components.
 * Manages the overall layout, form state, and coordinates between child components.
 * 
 * Features:
 * - Soft blue-to-white gradient background
 * - Centered login card with shadow
 * - Modular component structure for maintainability
 * 
 * @component
 * @returns {JSX.Element} The complete login page
 */
import React, { useState } from 'react';
import LoginHeader from './LoginHeader.jsx';
import LoginForm from './LoginForm.jsx';
import LoginLinks from './LoginLinks.jsx';
import api from '../../lib/axios.js';

export default function LoginPage() {
  // Form state management
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  /**
   * Handles input field changes and updates form state
   * @param {Event} e - Input change event
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * Handles form submission for login
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.post('/users/login', {
        user_email: formData.email,
        user_password: formData.password,
      });

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('current_user', JSON.stringify(data.user));
      // Optionally navigate to a protected page here
      console.log('Logged in successfully');
    } catch (err) {
      const message = err?.response?.data?.detail || err.message || 'Login failed';
      console.error(message);
      alert(message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header Section - Logo and App Name */}
        <LoginHeader />

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Login Form */}
          <LoginForm 
            formData={formData}
            onInputChange={handleInputChange}
            onSubmit={handleSubmit}
          />

          {/* Navigation Links */}
          <LoginLinks />
        </div>
      </div>
    </div>
  );
}
