/**
 * RegisterLinks Component
 * 
 * Displays navigation links for the registration page including:
 * - Login link for existing users
 * 
 * @component
 * @returns {JSX.Element} The registration navigation links
 */
import React from 'react';
import { Link } from 'react-router-dom';

function RegisterLinks() {
  return (
    <>
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
    </>
  );
}

export default RegisterLinks;
