/**
 * Card Component
 * 
 * A flexible card component for displaying content with consistent styling.
 * Uses Tailwind CSS for modern, utility-first styling with glass morphism effects.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Card content
 * @param {string} props.className - Additional CSS classes
 * @param {'default'|'primary'|'light'|'gradient'} props.variant - Card style variant
 * @param {'none'|'small'|'medium'|'large'} props.padding - Internal padding size
 * @param {boolean} props.hover - Whether to show hover lift effect
 * @param {Object} props...props - Additional props passed to div element
 * 
 * @example
 * // Basic card
 * <Card>Content here</Card>
 * 
 * @example
 * // Card with variant and hover
 * <Card variant="primary" hover>Blue card with hover effect</Card>
 * 
 * @example
 * // Card with custom padding
 * <Card padding="large">Large padding card</Card>
 */
import React from 'react';

const Card = ({ 
  children, 
  className = '', 
  variant = 'default',
  padding = 'medium',
  hover = false,
  ...props 
}) => {
  // Base card classes - applies to all card variants
  // Base without background so variant can fully control bg
  const baseClasses = 'backdrop-blur-sm border border-white/20 shadow-sm rounded-xl transition-all duration-300';
  
  // Card variant styles - different background colors and text colors
  const variantClasses = {
    default: 'bg-white/90',              // White background with transparency
    primary: 'bg-blue-600 text-white',   // Blue background with white text
    light: 'bg-blue-50',                 // Light blue background
    gradient: 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' // Blue gradient background
  };
  
  // Padding size options - controls internal spacing
  const paddingClasses = {
    none: '',        // No padding
    small: 'p-3',    // Small padding (12px)
    medium: 'p-4',   // Medium padding (16px)
    large: 'p-6'     // Large padding (24px)
  };
  
  // Hover effect classes - adds lift animation on hover
  const hoverClasses = hover ? 'hover:shadow-lg hover:-translate-y-1' : '';
  
  // Combine all classes into final className string
  const classes = `${baseClasses} ${variantClasses[variant]} ${paddingClasses[padding]} ${hoverClasses} ${className}`.trim();
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

/**
 * CardHeader Component
 * 
 * Header section for cards with transparent background and bottom padding.
 * 
 * @param {React.ReactNode} children - Header content
 * @param {string} className - Additional CSS classes
 * @param {Object} props - Additional props
 */
const CardHeader = ({ children, className = '', ...props }) => (
  <div className={`bg-transparent border-0 pb-2 ${className}`} {...props}>
    {children}
  </div>
);

/**
 * CardBody Component
 * 
 * Main content area for cards with standard body styling.
 * 
 * @param {React.ReactNode} children - Body content
 * @param {string} className - Additional CSS classes
 * @param {Object} props - Additional props
 */
const CardBody = ({ children, className = '', ...props }) => (
  <div className={`${className}`} {...props}>
    {children}
  </div>
);

/**
 * CardFooter Component
 * 
 * Footer section for cards with transparent background and top padding.
 * 
 * @param {React.ReactNode} children - Footer content
 * @param {string} className - Additional CSS classes
 * @param {Object} props - Additional props
 */
const CardFooter = ({ children, className = '', ...props }) => (
  <div className={`bg-transparent border-0 pt-2 ${className}`} {...props}>
    {children}
  </div>
);

/**
 * CardTitle Component
 * 
 * Title element for cards with semibold font weight and margin.
 * 
 * @param {React.ReactNode} children - Title text
 * @param {string} className - Additional CSS classes
 * @param {Object} props - Additional props
 */
const CardTitle = ({ children, className = '', ...props }) => (
  <h5 className={`font-semibold mb-2 text-gray-900 ${className}`} {...props}>
    {children}
  </h5>
);

/**
 * CardText Component
 * 
 * Text element for cards with muted color and no bottom margin.
 * 
 * @param {React.ReactNode} children - Text content
 * @param {string} className - Additional CSS classes
 * @param {Object} props - Additional props
 */
const CardText = ({ children, className = '', ...props }) => (
  <p className={`text-gray-600 mb-0 ${className}`} {...props}>
    {children}
  </p>
);

// Attach sub-components to main Card component for easy access
Card.Header = CardHeader;  // <Card.Header>Content</Card.Header>
Card.Body = CardBody;      // <Card.Body>Content</Card.Body>
Card.Footer = CardFooter;  // <Card.Footer>Content</Card.Footer>
Card.Title = CardTitle;    // <Card.Title>Title</Card.Title>
Card.Text = CardText;      // <Card.Text>Description</Card.Text>

export default Card;
