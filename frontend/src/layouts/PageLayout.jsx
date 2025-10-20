/**
 * PageLayout Component
 * 
 * A reusable page layout component that provides consistent structure
 * and styling for all application pages.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Page content
 * @param {string} props.className - Additional CSS classes for content area
 * @param {boolean} props.centered - Whether to center content vertically
 * @param {string} props.maxWidth - Maximum width of the content container
 * 
 * @example
 * // Basic page layout
 * <PageLayout>
 *   <PageHeader title="Dashboard" />
 *   <div>Page content here</div>
 * </PageLayout>
 * 
 * @example
 * // Centered layout for forms
 * <PageLayout centered maxWidth="max-w-md">
 *   <LoginForm />
 * </PageLayout>
 */
import React from 'react';

function PageLayout({ 
  children, 
  className = '', 
  centered = false,
  maxWidth = 'max-w-7xl'
}) {
  const containerClasses = centered 
    ? 'min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4'
    : 'min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 p-6';

  return (
    <div className={containerClasses}>
      <div className={`${maxWidth} mx-auto ${className}`}>
        {children}
      </div>
    </div>
  );
}

export default PageLayout;
