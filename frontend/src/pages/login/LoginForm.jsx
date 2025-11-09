/**
 * LoginForm Component
 *
 * Handles the main login form with email and password fields.
 * Supports a submitting state to disable inputs and show progress.
 *
 * @component
 * @param {Object}   props
 * @param {Object}   props.formData
 * @param {Function} props.onInputChange
 * @param {Function} props.onSubmit
 * @param {boolean}  [props.submitting=false]
 * @returns {JSX.Element}
 */
import React from "react";
import InputField from "../../components/ui/InputField.jsx";
import Button from "../../components/ui/Button.jsx";

function LoginForm({ formData, onInputChange, onSubmit, submitting = false }) {
  return (
    <form onSubmit={onSubmit} className="space-y-6" aria-busy={submitting}>
      {/* Email Field */}
      <InputField
        label="Email Address"
        type="email"
        name="email"
        placeholder="Email Address"
        value={formData.email}
        onChange={onInputChange}
        required
        autoComplete="email"
        disabled={submitting}
      />

      {/* Password Field */}
      <InputField
        label="Password"
        type="password"
        name="password"
        placeholder="Password"
        value={formData.password}
        onChange={onInputChange}
        required
        autoComplete="current-password"
        disabled={submitting}
      />

      {/* Login Button */}
      <Button
        type="submit"
        variant="primary"
        className="w-full"
        disabled={submitting}
      >
        {submitting ? "Logging in..." : "Login"}
      </Button>
    </form>
  );
}

export default LoginForm;
