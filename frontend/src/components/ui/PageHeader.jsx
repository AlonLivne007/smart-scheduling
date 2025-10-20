/**
 * PageHeader Component
 * 
 * A reusable page header component that provides consistent styling
 * for page titles, subtitles, and optional logos across the application.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {string} props.title - Main page title
 * @param {string} props.subtitle - Optional subtitle text
 * @param {boolean} props.showLogo - Whether to display the app logo
 * @param {string} props.logoSize - Logo size variant ('small'|'medium'|'large')
 * @param {string} props.className - Additional CSS classes
 * @param {React.ReactNode} props.children - Optional additional content
 * 
 * @example
 * // Basic page header
 * <PageHeader title="Dashboard" subtitle="Manage your workforce" />
 * 
 * @example
 * // With logo
 * <PageHeader title="Settings" subtitle="Configure preferences" showLogo={true} />
 */
import React from 'react';
import Logo from './Logo.jsx';

function PageHeader({ 
  title, 
  subtitle, 
  showLogo = false, 
  logoSize = 'medium',
  className = '',
  children 
}) {
  return (
    <div className={`mb-8 ${className}`}>
      {showLogo && (
        <div className="text-center mb-6">
          <Logo size={logoSize} showText={false} className="mx-auto" />
        </div>
      )}
      
      <div className="text-center">
        <h1 className="text-4xl font-bold text-blue-700 mb-2">
          {title}
        </h1>
        {subtitle && (
          <p className="text-lg text-blue-500 font-light">
            {subtitle}
          </p>
        )}
        {children}
      </div>
    </div>
  );
}

export default PageHeader;
