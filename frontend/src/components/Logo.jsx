/**
 * Logo Component
 * 
 * A modern, minimal logo for the Smart Scheduling application.
 * Features an abstract calendar with connected dots representing smart scheduling.
 * 
 * Props:
 * - variant: 'full' (with text) or 'icon' (icon only)
 * - size: 'sm', 'md', 'lg' for different sizes
 * - className: additional CSS classes
 * 
 * @component
 * @param {string} variant - Logo variant ('full' or 'icon')
 * @param {string} size - Logo size ('sm', 'md', 'lg')
 * @param {string} className - Additional CSS classes
 * @returns {JSX.Element} The logo component
 */
import React from 'react'

const Logo = ({ 
  variant = 'full', 
  size = 'sm', 
  className = '' 
}) => {
  // Shrink the logo size classes
  const sizeClasses = {
    sm: variant === 'full' ? 'w-20 h-5' : 'w-5 h-5',
    md: variant === 'full' ? 'w-28 h-7' : 'w-7 h-7',
    lg: variant === 'full' ? 'w-36 h-8' : 'w-8 h-8'
  }

  // Shrink SVG viewBox and internal coordinates for both variants
  if (variant === 'icon') {
    return (
      <div className={`${sizeClasses[size]} ${className}`}>
        <svg 
          width="100%" 
          height="100%" 
          viewBox="0 0 30 30" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          className="transition-all hover:scale-105"
        >
          {/* Calendar base */}
          <rect x="3.5" y="4.5" width="15" height="12.5" rx="2" fill="#2563eb" stroke="#1d4ed8" strokeWidth="0.6"/>
          
          {/* Calendar header */}
          <rect x="3.5" y="4.5" width="15" height="3.5" rx="2" fill="#1d4ed8"/>
          
          {/* Calendar grid dots */}
          <circle cx="6" cy="11" r="0.6" fill="white"/>
          <circle cx="8" cy="11" r="0.6" fill="white"/>
          <circle cx="10" cy="11" r="0.6" fill="white"/>
          <circle cx="12" cy="11" r="0.6" fill="white"/>
          
          <circle cx="6" cy="13" r="0.6" fill="white"/>
          <circle cx="8" cy="13" r="0.6" fill="white"/>
          <circle cx="10" cy="13" r="0.6" fill="white"/>
          <circle cx="12" cy="13" r="0.6" fill="white"/>
          
          <circle cx="6" cy="15" r="0.6" fill="white"/>
          <circle cx="8" cy="15" r="0.6" fill="white"/>
          <circle cx="10" cy="15" r="0.6" fill="white"/>
          <circle cx="12" cy="15" r="0.6" fill="white"/>
          
          {/* Connected dots representing smart connections */}
          <circle cx="19.5" cy="8" r="0.9" fill="#3b82f6"/>
          <circle cx="23.5" cy="11" r="0.9" fill="#3b82f6"/>
          <circle cx="21" cy="16" r="0.9" fill="#3b82f6"/>
          
          {/* Connection lines */}
          <path d="M20.3 8 L22.1 11" stroke="#3b82f6" strokeWidth="0.6" strokeLinecap="round"/>
          <path d="M23.5 11 L21.9 16" stroke="#3b82f6" strokeWidth="0.6" strokeLinecap="round"/>
          <path d="M20.3 8 L21.9 16" stroke="#3b82f6" strokeWidth="0.6" strokeLinecap="round" opacity="0.6"/>
        </svg>
      </div>
    )
  }

  return (
    <div className={`${sizeClasses[size]} ${className}`}>
      <svg 
        width="100%" 
        height="100%" 
        viewBox="0 0 120 32" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className="transition-all hover:scale-105"
      >
        {/* Icon: Abstract calendar with connected dots */}
        <g id="icon">
          {/* Calendar base */}
          <rect x="4" y="5" width="18" height="14" rx="2" fill="#2563eb" stroke="#1d4ed8" strokeWidth="0.7"/>
          
          {/* Calendar header */}
          <rect x="4" y="5" width="18" height="4" rx="2" fill="#1d4ed8"/>
          
          {/* Calendar grid dots */}
          <circle cx="7" cy="11" r="0.8" fill="white"/>
          <circle cx="10" cy="11" r="0.8" fill="white"/>
          <circle cx="13" cy="11" r="0.8" fill="white"/>
          <circle cx="16" cy="11" r="0.8" fill="white"/>
          
          <circle cx="7" cy="15" r="0.8" fill="white"/>
          <circle cx="10" cy="15" r="0.8" fill="white"/>
          <circle cx="13" cy="15" r="0.8" fill="white"/>
          <circle cx="16" cy="15" r="0.8" fill="white"/>
          
          <circle cx="7" cy="19" r="0.8" fill="white"/>
          <circle cx="10" cy="19" r="0.8" fill="white"/>
          <circle cx="13" cy="19" r="0.8" fill="white"/>
          <circle cx="16" cy="19" r="0.8" fill="white"/>
          
          {/* Connected dots representing smart connections */}
          <circle cx="23" cy="9" r="1.2" fill="#3b82f6"/>
          <circle cx="29" cy="12.5" r="1.2" fill="#3b82f6"/>
          <circle cx="25.5" cy="18.5" r="1.2" fill="#3b82f6"/>
          
          {/* Connection lines */}
          <path d="M24.4 9 L27.3 12.5" stroke="#3b82f6" strokeWidth="0.7" strokeLinecap="round"/>
          <path d="M29 12.5 L26.7 18.5" stroke="#3b82f6" strokeWidth="0.7" strokeLinecap="round"/>
          <path d="M24.4 9 L26.7 18.5" stroke="#3b82f6" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>
        </g>
        
        {/* Text: Smart Scheduling */}
        <g id="text">
          <text x="36" y="15" fontFamily="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" fontSize="9" fontWeight="600" fill="#1e293b">Smart</text>
          <text x="36" y="25" fontFamily="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" fontSize="9" fontWeight="600" fill="#2563eb">Scheduling</text>
        </g>
      </svg>
    </div>
  )
}

export default Logo
