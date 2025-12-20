import React, { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import api from "../../lib/axios";
import Button from "../../components/ui/Button";
import InputField, { validators } from "../../components/ui/InputField";
import Skeleton from "../../components/ui/Skeleton";
import ConfirmDialog from "../../components/ui/ConfirmDialog";

function formatTemplateTime(start, end) {
  const s = start ? String(start).slice(0, 5) : null;
  const e = end ? String(end).slice(0, 5) : null;
  if (!s && !e) return "—";
  return `${s || "?"} - ${e || "?"}`;
}

function summarizeRequirements(requiredRoles) {
  if (!Array.isArray(requiredRoles) || requiredRoles.length === 0) return "—";
  return requiredRoles
    .map((r) => {
      const name = r?.role_name || `Role ${r?.role_id}`;
      const count = Number(r?.required_count) || 1;
      return `${name} x${count}`;
    })
    .join(", ");
}

export default function ShiftTemplatesManagementPage() {
  const [loading, setLoading] = useState(true);
  const [rolesLoading, setRolesLoading] = useState(true);

  const [templates, setTemplates] = useState([]);
  const [roles, setRoles] = useState([]);

  const [submitting, setSubmitting] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [name, setName] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [location, setLocation] = useState("");

  // { [role_id]: required_count }
  const [requiredCounts, setRequiredCounts] = useState({});

  const templateNamesLower = useMemo(
    () => new Set((templates || []).map((t) => String(t.shift_template_name || "").trim().toLowerCase())),
    [templates]
  );

  async function loadTemplates() {
    setLoading(true);
    try {
      const { data } = await api.get("/shift-templates/");
      setTemplates(Array.isArray(data) ? data : []);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to load shift templates";
      toast.error(msg);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadRoles() {
    setRolesLoading(true);
    try {
      const { data } = await api.get("/roles/");
      setRoles(Array.isArray(data) ? data : []);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to load roles";
      toast.error(msg);
      setRoles([]);
    } finally {
      setRolesLoading(false);
    }
  }

  useEffect(() => {
    loadTemplates();
    loadRoles();
  }, []);

  function resetForm() {
    setEditingId(null);
    setName("");
    setStartTime("");
    setEndTime("");
    setLocation("");
    setRequiredCounts({});
  }

  function startEdit(template) {
    setEditingId(template.shift_template_id);
    setName(template.shift_template_name || "");
    setStartTime(template.start_time ? String(template.start_time).slice(0, 5) : "");
    setEndTime(template.end_time ? String(template.end_time).slice(0, 5) : "");
    setLocation(template.location || "");

    const nextCounts = {};
    (Array.isArray(template.required_roles) ? template.required_roles : []).forEach((r) => {
      if (r?.role_id) nextCounts[Number(r.role_id)] = Number(r.required_count) || 1;
    });
    setRequiredCounts(nextCounts);
  }

  function toggleRole(roleId) {
    const rid = Number(roleId);
    setRequiredCounts((prev) => {
      const next = { ...prev };
      if (next[rid]) {
        delete next[rid];
      } else {
        next[rid] = 1;
      }
      return next;
    });
  }

  function setRoleCount(roleId, count) {
    const rid = Number(roleId);
    const c = Math.max(1, Number(count) || 1);
    setRequiredCounts((prev) => ({ ...prev, [rid]: c }));
  }

  function validate() {
    const trimmed = name.trim();
    if (!trimmed) {
      toast.error("Template name is required");
      return false;
    }

    const nextLower = trimmed.toLowerCase();
    const original = templates.find((t) => t.shift_template_id === editingId);
    const originalLower = String(original?.shift_template_name || "").trim().toLowerCase();

    if (nextLower !== originalLower && templateNamesLower.has(nextLower)) {
      toast.error("Template name must be unique");
      return false;
    }

    if (startTime && endTime && startTime >= endTime) {
      toast.error("End time must be after start time");
      return false;
    }

    return true;
  }

  async function handleSave() {
    if (!validate()) return;

    const payload = {
      shift_template_name: name.trim(),
      start_time: startTime || null,
      end_time: endTime || null,
      location: location.trim() || null,
      required_roles: Object.entries(requiredCounts).map(([roleId, requiredCount]) => ({
        role_id: Number(roleId),
        required_count: Number(requiredCount) || 1,
      })),
    };

    setSubmitting(true);
    try {
      if (editingId) {
        await api.put(`/shift-templates/${editingId}`, payload);
        toast.success("Shift template updated");
      } else {
        await api.post("/shift-templates/", payload);
        toast.success("Shift template created");
      }
      resetForm();
      await loadTemplates();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to save shift template";
      toast.error(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  }

  async function confirmDelete() {
    if (!templateToDelete) return;
    setDeleting(true);
    try {
      await api.delete(`/shift-templates/${templateToDelete.shift_template_id}`);
      toast.success("Shift template deleted");
      setTemplateToDelete(null);
      await loadTemplates();
      if (editingId === templateToDelete.shift_template_id) {
        resetForm();
      }
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to delete shift template";
      toast.error(msg);
    } finally {
      setDeleting(false);
    }
  }

  const selectedRoleIds = useMemo(
    () => new Set(Object.keys(requiredCounts).map((k) => Number(k))),
    [requiredCounts]
  );

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Shift Template Management</h1>
        <p className="text-gray-600 mt-1">Create and manage reusable shift templates</p>
      </div>

      {/* Create / Edit form */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">
            {editingId ? "Edit Shift Template" : "Create Shift Template"}
          </h2>
          {editingId ? (
            <Button variant="outline" onClick={resetForm} disabled={submitting}>
              Cancel Edit
            </Button>
          ) : null}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InputField
            label="Template Name"
            placeholder="e.g., Morning Shift"
            value={name}
            onChange={(e) => setName(e.target.value)}
            validators={[validators.required("Template name is required")]}
            showSuccess
          />

          <InputField
            label="Location"
            placeholder="e.g., Main Store"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />

          <InputField
            label="Start Time"
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />

          <InputField
            label="End Time"
            type="time"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
          />
        </div>

        <div className="mt-2">
          <div className="text-sm font-medium text-gray-700 mb-2">Required Roles</div>
          {rolesLoading ? (
            <Skeleton height={80} />
          ) : roles.length === 0 ? (
            <div className="text-sm text-gray-600">No roles found. Create roles first.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {roles.map((role) => {
                const checked = selectedRoleIds.has(role.role_id);
                const count = requiredCounts[role.role_id] || 1;
                return (
                  <div
                    key={role.role_id}
                    className="flex items-center justify-between border rounded-lg px-3 py-2 bg-white"
                  >
                    <label className="flex items-center gap-2 text-sm text-gray-900">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleRole(role.role_id)}
                      />
                      {role.role_name}
                    </label>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Count</span>
                      <input
                        type="number"
                        min={1}
                        className="w-20 px-2 py-1 border border-gray-300 rounded-lg"
                        disabled={!checked}
                        value={count}
                        onChange={(e) => setRoleCount(role.role_id, e.target.value)}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <Button onClick={handleSave} disabled={submitting} isLoading={submitting}>
            {editingId ? "Save Changes" : "Create Template"}
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
        ) : templates.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No shift templates found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Required Roles
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {templates.map((tpl) => (
                  <tr key={tpl.shift_template_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {tpl.shift_template_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {formatTemplateTime(tpl.start_time, tpl.end_time)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">{tpl.location || "—"}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {summarizeRequirements(tpl.required_roles)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2 justify-end">
                        <Button size="sm" variant="outline" onClick={() => startEdit(tpl)}>
                          Edit
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => setTemplateToDelete(tpl)}>
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!templateToDelete}
        onClose={() => (deleting ? null : setTemplateToDelete(null))}
        onConfirm={confirmDelete}
        title="Delete Shift Template"
        message={
          templateToDelete
            ? `Are you sure you want to delete "${templateToDelete.shift_template_name}"?`
            : "Are you sure you want to delete this shift template?"
        }
        confirmText="Delete"
        variant="danger"
        isLoading={deleting}
      />
    </div>
  );
}
