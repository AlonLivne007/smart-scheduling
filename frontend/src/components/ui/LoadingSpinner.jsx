/**
 * LoadingSpinner Component
 * 
 * A full-screen or inline loading spinner that displays while content is loading.
 * Features smooth fade in/out animations and matches the app's blue theme.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {boolean} props.fullScreen - If true, renders full-screen overlay; otherwise inline
 * @param {string} props.message - Optional loading message to display below spinner
 * @param {boolean} props.show - If false, spinner is hidden
 * 
 * @example
 * // Full-screen spinner for page transitions
 * <LoadingSpinner fullScreen={true} show={isLoading} />
 * 
 * @example
 * // Inline spinner with message
 * <LoadingSpinner fullScreen={false} message="Loading dashboard..." show={true} />
 */

import React from 'react';
import { Loader } from 'lucide-react';

function LoadingSpinner({ 
  fullScreen = true, 
  message = 'Loading...',
  show = true 
}) {
  // Don't render if not showing
  if (!show) return null;

  // Full-screen overlay
  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-95 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
        <div className="text-center">
          {/* Animated Spinner Icon */}
          <div className="mb-4 flex justify-center">
            <Loader className="w-12 h-12 text-blue-600 animate-spin" />
          </div>
          
          {/* Loading Message */}
          {message && (
            <p className="text-gray-700 font-medium">{message}</p>
          )}
          
          {/* Optional: Loading dots */}
          <div className="mt-4 flex justify-center gap-1">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    );
  }

  // Inline spinner
  return (
    <div className="flex items-center justify-center py-8">
      <Loader className="w-8 h-8 text-blue-600 animate-spin mr-3" />
      {message && (
        <p className="text-gray-700 font-medium">{message}</p>
      )}
    </div>
  );
}

export default LoadingSpinner;
