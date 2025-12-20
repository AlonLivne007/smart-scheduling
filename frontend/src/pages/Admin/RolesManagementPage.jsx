import React, { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import api from "../../lib/axios";
import Button from "../../components/ui/Button";
import InputField, { validators } from "../../components/ui/InputField";
import Skeleton from "../../components/ui/Skeleton";
import ConfirmDialog from "../../components/ui/ConfirmDialog";

export default function RolesManagementPage() {
  const [loading, setLoading] = useState(true);
  const [roles, setRoles] = useState([]);

  const [newRoleName, setNewRoleName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [editingRoleId, setEditingRoleId] = useState(null);
  const [editingRoleName, setEditingRoleName] = useState("");

  const [roleToDelete, setRoleToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const roleNamesLower = useMemo(
    () => new Set((roles || []).map((r) => String(r.role_name || "").trim().toLowerCase())),
    [roles]
  );

  async function loadRoles() {
    setLoading(true);
    try {
      const { data } = await api.get("/roles/");
      setRoles(Array.isArray(data) ? data : []);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to load roles";
      toast.error(msg);
      setRoles([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRoles();
  }, []);

  async function handleCreateRole() {
    const name = newRoleName.trim();
    if (!name) {
      toast.error("Role name is required");
      return;
    }
    if (roleNamesLower.has(name.toLowerCase())) {
      toast.error("Role name must be unique");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/roles/", { role_name: name });
      toast.success("Role created");
      setNewRoleName("");
      await loadRoles();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to create role";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(role) {
    setEditingRoleId(role.role_id);
    setEditingRoleName(role.role_name || "");
  }

  function cancelEdit() {
    setEditingRoleId(null);
    setEditingRoleName("");
  }

  async function saveEdit() {
    const roleId = editingRoleId;
    const nextName = editingRoleName.trim();

    if (!roleId) return;
    if (!nextName) {
      toast.error("Role name is required");
      return;
    }

    const original = roles.find((r) => r.role_id === roleId);
    const originalLower = String(original?.role_name || "").trim().toLowerCase();
    const nextLower = nextName.toLowerCase();

    if (nextLower !== originalLower && roleNamesLower.has(nextLower)) {
      toast.error("Role name must be unique");
      return;
    }

    setSubmitting(true);
    try {
      await api.put(`/roles/${roleId}`, { role_name: nextName });
      toast.success("Role updated");
      cancelEdit();
      await loadRoles();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to update role";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  async function confirmDelete() {
    if (!roleToDelete) return;
    setDeleting(true);
    try {
      await api.delete(`/roles/${roleToDelete.role_id}`);
      toast.success("Role deleted");
      setRoleToDelete(null);
      await loadRoles();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to delete role";
      toast.error(msg);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Role Management</h1>
        <p className="text-gray-600 mt-1">Create and manage roles used across the system</p>
      </div>

      {/* Create */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end">
          <InputField
            label="New Role Name"
            placeholder="e.g., Waiter"
            value={newRoleName}
            onChange={(e) => setNewRoleName(e.target.value)}
            validators={[validators.required("Role name is required")]}
            showSuccess
          />
          <Button onClick={handleCreateRole} disabled={submitting} isLoading={submitting}>
            Create Role
          </Button>
        </div>
      </div>

      {/* List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            <Skeleton height={50} />
            <Skeleton height={50} />
            <Skeleton height={50} />
          </div>
        ) : roles.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No roles found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {roles.map((role) => {
                  const isEditing = editingRoleId === role.role_id;
                  return (
                    <tr key={role.role_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        {isEditing ? (
                          <InputField
                            label={null}
                            value={editingRoleName}
                            onChange={(e) => setEditingRoleName(e.target.value)}
                            validators={[validators.required("Role name is required")]}
                            validateOnChange
                            showSuccess
                            className="mb-0"
                          />
                        ) : (
                          <div className="text-sm font-medium text-gray-900">{role.role_name}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex gap-2 justify-end">
                          {isEditing ? (
                            <>
                              <Button
                                size="sm"
                                onClick={saveEdit}
                                disabled={submitting}
                                isLoading={submitting}
                              >
                                Save
                              </Button>
                              <Button size="sm" variant="outline" onClick={cancelEdit} disabled={submitting}>
                                Cancel
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button size="sm" variant="outline" onClick={() => startEdit(role)}>
                                Edit
                              </Button>
                              <Button
                                size="sm"
                                variant="danger"
                                onClick={() => setRoleToDelete(role)}
                              >
                                Delete
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!roleToDelete}
        onClose={() => (deleting ? null : setRoleToDelete(null))}
        onConfirm={confirmDelete}
        title="Delete Role"
        message={
          roleToDelete
            ? `Are you sure you want to delete the role "${roleToDelete.role_name}"?`
            : "Are you sure you want to delete this role?"
        }
        confirmText="Delete"
        variant="danger"
        sideEffects={["Deletion may fail if this role is assigned to any shift assignments."]}
        isLoading={deleting}
      />
    </div>
  );
}
