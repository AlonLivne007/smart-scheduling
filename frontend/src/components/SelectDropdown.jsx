import React from 'react';

const SelectDropdown = ({
  label,
  options = [],
  value,
  onChange,
  placeholder = 'Select an option',
  error,
  disabled = false,
  required = false,
  className = '',
  id,
  name,
  ...props
}) => {
  const selectId = id || name || `select-${Math.random().toString(36).substr(2, 9)}`;
  
  const selectClasses = [
    'form-select',
    error ? 'is-invalid' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className="mb-3">
      {label && (
        <label htmlFor={selectId} className="form-label">
          {label}
          {required && <span className="text-danger ms-1">*</span>}
        </label>
      )}
      <select
        id={selectId}
        name={name}
        className={selectClasses}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        aria-describedby={error ? `${selectId}-error` : undefined}
        {...props}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((option, index) => (
          <option key={option.value || index} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <div id={`${selectId}-error`} className="invalid-feedback">
          {error}
        </div>
      )}
    </div>
  );
};

export default SelectDropdown;