/**
 * LoginLinks Component
 * 
 * Displays navigation links for the login page including:
 * - Forgot password link
 * - Sign up link for new users
 * 
 * @component
 * @returns {JSX.Element} The login navigation links
 */
import React from 'react';
import { Link } from 'react-router-dom';

function LoginLinks() {
  return (
    <>
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
        <p className="text-sm text-gray-600">
          Don't have an account?{' '}
          <Link 
            to="/register" 
            className="text-blue-500 hover:text-blue-600 font-medium transition-colors duration-200"
          >
            Sign up
          </Link>
        </p>
      </div>
    </>
  );
}

export default LoginLinks;