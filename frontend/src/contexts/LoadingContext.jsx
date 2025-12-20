/**
 * LoadingContext
 * 
 * React context for managing global loading state during route transitions.
 * Provides useLoading hook for easy access to loading state and controls.
 * 
 * @example
 * // In App component
 * <LoadingProvider>
 *   <App />
 * </LoadingProvider>
 * 
 * @example
 * // In any component
 * const { isLoading, setIsLoading } = useLoading();
 */

import React, { createContext, useContext, useState } from 'react';

// Create the context
const LoadingContext = createContext();

/**
 * LoadingProvider component
 * Wraps the app and provides loading state
 */
export function LoadingProvider({ children }) {
  const [isLoading, setIsLoading] = useState(false);

  const value = {
    isLoading,
    setIsLoading,
  };

  return (
    <LoadingContext.Provider value={value}>
      {children}
    </LoadingContext.Provider>
  );
}

/**
 * Hook to use loading context
 * @returns {Object} Loading state and setter
 */
export function useLoading() {
  const context = useContext(LoadingContext);
  if (!context) {
    throw new Error('useLoading must be used within LoadingProvider');
  }
  return context;
}
