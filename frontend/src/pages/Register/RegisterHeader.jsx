/**
 * RegisterHeader Component
 * 
 * Displays the application logo, name, and subtitle for the registration page.
 * This component handles the branding section at the top of the registration form.
 * 
 * @component
 * @returns {JSX.Element} The registration header with logo and branding
 */
import React from 'react';
import Logo from '../../components/ui/Logo.jsx';

function RegisterHeader() {
  return (
    <div className="text-center mb-8">
      {/* App Logo/Icon */}
      <div className="mb-6 flex justify-center">
        <Logo size="large" showText={false} className="w-20 h-20" />
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
  );
}

export default RegisterHeader;
