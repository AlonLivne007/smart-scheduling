/**
 * Logo Component
 * 
 * A branded logo component featuring a calendar icon and "Smart Scheduling" text.
 * The logo uses a custom SVG calendar icon with the app's blue color scheme.
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
  // Icon size classes - controls the calendar icon dimensions
  const sizeClasses = {
    small: 'h-8 w-8',    // 32x32px - for headers and small spaces
    medium: 'h-10 w-10', // 40x40px - for navigation and standard use
    large: 'h-12 w-12'   // 48x48px - for hero sections and large displays
  };

  // Text size classes - matches the icon size for visual harmony
  const textSizeClasses = {
    small: 'text-sm',    // Small text for compact spaces
    medium: 'text-lg',   // Medium text for standard use
    large: 'text-xl'     // Large text for prominent displays
  };

  return (
    <div className={`d-flex align-items-center ${className}`}>
      {/* Calendar Icon Container */}
      <div className={`${sizeClasses[size]} bg-primary rounded-3 d-flex align-items-center justify-content-center me-3 shadow-sm`}>
        <svg 
          width="60%" 
          height="60%" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          className="text-white"
        >
          {/* Calendar base rectangle */}
          <rect 
            x="3" 
            y="4" 
            width="18" 
            height="18" 
            rx="2" 
            ry="2" 
            stroke="currentColor" 
            strokeWidth="1.5" 
            fill="white"
          />
          {/* Calendar binding loops at the top */}
          <rect x="7" y="2" width="3" height="2" rx="1" fill="currentColor" />
          <rect x="14" y="2" width="3" height="2" rx="1" fill="currentColor" />
          {/* Calendar grid lines for date representation */}
          <line x1="8" y1="10" x2="8" y2="16" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
          <line x1="12" y1="10" x2="12" y2="16" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
          <line x1="16" y1="10" x2="16" y2="16" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
          <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
          <line x1="8" y1="14" x2="16" y2="14" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
        </svg>
      </div>
      
      {/* Text portion - conditionally rendered */}
      {showText && (
        <div className="d-flex flex-column">
          <span className={`fw-bold text-primary mb-0 ${textSizeClasses[size]}`}>
            Smart
          </span>
          <span className={`fw-bold text-primary ${textSizeClasses[size]}`}>
            Scheduling
          </span>
        </div>
      )}
    </div>
  );
};

export default Logo;
