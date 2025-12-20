/**
 * Button Component
 * 
 * A reusable button component with consistent styling and multiple variants.
 * Uses Tailwind CSS for modern, utility-first styling with a blue theme.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Button content (text, icons, etc.)
 * @param {'primary'|'success'|'danger'|'primarySolid'|'successSolid'|'secondarySolid'|'primarySubtle'} props.variant - Button style variant
 * @param {'small'|'medium'|'large'} props.size - Button size
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.disabled - Whether button is disabled
 * @param {Function} props.onClick - Click event handler
 * @param {'button'|'submit'|'reset'} props.type - HTML button type
 * @param {Object} props...props - Additional props passed to button element
 * 
 * @example
 * // Basic usage
 * <Button>Click me</Button>
 * 
 * @example
 * // With variant and size
 * <Button variant="success" size="large">Save</Button>
 * 
 * @example
 * // With click handler
 * <Button onClick={() => console.log('clicked')}>Submit</Button>
 */
import React, { forwardRef } from 'react';

const Button = forwardRef(({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  className = '', 
  disabled = false,
  isLoading = false,
  onClick,
  type = 'button',
  ...props 
}, ref) => {
  // Base button classes - applies to all button variants
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-full border-0 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  // Button variant styles - each variant has different colors and effects
  const variantClasses = {
    // Primary is now gradient (default look)
    primary: 'bg-gradient-to-br from-blue-500 to-blue-600 text-white font-semibold hover:from-blue-600 hover:to-blue-700 focus:ring-blue-500',
    // Subtle alternative kept as primarySubtle for low-emphasis actions
    primarySubtle: 'bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100 hover:text-blue-700 focus:ring-blue-500 shadow-sm hover:shadow-md',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500 shadow-sm hover:shadow-md',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-sm hover:shadow-md',
    outline: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:border-gray-400 focus:ring-gray-500 shadow-sm hover:shadow-md',

    // Solid variants (match page-level action buttons)
    primarySolid: 'bg-blue-600 text-white font-semibold hover:bg-blue-700 focus:ring-blue-500',
    successSolid: 'bg-green-600 text-white font-semibold hover:bg-green-700 focus:ring-green-500',
    secondarySolid: 'bg-gray-600 text-white font-semibold hover:bg-gray-700 focus:ring-gray-500',

    // (former gradient alias removed; primary now serves that purpose)
  };
  
  // Button size styles - controls padding and font size
  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-base',
    large: 'px-6 py-3 text-lg'
  };
  
  // Disabled state styling - reduces opacity and changes cursor
  const disabledClasses = disabled || isLoading ? 'opacity-50 cursor-not-allowed' : '';
  
  // Combine all classes into final className string
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabledClasses} ${className}`.trim();
  
  return (
    <button
      ref={ref}                      // Forward ref for focus management
      type={type}                    // HTML button type (button, submit, reset)
      className={classes}            // Combined CSS classes
      disabled={disabled || isLoading} // Disabled state
      onClick={onClick}             // Click event handler
      {...props}                     // Spread any additional props
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {children}
        </span>
      ) : (
        children                     /* Button content */
      )}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;
