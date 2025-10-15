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
    'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
    error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300',
    disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white',
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
        <div id={`${inputId}-error`} className="mt-1 text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
};

export default InputField;