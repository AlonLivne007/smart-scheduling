/**
 * Logo Component
 * 
 * A modern logo for the Smart Scheduling application.
 * Features a calendar icon with checkmark and "smart scheduling" text.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {'small'|'medium'|'large'} props.size - Logo size variant
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.showText - Whether to display the text portion
 * 
 * @example
 * // Small logo for headers
 * <Logo size="small" />
 * 
 * @example
 * // Large logo for hero sections
 * <Logo size="large" />
 * 
 * @example
 * // Icon only (no text)
 * <Logo showText={false} />
 */
import React from 'react';

const Logo = ({ size = 'medium', className = '', showText = true }) => {
  // Size classes for different logo variants
  const sizeClasses = {
    small: 'h-8',    // 32px height for headers
    medium: 'h-12',  // 48px height for navigation
    large: 'h-16'    // 64px height for hero sections
  };

  if (!showText) {
    // Icon only version
    return (
      <div className={`${sizeClasses[size]} ${className}`}>
        <svg 
          width="100%" 
          height="100%" 
          viewBox="0 0 120 120" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          className="transition-all hover:scale-105"
        >
          <g transform="translate(16,16)">
            <rect x="0" y="6" rx="14" ry="14" width="88" height="88" fill="#ffffff" stroke="#0b1220" strokeWidth="2"/>
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
    );
  }

  // Full logo with text
  return (
    <div className={`${sizeClasses[size]} ${className}`}>
      <svg 
        width="100%" 
        height="100%" 
        viewBox="0 0 420 120" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className="transition-all hover:scale-105"
      >
        <g transform="translate(16,16)">
          <rect x="0" y="6" rx="14" ry="14" width="88" height="88" fill="#ffffff" stroke="#0b1220" strokeWidth="2"/>
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
        <g transform="translate(120,58)">
          <text x="0" y="0" fontFamily="system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" fontSize="36" fontWeight="700" fill="#0f172a">
            smart <tspan fill="#2563eb">scheduling</tspan>
          </text>
        </g>
      </svg>
    </div>
  );
};

export default Logo;
