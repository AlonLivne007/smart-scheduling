/**
 * AddUserHeader Component
 * 
 * Displays the page header for the Add User admin page.
 * Shows the page title, subtitle, and optional admin branding.
 * 
 * @component
 * @returns {JSX.Element} The add user page header
 */
import React from 'react';
import Logo from '../../../components/ui/Logo.jsx';

function AddUserHeader() {
  return (
    <div className="text-center mb-8">
      {/* Admin Logo/Icon */}
      <div className="mb-6 flex justify-center">
        <Logo size="large" showText={false} className="w-20 h-20" />
      </div>
      
      {/* Page Title */}
      <h1 className="text-4xl font-bold text-blue-700 mb-2">
        Add New User
      </h1>
      
      {/* Subtitle */}
      <p className="text-lg text-blue-500 font-light">
        Create a new user account for the Smart Scheduling system
      </p>
    </div>
  );
}

export default AddUserHeader;
