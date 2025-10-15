import React from 'react';

const Button = ({ 
  variant = 'primary', 
  size = 'md', 
  children, 
  onClick, 
  disabled = false, 
  type = 'button',
  className = '',
  ...props 
}) => {
  const getVariantClass = () => {
    switch (variant) {
      case 'primary':
        return 'btn-primary';
      case 'secondary':
        return 'btn-secondary';
      case 'outline':
        return 'btn-outline-primary';
      case 'outline-secondary':
        return 'btn-outline-secondary';
      case 'success':
        return 'btn-success';
      case 'danger':
        return 'btn-danger';
      case 'warning':
        return 'btn-warning';
      case 'info':
        return 'btn-info';
      case 'light':
        return 'btn-light';
      case 'dark':
        return 'btn-dark';
      case 'link':
        return 'btn-link';
      default:
        return 'btn-primary';
    }
  };

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return 'btn-sm';
      case 'lg':
        return 'btn-lg';
      case 'md':
      default:
        return '';
    }
  };

  const buttonClasses = [
    'btn',
    getVariantClass(),
    getSizeClass(),
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      className={buttonClasses}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;