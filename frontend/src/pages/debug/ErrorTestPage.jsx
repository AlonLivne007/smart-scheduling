/**
 * Error Test Page - Debug/Testing Component
 * 
 * This page is used to test the ErrorBoundary component.
 * It allows testing different error scenarios.
 * 
 * Route: /debug/error
 * 
 * @component
 */

import React, { useState } from 'react';
import PageLayout from '../../layouts/PageLayout.jsx';
import PageHeader from '../../components/ui/PageHeader.jsx';

/**
 * Component that throws an error
 * Used for testing ErrorBoundary
 */
function ErrorThrower({ errorType }) {
  if (errorType === 'render') {
    throw new Error('This is a test render error!');
  }
  
  if (errorType === 'not-found') {
    throw new Error('404: Page Not Found');
  }
  
  if (errorType === 'server') {
    throw new Error('500: Server Error - Internal Server Error');
  }
  
  if (errorType === 'network') {
    throw new Error('Network Error: Failed to fetch data');
  }

  return null;
}

/**
 * Error Test Page Component
 */
export default function ErrorTestPage() {
  const [triggerError, setTriggerError] = useState(null);

  // If an error should be triggered, render the error-throwing component
  if (triggerError) {
    return <ErrorThrower errorType={triggerError} />;
  }

  return (
    <PageLayout>
      <PageHeader 
        title="Error Boundary Testing" 
        subtitle="Test different error scenarios to verify ErrorBoundary functionality"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        
        {/* Testing Instructions */}
        <div className="lg:col-span-2 bg-blue-50 border border-blue-200 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">📋 How to Test</h3>
          <p className="text-blue-800">
            Click any button below to trigger a test error. The ErrorBoundary should catch the error 
            and display a friendly error page with recovery options. You can then click "Retry" to reload 
            or "Go Home" to return to the dashboard.
          </p>
        </div>

        {/* Test Error Buttons */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Generic Render Error</h3>
          <p className="text-gray-600 mb-4">
            Tests a basic rendering error with generic error code.
          </p>
          <button
            onClick={() => setTriggerError('render')}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            Trigger Render Error
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">404 Not Found Error</h3>
          <p className="text-gray-600 mb-4">
            Tests a 404 error. ErrorBoundary should show special 404 UI.
          </p>
          <button
            onClick={() => setTriggerError('not-found')}
            className="w-full bg-amber-600 hover:bg-amber-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            Trigger 404 Error
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">500 Server Error</h3>
          <p className="text-gray-600 mb-4">
            Tests a 500 server error. ErrorBoundary should show special 500 UI.
          </p>
          <button
            onClick={() => setTriggerError('server')}
            className="w-full bg-orange-600 hover:bg-orange-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            Trigger Server Error
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Network Error</h3>
          <p className="text-gray-600 mb-4">
            Tests a network error. ErrorBoundary should show network error UI.
          </p>
          <button
            onClick={() => setTriggerError('network')}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            Trigger Network Error
          </button>
        </div>

        {/* Information Box */}
        <div className="lg:col-span-2 bg-green-50 border border-green-200 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-2">✅ What to Verify</h3>
          <ul className="text-green-800 space-y-2">
            <li>• Error page displays when button is clicked</li>
            <li>• Correct error title shows based on error type</li>
            <li>• Error code displays in the error page</li>
            <li>• Error details (message, stack trace) show in development mode</li>
            <li>• "Retry" button reloads the page</li>
            <li>• "Go Home" button navigates back to dashboard</li>
            <li>• Error UI is styled consistently with app theme</li>
          </ul>
        </div>

      </div>
    </PageLayout>
  );
}
