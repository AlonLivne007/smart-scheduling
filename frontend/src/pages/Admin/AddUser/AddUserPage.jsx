// frontend/src/pages/Admin/AddUser/AddUserPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../../lib/axios";
import InputField from "../../../components/ui/InputField.jsx";
import Button from "../../../components/ui/Button.jsx";

const DEFAULT_FORM = {
  user_full_name: "",
  user_email: "",
  user_password: "",
  user_status: "active",   // active | vacation | sick  (your enum)
  is_manager: false,
  role_id: "",             // we'll store single selected role id here
};

export default function AddUserPage() {
  const navigate = useNavigate();

  const [roles, setRoles] = useState([]);     // list from GET /roles
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Load roles for the selector
  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const { data } = await api.get("/roles");
        if (!canceled) setRoles(data || []);
      } catch (e) {
        if (!canceled) {
          const m = e?.response?.data?.detail || e.message || "Failed to load roles";
          setError(m);
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
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");

    // small validations
    if (!form.user_full_name.trim()) return setError("Full name is required.");
    if (!form.user_email.trim()) return setError("Email is required.");
    if (!form.user_password.trim()) return setError("Password is required.");
    if (!form.role_id) return setError("Please select a role.");

    setSaving(true);
    try {
      // Build payload expected by backend
      const payload = {
        user_full_name: form.user_full_name,
        user_email: form.user_email,
        user_password: form.user_password,
        user_status: form.user_status,  // "active" | "vacation" | "sick"
        is_manager: form.is_manager,
        roles_by_id: [Number(form.role_id)], // single role selection
      };

      await api.post("/users", payload); // admin-only; backend enforces RBAC
      navigate("/employees", { replace: true });
    } catch (e) {
      const m =
        e?.response?.data?.detail ||
        e.message ||
        "Failed to create user. Please try again.";
      setError(m);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-4 text-2xl font-semibold">Add New Employee</h1>

      {/* Error line */}
      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

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
              required
              disabled={saving}
            />
            <InputField
              label="Password"
              name="user_password"
              type="password"
              placeholder="Temporary password"
              value={form.user_password}
              onChange={onChange}
              required
              disabled={saving}
            />

            {/* Status select */}
            <div className="flex flex-col">
              <label className="mb-1 text-sm font-medium text-gray-700">Status</label>
              <select
                name="user_status"
                value={form.user_status}
                onChange={onChange}
                className="rounded border px-3 py-2"
                disabled={saving}
              >
                <option value="active">Active</option>
                <option value="vacation">Vacation</option>
                <option value="sick">Sick</option>
              </select>
            </div>

            {/* Role select (from DB) */}
            <div className="flex flex-col">
              <label className="mb-1 text-sm font-medium text-gray-700">Role</label>
              <select
                name="role_id"
                value={form.role_id}
                onChange={onChange}
                className="rounded border px-3 py-2"
                required
                disabled={saving}
              >
                <option value="">Select a role…</option>
                {roles.map((r) => (
                  <option key={r.role_id} value={r.role_id}>
                    {r.role_name}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Roles are loaded from the database.
              </p>
            </div>

            {/* Is Manager */}
            <div className="flex items-center gap-2">
              <input
                id="is_manager"
                name="is_manager"
                type="checkbox"
                checked={form.is_manager}
                onChange={onChange}
                disabled={saving}
              />
              <label htmlFor="is_manager" className="text-sm text-gray-700">
                Grant manager permissions
              </label>
            </div>
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
