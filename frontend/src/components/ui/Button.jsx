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
  const baseClasses = 'btn border-0 rounded-pill fw-medium transition-all';
  
  const variantClasses = {
    primary: 'btn-primary bg-gradient',
    success: 'btn-success bg-gradient',
    danger: 'btn-danger bg-gradient'
  };
  
  const sizeClasses = {
    small: 'px-3 py-2 fs-6',
    medium: 'px-4 py-2',
    large: 'px-5 py-3 fs-5'
  };
  
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabledClasses} ${className}`.trim();
  
  return (
    <button
      type={type}
      className={classes}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
