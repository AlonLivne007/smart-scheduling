// frontend/src/pages/Admin/AddUser/AddUserPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import api from "../../../lib/axios";
import InputField from "../../../components/ui/InputField.jsx";
import Button from "../../../components/ui/Button.jsx";
import { validators } from "../../../components/ui/InputField.jsx";

const DEFAULT_FORM = {
  user_full_name: "",
  user_email: "",
  user_password: "",
  is_manager: false,
  roles_selected: [],    // array of role_ids
};

export default function AddUserPage() {
  const navigate = useNavigate();

  const [roles, setRoles] = useState([]);     // list from GET /roles
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});   // field-level errors

  // Load roles for the selector
  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get("/roles");
        if (!canceled) setRoles(data || []);
      } catch (e) {
        if (!canceled) {
          const m = e?.response?.data?.detail || e.message || "Failed to load roles";
          toast.error(m);
        }
      } finally {
        if (!canceled) setLoading(false);
      }
    })();
    return () => {
      canceled = true;
    };
  }, []);

  function onChange(e) {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    // Clear field error when user types
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  }

  function toggleRole(roleId) {
    setForm((prev) => {
      const selected = prev.roles_selected.includes(roleId)
        ? prev.roles_selected.filter((id) => id !== roleId)
        : [...prev.roles_selected, roleId];
      return { ...prev, roles_selected: selected };
    });
    // Clear role error when user selects
    if (errors.roles_selected) {
      setErrors((prev) => ({ ...prev, roles_selected: "" }));
    }
  }

  function validateForm() {
    const newErrors = {};

    // Full name
    if (!form.user_full_name.trim()) {
      newErrors.user_full_name = "Full name is required.";
    }

    // Email
    if (!form.user_email.trim()) {
      newErrors.user_email = "Email is required.";
    } else {
      const emailError = validators.email()(form.user_email);
      if (emailError) newErrors.user_email = emailError;
    }

    // Password
    if (!form.user_password.trim()) {
      newErrors.user_password = "Password is required.";
    } else if (form.user_password.length < 6) {
      newErrors.user_password = "Password must be at least 6 characters.";
    }

    // Roles
    if (form.roles_selected.length === 0) {
      newErrors.roles_selected = "Please select at least one role.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function onSubmit(e) {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error("Please fix the errors before submitting.");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        user_full_name: form.user_full_name.trim(),
        user_email: form.user_email.trim(),
        user_password: form.user_password,
        is_manager: form.is_manager,
        roles_by_id: form.roles_selected,
      };

      await api.post("/users", payload);
      toast.success("Employee created successfully!");
      navigate("/employees", { replace: true });
    } catch (e) {
      // Check for email uniqueness error
      if (e?.response?.status === 400 && e?.response?.data?.detail?.includes("email")) {
        setErrors((prev) => ({ ...prev, user_email: "This email is already in use." }));
        toast.error("Email already exists.");
      } else {
        const m = e?.response?.data?.detail || e.message || "Failed to create user. Please try again.";
        toast.error(m);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-4 text-2xl font-semibold">Add New Employee</h1>

      {loading ? (
        <div className="text-gray-600">Loading roles…</div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-5 bg-white p-6 rounded-xl shadow">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InputField
              label="Full Name"
              name="user_full_name"
              type="text"
              placeholder="e.g., Dana Cohen"
              value={form.user_full_name}
              onChange={onChange}
              error={errors.user_full_name}
              required
              disabled={saving}
            />
            <InputField
              label="Email"
              name="user_email"
              type="email"
              placeholder="name@example.com"
              value={form.user_email}
              onChange={onChange}
              error={errors.user_email}
              required
              disabled={saving}
            />
            <InputField
              label="Password"
              name="user_password"
              type="password"
              placeholder="At least 6 characters"
              value={form.user_password}
              onChange={onChange}
              error={errors.user_password}
              required
              disabled={saving}
            />

            {/* Manager checkbox */}
            <div className="flex items-center gap-2 mt-2">
              <input
                id="is_manager"
                name="is_manager"
                type="checkbox"
                checked={form.is_manager}
                onChange={onChange}
                disabled={saving}
                className="h-4 w-4"
              />
              <label htmlFor="is_manager" className="text-sm text-gray-700">
                Manager
              </label>
            </div>
          </div>

          {/* Roles - Multi-select checkboxes */}
          <div className="flex flex-col">
            <label className="mb-2 text-sm font-medium text-gray-700">
              Roles <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3 p-4 border rounded-lg">
              {roles.map((role) => (
                <label
                  key={role.role_id}
                  className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                >
                  <input
                    type="checkbox"
                    checked={form.roles_selected.includes(role.role_id)}
                    onChange={() => toggleRole(role.role_id)}
                    disabled={saving}
                    className="h-4 w-4"
                  />
                  <span className="text-sm text-gray-700">{role.role_name}</span>
                </label>
              ))}
            </div>
            {errors.roles_selected && (
              <p className="mt-1 text-sm text-red-600">{errors.roles_selected}</p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Creating…" : "Create Employee"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate("/employees")}
              disabled={saving}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
