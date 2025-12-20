/**
 * ErrorBoundary Component
 * 
 * A React component that catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of crashing the entire app.
 * 
 * Features:
 * - Catches render errors in child components
 * - Displays error message and stack trace (dev only)
 * - Shows error code for debugging
 * - Provides "Retry" and "Go Home" recovery actions
 * - Different UI for 404 vs 500 errors
 * - Styled consistently with app theme
 * 
 * @component
 * @example
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 */

import React from 'react';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';
import Button from './ui/Button';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCode: 'UNKNOWN_ERROR',
    };
  }

  /**
   * Update state so the next render will show the fallback UI
   * @param {Error} error - The error that was thrown
   * @returns {Object} New state object
   */
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  /**
   * Log error details for debugging
   * @param {Error} error - The error that was thrown
   * @param {Object} errorInfo - Object with componentStack key
   */
  componentDidCatch(error, errorInfo) {
    // Log to console in development
    console.error('🔴 Error caught by ErrorBoundary:');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);

    // Determine error code based on error type or message
    let errorCode = 'RENDER_ERROR';
    if (error.message.includes('404') || error.message.includes('Not Found')) {
      errorCode = '404_NOT_FOUND';
    } else if (error.message.includes('500') || error.message.includes('Server Error')) {
      errorCode = '500_SERVER_ERROR';
    } else if (error.message.includes('Network')) {
      errorCode = 'NETWORK_ERROR';
    }

    this.setState({
      error,
      errorInfo,
      errorCode,
    });

    // Optional: Send error to external logging service
    // logErrorToService(error, errorInfo);
  }

  /**
   * Handle retry - reload the page
   */
  handleRetry = () => {
    // Reset error boundary state
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCode: 'UNKNOWN_ERROR',
    });
    
    // Optionally reload the page
    window.location.reload();
  };

  /**
   * Handle go home - navigate to dashboard
   */
  handleGoHome = () => {
    // Reset error boundary state
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCode: 'UNKNOWN_ERROR',
    });
    
    // Navigate to home
    window.location.href = '/';
  };

  /**
   * Determine error severity and styling based on error code
   */
  getErrorUI() {
    const { error, errorInfo, errorCode } = this.state;
    const isDevelopment = process.env.NODE_ENV === 'development';

    // Different UI for different error types
    const is404 = errorCode === '404_NOT_FOUND';
    const is500 = errorCode === '500_SERVER_ERROR';

    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          {/* Error Container */}
          <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 border-t-4 border-red-500">
            
            {/* Error Icon and Title */}
            <div className="flex items-center justify-center mb-6">
              <div className="bg-red-100 rounded-full p-4">
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
            </div>

            {/* Error Title */}
            <h1 className="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-2">
              {is404 ? 'Page Not Found' : is500 ? 'Server Error' : 'Something Went Wrong'}
            </h1>

            {/* Error Code */}
            <div className="text-center mb-6">
              <p className="text-lg font-mono text-red-600 bg-red-50 rounded-lg py-2 px-4 inline-block">
                Error Code: {errorCode}
              </p>
            </div>

            {/* Error Message */}
            <div className="mb-8">
              <p className="text-center text-gray-700 mb-4 text-lg leading-relaxed">
                {is404
                  ? 'The page you are looking for does not exist. Please check the URL and try again.'
                  : is500
                  ? 'The server encountered an unexpected error. Please try again later.'
                  : 'An unexpected error occurred in the application. We apologize for the inconvenience.'}
              </p>

              {/* Error Details Box (Development Only) */}
              {isDevelopment && error && (
                <div className="bg-gray-100 rounded-lg p-4 mt-6 border border-gray-300">
                  <h3 className="font-semibold text-gray-900 mb-2">📋 Error Details (Development Only):</h3>
                  
                  {/* Error Message */}
                  <div className="mb-3">
                    <p className="font-mono text-sm text-red-600 break-all">
                      <span className="font-bold">Message:</span> {error.toString()}
                    </p>
                  </div>

                  {/* Stack Trace */}
                  {errorInfo && (
                    <div className="mb-3">
                      <p className="font-mono text-xs text-gray-700 bg-white p-3 rounded max-h-48 overflow-y-auto whitespace-pre-wrap">
                        <span className="font-bold">Stack:</span>
                        {'\n'}
                        {errorInfo.componentStack}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={this.handleRetry}
                className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                <RefreshCw className="w-5 h-5" />
                Retry
              </button>
              
              <button
                onClick={this.handleGoHome}
                className="flex items-center justify-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                <Home className="w-5 h-5" />
                Go Home
              </button>
            </div>

            {/* Support Message */}
            <div className="mt-8 pt-6 border-t border-gray-200 text-center">
              <p className="text-gray-600 text-sm">
                If this problem persists, please contact support at{' '}
                <a href="mailto:support@example.com" className="text-blue-600 hover:underline">
                  support@example.com
                </a>
              </p>
            </div>
          </div>

          {/* Footer Message */}
          <div className="text-center mt-8 text-gray-600">
            <p className="text-sm">
              Error ID: <span className="font-mono">{Date.now()}</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  render() {
    if (this.state.hasError) {
      return this.getErrorUI();
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
