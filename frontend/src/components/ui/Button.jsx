/**
 * Button Component
 * 
 * A reusable button component with consistent styling and multiple variants.
 * Uses Bootstrap classes with custom CSS overrides for the blue theme.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Button content (text, icons, etc.)
 * @param {'primary'|'success'|'danger'} props.variant - Button style variant
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
import React from 'react';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  className = '', 
  disabled = false,
  onClick,
  type = 'button',
  ...props 
}) => {
  // Base button classes - applies to all button variants
  const baseClasses = 'btn border-0 rounded-pill fw-medium transition-all';
  
  // Button variant styles - each variant has different colors and effects
  const variantClasses = {
    primary: 'btn-primary bg-gradient',    // Light blue background with blue text
    success: 'btn-success bg-gradient',    // Green background with white text
    danger: 'btn-danger bg-gradient'       // Red background with white text
  };
  
  // Button size styles - controls padding and font size
  const sizeClasses = {
    small: 'px-3 py-2 fs-6',    // Small padding, small font
    medium: 'px-4 py-2',        // Medium padding, default font
    large: 'px-5 py-3 fs-5'     // Large padding, large font
  };
  
  // Disabled state styling - reduces opacity and changes cursor
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';
  
  // Combine all classes into final className string
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabledClasses} ${className}`.trim();
  
  return (
    <button
      type={type}                    // HTML button type (button, submit, reset)
      className={classes}            // Combined CSS classes
      disabled={disabled}            // Disabled state
      onClick={onClick}             // Click event handler
      {...props}                     // Spread any additional props
    >
      {children}                     {/* Button content */}
    </button>
  );
};

export default Button;
