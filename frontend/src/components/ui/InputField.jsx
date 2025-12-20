/**
 * InputField Component
 * 
 * Enhanced input field with comprehensive validation support, visual feedback,
 * and accessibility features.
 * 
 * Features:
 * - Real-time validation with customizable rules
 * - Visual state indicators (error/success/default)
 * - Touch/blur validation (errors show only after interaction)
 * - Built-in validators: email, minLength, maxLength, pattern, required
 * - Custom validation function support
 * - Success state with green border when valid
 * - Disabled/read-only states
 * - Accessible with ARIA attributes
 * 
 * @component
 * @example
 * // Basic usage with built-in email validator
 * <InputField
 *   label="Email"
 *   value={email}
 *   onChange={(e) => setEmail(e.target.value)}
 *   validators={[validators.email(), validators.required()]}
 *   showSuccess
 * />
 * 
 * @example
 * // Custom validation
 * <InputField
 *   label="Username"
 *   value={username}
 *   onChange={(e) => setUsername(e.target.value)}
 *   validators={[
 *     validators.required('Username is required'),
 *     validators.minLength(3, 'Must be at least 3 characters'),
 *     (value) => value.includes('@') ? 'Username cannot contain @' : null
 *   ]}
 * />
 */
import React, { useState, useEffect } from 'react';

/**
 * Built-in validation functions
 */
export const validators = {
  /**
   * Validates required fields
   */
  required: (message = 'This field is required') => (value) => {
    if (!value || value.toString().trim() === '') {
      return message;
    }
    return null;
  },

  /**
   * Validates email format
   */
  email: (message = 'Please enter a valid email address') => (value) => {
    if (!value) return null; // Only validate if value exists
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(value) ? null : message;
  },

  /**
   * Validates minimum length
   */
  minLength: (min, message) => (value) => {
    if (!value) return null; // Only validate if value exists
    const msg = message || `Must be at least ${min} characters`;
    return value.length >= min ? null : msg;
  },

  /**
   * Validates maximum length
   */
  maxLength: (max, message) => (value) => {
    if (!value) return null; // Only validate if value exists
    const msg = message || `Must be no more than ${max} characters`;
    return value.length <= max ? null : msg;
  },

  /**
   * Validates against a regex pattern
   */
  pattern: (regex, message = 'Invalid format') => (value) => {
    if (!value) return null; // Only validate if value exists
    return regex.test(value) ? null : message;
  },

  /**
   * Validates numeric values
   */
  number: (message = 'Please enter a valid number') => (value) => {
    if (!value) return null;
    return !isNaN(value) ? null : message;
  },

  /**
   * Validates minimum numeric value
   */
  min: (minValue, message) => (value) => {
    if (!value) return null;
    const msg = message || `Must be at least ${minValue}`;
    return Number(value) >= minValue ? null : msg;
  },

  /**
   * Validates maximum numeric value
   */
  max: (maxValue, message) => (value) => {
    if (!value) return null;
    const msg = message || `Must be no more than ${maxValue}`;
    return Number(value) <= maxValue ? null : msg;
  },
};

const InputField = ({
  label,
  placeholder,
  value,
  onChange,
  onBlur,
  type = 'text',
  error: externalError, // External error prop (for form-level validation)
  disabled = false,
  readOnly = false,
  required = false,
  className = '',
  id,
  name,
  validators: validationRules = [],
  showSuccess = false, // Show green border when valid
  validateOnChange = false, // Validate while typing (default: only on blur)
  helperText, // Optional helper text shown below field
  ...props
}) => {
  const [touched, setTouched] = useState(false);
  const [internalError, setInternalError] = useState(null);
  const [isValid, setIsValid] = useState(false);

  const inputId = id || name || `input-${Math.random().toString(36).substr(2, 9)}`;

  // Use external error if provided, otherwise use internal error
  const displayError = externalError || (touched ? internalError : null);
  const showValidState = showSuccess && touched && !displayError && value && isValid;

  /**
   * Run all validators and return first error found
   */
  const validate = (val) => {
    for (const validator of validationRules) {
      const error = validator(val);
      if (error) {
        return error;
      }
    }
    return null;
  };

  /**
   * Validate on value change
   */
  useEffect(() => {
    if (validationRules.length > 0) {
      const error = validate(value);
      setInternalError(error);
      setIsValid(!error && value !== '');
      
      // Clear error when user starts typing correct value
      if (touched && validateOnChange && !error) {
        setInternalError(null);
      }
    }
  }, [value, validationRules, validateOnChange, touched]);

  /**
   * Handle input change
   */
  const handleChange = (e) => {
    onChange(e);
    
    // Clear error when user starts typing
    if (touched && displayError) {
      if (validateOnChange) {
        const error = validate(e.target.value);
        setInternalError(error);
      }
    }
  };

  /**
   * Handle input blur - marks field as touched and validates
   */
  const handleBlur = (e) => {
    setTouched(true);
    
    if (validationRules.length > 0) {
      const error = validate(value);
      setInternalError(error);
    }
    
    if (onBlur) {
      onBlur(e);
    }
  };

  /**
   * Build input classes based on state
   */
  const inputClasses = [
    'w-full px-3 py-2 border-2 rounded-lg focus:ring-2 focus:outline-none transition-all duration-200',
    // Error state
    displayError
      ? 'border-red-500 focus:ring-red-200 focus:border-red-500 bg-red-50'
      : showValidState
      ? 'border-green-500 focus:ring-green-200 focus:border-green-500 bg-green-50'
      : 'border-gray-300 focus:ring-blue-200 focus:border-blue-500 bg-white',
    // Disabled/readonly state
    disabled || readOnly ? 'bg-gray-100 cursor-not-allowed text-gray-500' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className="mb-4">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <input
          id={inputId}
          name={name}
          type={type}
          className={inputClasses}
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          readOnly={readOnly}
          required={required}
          aria-invalid={displayError ? 'true' : 'false'}
          aria-describedby={
            displayError
              ? `${inputId}-error`
              : helperText
              ? `${inputId}-helper`
              : undefined
          }
          {...props}
        />
        
        {/* Success indicator icon */}
        {showValidState && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
        )}
        
        {/* Error indicator icon */}
        {displayError && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      {/* Error message */}
      {displayError && (
        <div id={`${inputId}-error`} className="mt-1 text-sm text-red-600 flex items-start gap-1">
          <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>{displayError}</span>
        </div>
      )}

      {/* Helper text */}
      {!displayError && helperText && (
        <div id={`${inputId}-helper`} className="mt-1 text-sm text-gray-500">
          {helperText}
        </div>
      )}
    </div>
  );
};

export default InputField;