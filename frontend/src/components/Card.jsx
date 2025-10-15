import React from 'react';

const Card = ({
  title,
  subtitle,
  children,
  footer,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footerClassName = '',
  variant = 'default',
  ...props
}) => {
  const getVariantClass = () => {
    switch (variant) {
      case 'primary':
        return 'border-primary';
      case 'secondary':
        return 'border-secondary';
      case 'success':
        return 'border-success';
      case 'danger':
        return 'border-danger';
      case 'warning':
        return 'border-warning';
      case 'info':
        return 'border-info';
      case 'light':
        return 'border-light';
      case 'dark':
        return 'border-dark';
      case 'default':
      default:
        return '';
    }
  };

  const cardClasses = [
    'card',
    'shadow-sm',
    getVariantClass(),
    className
  ].filter(Boolean).join(' ');

  const headerClasses = [
    'card-header',
    headerClassName
  ].filter(Boolean).join(' ');

  const bodyClasses = [
    'card-body',
    bodyClassName
  ].filter(Boolean).join(' ');

  const footerClasses = [
    'card-footer',
    'text-muted',
    footerClassName
  ].filter(Boolean).join(' ');

  return (
    <div className={cardClasses} {...props}>
      {(title || subtitle) && (
        <div className={headerClasses}>
          {title && <h5 className="card-title mb-0">{title}</h5>}
          {subtitle && <h6 className="card-subtitle text-muted">{subtitle}</h6>}
        </div>
      )}
      <div className={bodyClasses}>
        {children}
      </div>
      {footer && (
        <div className={footerClasses}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;