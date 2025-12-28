/**
 * Skeleton Component
 * 
 * A reusable skeleton loader component that displays animated placeholders
 * while data is loading. Used to improve perceived performance by showing
 * the layout structure before content arrives.
 * 
 * Features:
 * - Multiple size variants (small, medium, large)
 * - Smooth pulse animation effect
 * - Light gray color matching card backgrounds
 * - Can be rounded or full width
 * - Customizable dimensions
 * 
 * @component
 * @example
 * // Small skeleton (e.g., for text)
 * <Skeleton size="small" />
 * 
 * @example
 * // Medium skeleton (e.g., for metric cards)
 * <Skeleton size="medium" className="mb-4" />
 * 
 * @example
 * // Large skeleton (e.g., for full-width content)
 * <Skeleton size="large" />
 * 
 * @example
 * // Custom dimensions
 * <Skeleton width="100%" height="24px" className="rounded-lg" />
 */

import React from 'react';

function Skeleton({ 
  size = 'medium',
  width = undefined,
  height = undefined,
  className = '',
  rounded = true,
  count = 1,
}) {
  // Predefined size dimensions
  const sizes = {
    small: { width: '60px', height: '16px' },
    medium: { width: '100%', height: '24px' },
    large: { width: '100%', height: '40px' },
  };

  // Get dimensions from size or custom props
  const dimensions = {
    width: width || sizes[size]?.width,
    height: height || sizes[size]?.height,
  };

  // Build className for single skeleton
  const skeletonClasses = [
    'bg-gradient-to-r',
    'from-gray-200',
    'via-gray-100',
    'to-gray-200',
    'animate-pulse',
    rounded ? 'rounded' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  // For multiple skeletons, render a group
  if (count > 1) {
    return (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, idx) => (
          <div
            key={idx}
            className={skeletonClasses}
            style={{
              width: dimensions.width,
              height: dimensions.height,
            }}
          />
        ))}
      </div>
    );
  }

  // Single skeleton
  return (
    <div
      className={skeletonClasses}
      style={{
        width: dimensions.width,
        height: dimensions.height,
      }}
    />
  );
}

export default Skeleton;
