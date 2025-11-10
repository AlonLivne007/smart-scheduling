/**
 * LoginPage Component
 *
 * Public entry page. On success, stores token + user and redirects to "/".
 * On failure, shows an inline error message.
 */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import LoginHeader from "./LoginHeader.jsx";
import LoginForm from "./LoginForm.jsx";
import LoginLinks from "./LoginLinks.jsx";
import api from "../../lib/axios.js";

export default function LoginPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({ email: "", password: "" });
  const [errorMsg, setErrorMsg] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSubmitting(true);

    try {
      const { data } = await api.post("/users/login", {
        user_email: formData.email,
        user_password: formData.password,
      });

      // Persist auth
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("auth_user", JSON.stringify(data.user));

      // Go to protected HomePage (MainLayout -> Home)
      navigate("/", { replace: true });
    } catch (err) {
      // Prefer 401 → incorrect credentials
      if (err?.response?.status === 401) {
        setErrorMsg("Incorrect email or password.");
      } else {
        // Fallback to backend message or generic
        const msg =
          err?.response?.data?.detail ||
          err?.message ||
          "Login failed. Please try again.";
        setErrorMsg(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <LoginHeader />

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Error banner (shown only on failure) */}
          {errorMsg && (
            <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMsg}
            </div>
          )}

          {/* Form */}
          <LoginForm
            formData={formData}
            onInputChange={handleInputChange}
            onSubmit={handleSubmit}
            submitting={submitting}   // safe even if LoginForm ignores it
          />

          {/* Links (no signup) */}
          <LoginLinks />
        </div>
      </div>
    </div>
  );
}
