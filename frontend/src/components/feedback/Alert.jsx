import React, { useState } from 'react';

const Alert = ({
  type = 'info',
  title,
  children,
  dismissible = false,
  onDismiss,
  className = '',
  show = true,
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(show);

  const getTypeClass = () => {
    switch (type) {
      case 'success':
        return 'alert-success';
      case 'warning':
        return 'alert-warning';
      case 'error':
      case 'danger':
        return 'alert-danger';
      case 'info':
      default:
        return 'alert-info';
    }
  };

  const handleDismiss = () => {
    setIsVisible(false);
    if (onDismiss) {
      onDismiss();
    }
  };

  if (!isVisible) return null;

  const alertClasses = [
    'alert',
    getTypeClass(),
    dismissible ? 'alert-dismissible' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={alertClasses} role="alert" {...props}>
      {title && <h6 className="alert-heading">{title}</h6>}
      {children}
      {dismissible && (
        <button
          type="button"
          className="btn-close"
          aria-label="Close"
          onClick={handleDismiss}
        ></button>
      )}
    </div>
  );
};

export default Alert;