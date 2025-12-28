/**
 * RouteSuspense Component
 * 
 * Wraps routes to show a loading spinner during async component loading.
 * Uses React Suspense with a fallback LoadingSpinner component.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Route component to load
 * @param {string} props.text - Optional loading text
 * 
 * @example
 * <RouteSuspense>
 *   <HomePage />
 * </RouteSuspense>
 */

import React, { Suspense } from 'react';
import LoadingSpinner from './LoadingSpinner.jsx';

function RouteSuspense({ children, text = 'Loading page...' }) {
  return (
    <Suspense fallback={<LoadingSpinner fullPage text={text} />}>
      {children}
    </Suspense>
  );
}

export default RouteSuspense;
