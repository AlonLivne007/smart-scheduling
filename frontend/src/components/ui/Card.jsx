import React from 'react';

const Card = ({ 
  children, 
  className = '', 
  variant = 'default',
  padding = 'medium',
  hover = false,
  ...props 
}) => {
  const baseClasses = 'card border-0 shadow-sm rounded-3';
  
  const variantClasses = {
    default: 'bg-white',
    primary: 'bg-primary text-white',
    light: 'bg-light',
    gradient: 'bg-gradient'
  };
  
  const paddingClasses = {
    none: '',
    small: 'p-3',
    medium: 'p-4',
    large: 'p-5'
  };
  
  const hoverClasses = hover ? 'hover-lift' : '';
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${paddingClasses[padding]} ${hoverClasses} ${className}`.trim();
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardHeader = ({ children, className = '', ...props }) => (
  <div className={`card-header bg-transparent border-0 pb-2 ${className}`} {...props}>
    {children}
  </div>
);

const CardBody = ({ children, className = '', ...props }) => (
  <div className={`card-body ${className}`} {...props}>
    {children}
  </div>
);

const CardFooter = ({ children, className = '', ...props }) => (
  <div className={`card-footer bg-transparent border-0 pt-2 ${className}`} {...props}>
    {children}
  </div>
);

const CardTitle = ({ children, className = '', ...props }) => (
  <h5 className={`card-title fw-semibold mb-2 ${className}`} {...props}>
    {children}
  </h5>
);

const CardText = ({ children, className = '', ...props }) => (
  <p className={`card-text text-muted mb-0 ${className}`} {...props}>
    {children}
  </p>
);

Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;
Card.Title = CardTitle;
Card.Text = CardText;

export default Card;
