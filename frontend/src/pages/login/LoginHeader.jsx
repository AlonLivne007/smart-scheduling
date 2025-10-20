/**
 * LoginHeader Component
 * 
 * Displays the application logo, name, and subtitle for the login page.
 * This component handles the branding section at the top of the login form.
 * 
 * @component
 * @returns {JSX.Element} The login header with logo and branding
 */
import React from 'react';

function LoginHeader() {
  return (
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
  );
}

export default LoginHeader;