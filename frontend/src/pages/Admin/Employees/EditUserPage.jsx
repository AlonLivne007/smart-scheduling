// frontend/src/pages/Admin/Employees/EditUserPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../../lib/axios";
import InputField from "../../../components/ui/InputField.jsx";
import Button from "../../../components/ui/Button.jsx";

export default function EditUserPage() {
  const { id } = useParams(); // user_id
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [roles, setRoles] = useState([]);
  const [form, setForm] = useState({
    user_full_name: "",
    user_email: "",
    is_manager: false,
    new_password: "",
    roles_selected: [],
  });

  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [userRes, rolesRes] = await Promise.all([
          api.get(`/users/${id}`),
          api.get("/roles"),
        ]);

        const user = userRes.data;
        const allRoles = rolesRes.data || [];

        if (!canceled) {
          setRoles(allRoles);
          setForm({
            user_full_name: user.user_full_name,
            user_email: user.user_email,
            is_manager: user.is_manager,
            new_password: "",
            roles_selected: (user.roles || []).map((r) => r.role_id),
          });
        }
      } catch (e) {
        if (!canceled) {
          const m = e?.response?.data?.detail || e.message || "Failed to load user";
          setError(m);
        }
      } finally {
        if (!canceled) setLoading(false);
      }
    })();
    return () => {
      canceled = true;
    };
  }, [id]);

  const roleIndexById = useMemo(() => {
    const map = new Map();
    roles.forEach((r, i) => map.set(r.role_id, i));
    return map;
  }, [roles]);

  function onChange(e) {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function onChangeRoles(e) {
    const selected = Array.from(e.target.selectedOptions).map((o) => Number(o.value));
    setForm((p) => ({ ...p, roles_selected: selected }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = {
        user_full_name: form.user_full_name,
        user_email: form.user_email,
        is_manager: form.is_manager,
        roles_by_id: form.roles_selected,
      };
      if (form.new_password?.trim()) {
        payload.new_password = form.new_password.trim();
      }

      await api.put(`/users/${id}`, payload);
      navigate("/employees", { replace: true });
    } catch (e) {
      const m =
        e?.response?.data?.detail ||
        e.message ||
        "Failed to update user. Please try again.";
      setError(m);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="mb-4 text-2xl font-semibold">Edit Employee</h1>

      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-gray-600">Loading…</div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-5 bg-white p-6 rounded-xl shadow">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InputField
              label="Full Name"
              name="user_full_name"
              type="text"
              value={form.user_full_name}
              onChange={onChange}
              required
              disabled={saving}
            />

            <InputField
              label="Email"
              name="user_email"
              type="email"
              value={form.user_email}
              onChange={onChange}
              required
              disabled={saving}
            />

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
                Manager
              </label>
            </div>

            <InputField
              label="New Password (optional)"
              name="new_password"
              type="password"
              placeholder="Leave blank to keep current password"
              value={form.new_password}
              onChange={onChange}
              disabled={saving}
            />

            <div className="flex flex-col md:col-span-2">
              <label className="mb-1 text-sm font-medium text-gray-700">Roles</label>
              <select
                multiple
                className="rounded border px-3 py-2 min-h-28"
                value={form.roles_selected}
                onChange={onChangeRoles}
                disabled={saving}
              >
                {roles.map((r) => (
                  <option key={r.role_id} value={r.role_id}>
                    {r.role_name}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Hold Ctrl/Command to select multiple roles.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Saving…" : "Save Changes"}
            </Button>
            <Button type="button" variant="secondary" onClick={() => navigate("/employees")} disabled={saving}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
