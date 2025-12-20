/**
 * MetricCard Component
 * 
 * A reusable metric card component for displaying key performance indicators
 * and statistics in dashboard layouts.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.icon - Icon component or element
 * @param {string} props.title - Metric title
 * @param {string|number} props.value - Metric value
 * @param {string} props.description - Optional description text
 * @param {string} props.iconColor - Icon background color class
 * @param {string} props.valueColor - Value text color class
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.hover - Whether to show hover effects
 * @param {boolean} props.isLoading - If true, shows skeleton loader instead of content
 * 
 * @example
 * // Basic metric card
 * <MetricCard 
 *   icon={<Users className="w-6 h-6" />}
 *   title="Total Employees"
 *   value="120"
 *   description="Active team members"
 * />
 * 
 * @example
 * // Loading state
 * <MetricCard 
 *   title="Total Employees"
 *   isLoading={true}
 * />
 * 
 * @example
 * // With custom colors
 * <MetricCard 
 *   icon={<Clock className="w-6 h-6" />}
 *   title="Upcoming Shifts"
 *   value="24"
 *   description="Next 7 days"
 *   iconColor="bg-green-50"
 *   valueColor="text-green-600"
 * />
 */
import React from 'react';
import Skeleton from './Skeleton.jsx';

function MetricCard({ 
  icon, 
  title, 
  value, 
  description, 
  iconColor = 'bg-blue-50',
  valueColor = 'text-blue-600',
  className = '',
  hover = true,
  isLoading = false,
}) {
  const hoverClasses = hover 
    ? 'hover:shadow-xl hover:-translate-y-1 transition-all duration-300' 
    : '';

  // Loading state - show skeletons
  if (isLoading) {
    return (
      <div className={`bg-white rounded-2xl shadow-lg p-6 h-full ${className}`}>
        <div className="text-center">
          {/* Icon skeleton */}
          <div className="mb-3 flex justify-center">
            <Skeleton width="48px" height="48px" rounded={true} />
          </div>
          
          {/* Title skeleton */}
          <Skeleton size="small" width="60%" className="mx-auto mb-2" />
          
          {/* Value skeleton */}
          <Skeleton size="large" width="70%" className="mx-auto mb-2" />
          
          {/* Description skeleton */}
          {description && (
            <Skeleton size="small" width="50%" className="mx-auto" />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-2xl shadow-lg p-6 h-full ${hoverClasses} ${className}`}>
      <div className="text-center">
        <div className={`${iconColor} rounded-full p-3 inline-block mb-3`}>
          {icon}
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <h2 className={`text-4xl font-bold ${valueColor} mb-2`}>{value}</h2>
        {description && (
          <p className="text-gray-600">{description}</p>
        )}
      </div>
    </div>
  );
}

export default MetricCard;
