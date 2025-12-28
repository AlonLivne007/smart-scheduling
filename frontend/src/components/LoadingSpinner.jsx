/**
 * LoadingSpinner Component
 * 
 * A full-page loading spinner that displays while content is loading or routes are transitioning.
 * Features smooth fade in/out animations and matches the app theme with blue gradient styling.
 * 
 * Features:
 * - Animated rotating spinner icon
 * - Centered on page or header
 * - Smooth fade in/out transitions
 * - Blue gradient theme consistent with app
 * - Optional loading text
 * - Configurable backdrop opacity
 * 
 * @component
 * @param {Object} props - Component props
 * @param {string} props.text - Optional loading text to display below spinner
 * @param {boolean} props.fullPage - Whether to cover full page (true) or show inline (false, default)
 * @param {string} props.className - Additional CSS classes
 * @param {number} props.size - Icon size in pixels (default: 48)
 * 
 * @example
 * // Full page spinner with text
 * <LoadingSpinner fullPage text="Loading dashboard..." />
 * 
 * @example
 * // Inline spinner (e.g., in component)
 * <LoadingSpinner text="Fetching data..." />
 * 
 * @example
 * // Custom size
 * <LoadingSpinner fullPage size={64} />
 */

import React from 'react';
import { Loader2 } from 'lucide-react';

function LoadingSpinner({ 
  text = 'Loading...', 
  fullPage = false,
  className = '',
  size = 48,
}) {
  if (fullPage) {
    // Full page overlay spinner
    return (
      <div className="fixed inset-0 bg-white bg-opacity-90 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              {/* Animated gradient spinner */}
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full blur opacity-75 animate-pulse"></div>
              <div className="relative bg-white rounded-full p-3">
                <Loader2 
                  size={size} 
                  className="text-blue-600 animate-spin"
                  strokeWidth={2.5}
                />
              </div>
            </div>
          </div>
          {text && (
            <p className="text-gray-700 font-medium text-lg">{text}</p>
          )}
        </div>
      </div>
    );
  }

  // Inline spinner (e.g., in component)
  return (
    <div className={`flex flex-col items-center justify-center py-8 ${className}`}>
      <div className="relative mb-3">
        {/* Animated gradient spinner */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full blur opacity-75 animate-pulse"></div>
        <div className="relative bg-white rounded-full p-2">
          <Loader2 
            size={size} 
            className="text-blue-600 animate-spin"
            strokeWidth={2.5}
          />
        </div>
      </div>
      {text && (
        <p className="text-gray-600 font-medium">{text}</p>
      )}
    </div>
  );
}

export default LoadingSpinner;
