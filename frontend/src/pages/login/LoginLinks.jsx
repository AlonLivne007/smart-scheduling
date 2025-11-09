/**
 * LoginLinks Component
 *
 * Navigation helpers on the login page.
 * - Keeps "Forgot password?" placeholder
 * - Removes public Sign-up (manager creates accounts)
 */
import React from "react";

function LoginLinks({ showForgot = true, showManagerHint = true }) {
  return (
    <>
      {/* Forgot Password (placeholder / wire later) */}
      {showForgot && (
        <div className="text-center">
          <a
            href="#"
            className="text-blue-500 hover:text-blue-600 text-sm transition-colors duration-200"
            onClick={(e) => {
              e.preventDefault();
              // TODO: hook to your password reset flow when available
              alert("Please contact your manager to reset your password.");
            }}
          >
            Forgot password?
          </a>
        </div>
      )}

      {/* Divider */}
      <div className="relative my-3">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
      </div>

      {/* Manager hint (no Sign-up link) */}
      {showManagerHint && (
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don’t have an account?{" "}
            <span className="font-medium text-gray-700">
              Ask your manager to create one.
            </span>
          </p>
        </div>
      )}
    </>
  );
}

export default LoginLinks;
