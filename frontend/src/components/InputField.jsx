import React from 'react';

const InputField = ({
  label,
  placeholder,
  value,
  onChange,
  type = 'text',
  error,
  disabled = false,
  required = false,
  className = '',
  id,
  name,
  ...props
}) => {
  const inputId = id || name || `input-${Math.random().toString(36).substr(2, 9)}`;
  
  const inputClasses = [
    'form-control',
    error ? 'is-invalid' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className="mb-3">
      {label && (
        <label htmlFor={inputId} className="form-label">
          {label}
          {required && <span className="text-danger ms-1">*</span>}
        </label>
      )}
      <input
        id={inputId}
        name={name}
        type={type}
        className={inputClasses}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        aria-describedby={error ? `${inputId}-error` : undefined}
        {...props}
      />
      {error && (
        <div id={`${inputId}-error`} className="invalid-feedback">
          {error}
        </div>
      )}
    </div>
  );
};

export default InputField;