// frontend/src/pages/Admin/Employees/EmployeesPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../../lib/axios";

export default function EmployeesPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const navigate = useNavigate();

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const { data } = await api.get("/users");
      setUsers(data || []);
    } catch (e) {
      const m = e?.response?.data?.detail || e.message || "Failed to load users";
      setErr(m);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onDelete(userId) {
    if (!confirm("Delete this employee? This action cannot be undone.")) return;
    try {
      await api.delete(`/users/${userId}`);
      setUsers((prev) => prev.filter((u) => u.user_id !== userId));
    } catch (e) {
      const m = e?.response?.data?.detail || e.message || "Delete failed";
      alert(m);
    }
  }

  function onAdd() {
    navigate("/admin/add-user");
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Employees</h1>
        <button
          onClick={onAdd}
          className="rounded bg-blue-600 text-white px-3 py-1.5 hover:bg-blue-700"
        >
          Add New Employee
        </button>
      </div>

      {err && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </div>
      )}

      {loading ? (
        <div className="text-gray-600">Loading employees…</div>
      ) : users.length === 0 ? (
        <div className="text-gray-600">No employees found.</div>
      ) : (
        <div className="overflow-x-auto rounded border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Manager</th>
                <th className="px-3 py-2">Roles</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id} className="border-t">
                  <td className="px-3 py-2">{u.user_full_name}</td>
                  <td className="px-3 py-2">{u.user_email}</td>
                  <td className="px-3 py-2 capitalize">{u.user_status}</td>
                  <td className="px-3 py-2">{u.is_manager ? "Yes" : "No"}</td>
                  <td className="px-3 py-2">
                    {u.roles?.length
                      ? u.roles.map((r) => r.role_name).join(", ")
                      : "—"}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => onDelete(u.user_id)}
                        className="rounded bg-red-50 px-2 py-1 text-red-600 hover:bg-red-100"
                        title="Delete employee"
                      >
                        Delete
                      </button>
                      {/* (Optional) You can add an Edit button later to update roles/status */}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
