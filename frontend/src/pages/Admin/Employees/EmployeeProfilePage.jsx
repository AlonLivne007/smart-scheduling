// frontend/src/pages/Admin/Employees/EmployeeProfilePage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { format, parseISO } from "date-fns";
import toast from "react-hot-toast";
import api from "../../../lib/axios";
import Button from "../../../components/ui/Button";
import Skeleton from "../../../components/ui/Skeleton";

export default function EmployeeProfilePage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [employee, setEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState("info");

  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get(`/users/${id}`);
        if (!canceled) setEmployee(data);
      } catch (e) {
        if (!canceled) {
          const msg = e?.response?.data?.detail || e.message || "Failed to load employee";
          toast.error(msg);
        }
      } finally {
        if (!canceled) setLoading(false);
      }
    })();
    return () => {
      canceled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-5xl">
        <Skeleton className="h-8 w-64 mb-6" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="max-w-5xl">
        <h1 className="text-2xl font-semibold mb-4">Employee Not Found</h1>
        <Button onClick={() => navigate("/employees")}>Back to Employees</Button>
      </div>
    );
  }

  const tabs = [
    { id: "info", label: "Info" },
    { id: "schedule", label: "Schedule" },
    { id: "time-off", label: "Time-Off" },
    { id: "preferences", label: "Preferences" },
  ];

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">{employee.user_full_name}</h1>
          <p className="text-gray-600">{employee.user_email}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={() => navigate("/employees")}>
            Back
          </Button>
          <Button variant="primary" onClick={() => navigate(`/employees/edit/${id}`)}>
            Edit Employee
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-xl shadow p-6">
        {activeTab === "info" && <InfoTab employee={employee} />}
        {activeTab === "schedule" && <ScheduleTab employeeId={id} />}
        {activeTab === "time-off" && <TimeOffTab employeeId={id} />}
        {activeTab === "preferences" && <PreferencesTab employeeId={id} />}
      </div>
    </div>
  );
}

// Info Tab - Basic employee information
function InfoTab({ employee }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <InfoField label="Full Name" value={employee.user_full_name} />
        <InfoField label="Email" value={employee.user_email} />
        <InfoField
          label="Roles"
          value={employee.roles?.map((r) => r.role_name).join(", ") || "No roles assigned"}
        />
        <InfoField label="Manager" value={employee.is_manager ? "Yes" : "No"} />
        <InfoField label="Status" value={employee.user_status || "ACTIVE"} />
        <InfoField
          label="Joined"
          value={
            employee.created_at
              ? format(new Date(employee.created_at), "MMM dd, yyyy")
              : "N/A"
          }
        />
      </div>
    </div>
  );
}

function InfoField({ label, value }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-500 mb-1">{label}</label>
      <p className="text-gray-900">{value}</p>
    </div>
  );
}

// Schedule Tab - Assigned shifts for current week
function ScheduleTab({ employeeId }) {
  const [loading, setLoading] = useState(true);
  const [assignments, setAssignments] = useState([]);

  function extractErrorMessage(e, fallback) {
    if (e?.response?.data?.detail) {
      const detail = e.response.data.detail;
      if (Array.isArray(detail)) {
        return detail.map((err) => err?.msg || JSON.stringify(err)).join(", ");
      }
      if (typeof detail === "string") return detail;
      return JSON.stringify(detail);
    }
    return e?.message || fallback;
  }

  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get(`/shift-assignments/by-user/${employeeId}`);

        // Axios will normally give an array here, but be defensive.
        const baseAssignments = Array.isArray(data) ? data : (data?.value || []);
        const shiftIds = Array.from(
          new Set(
            baseAssignments
              .map((a) => a?.planned_shift_id)
              .filter((v) => v !== null && v !== undefined)
              .map((v) => Number(v))
          )
        ).filter((v) => Number.isFinite(v) && v > 0);

        const shiftResponses = await Promise.all(
          shiftIds.map((sid) => api.get(`/planned-shifts/${sid}`))
        );
        const plannedShiftById = shiftResponses.reduce((acc, res) => {
          const ps = res?.data;
          if (ps?.planned_shift_id) {
            acc[Number(ps.planned_shift_id)] = ps;
          }
          return acc;
        }, {});

        const enriched = baseAssignments.map((a) => ({
          ...a,
          planned_shift: plannedShiftById[Number(a.planned_shift_id)] || null,
        }));

        if (!canceled) setAssignments(enriched);
      } catch (e) {
        if (!canceled) {
          toast.error(extractErrorMessage(e, "Failed to load shifts"));
        }
      } finally {
        if (!canceled) setLoading(false);
      }
    })();
    return () => {
      canceled = true;
    };
  }, [employeeId]);

  if (loading) {
    return <Skeleton className="h-64" />;
  }

  if (assignments.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No shift assignments found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Assigned Shifts</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Date</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Shift</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Time</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {assignments.map((assignment) => (
              <tr key={assignment.assignment_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">
                  {assignment.planned_shift?.date
                    ? format(parseISO(assignment.planned_shift.date), "EEE, MMM dd")
                    : "N/A"}
                </td>
                <td className="px-4 py-3 text-sm">
                  {assignment.planned_shift?.shift_template_name || "N/A"}
                  {assignment.role_name ? (
                    <div className="text-xs text-gray-500">Role: {assignment.role_name}</div>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {assignment.planned_shift?.start_time
                    ? format(new Date(assignment.planned_shift.start_time), "HH:mm")
                    : "N/A"} -{" "}
                  {assignment.planned_shift?.end_time
                    ? format(new Date(assignment.planned_shift.end_time), "HH:mm")
                    : "N/A"}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      assignment.planned_shift?.status === "FULLY_ASSIGNED"
                        ? "bg-green-100 text-green-800"
                        : assignment.planned_shift?.status === "PARTIALLY_ASSIGNED"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {assignment.planned_shift?.status || "N/A"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Time-Off Tab - Time-off requests
function TimeOffTab({ employeeId }) {
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get("/time-off/requests/", {
          params: { user_id: employeeId },
        });
        if (!canceled) setRequests(data || []);
      } catch (e) {
        if (!canceled) {
          const msg = e?.response?.data?.detail || e.message || "Failed to load time-off";
          toast.error(msg);
        }
      } finally {
        if (!canceled) setLoading(false);
      }
    })();
    return () => {
      canceled = true;
    };
  }, [employeeId]);

  if (loading) {
    return <Skeleton className="h-64" />;
  }

  if (requests.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No time-off requests found</p>
      </div>
    );
  }

  const getStatus = (r) => r?.status || r?.request_status;

  const pending = requests.filter((r) => getStatus(r) === "PENDING");
  const approved = requests.filter((r) => getStatus(r) === "APPROVED");
  const rejected = requests.filter((r) => getStatus(r) === "REJECTED");

  return (
    <div className="space-y-6">
      {/* Pending Requests */}
      {pending.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Pending Requests</h3>
          <RequestList requests={pending} />
        </div>
      )}

      {/* Approved Requests */}
      {approved.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Approved Time-Off</h3>
          <RequestList requests={approved} />
        </div>
      )}

      {/* Rejected Requests */}
      {rejected.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Rejected Requests</h3>
          <RequestList requests={rejected} />
        </div>
      )}
    </div>
  );
}

function RequestList({ requests }) {
  return (
    <div className="space-y-3">
      {requests.map((request) => {
        const requestId = request?.request_id ?? request?.time_off_request_id;
        const status = request?.status || request?.request_status || "UNKNOWN";
        const reviewer = request?.approved_by_name || request?.approver_name;

        return (
        <div
          key={requestId}
          className="border rounded-lg p-4 flex items-center justify-between"
        >
          <div>
            <div className="flex items-center gap-3">
              <span className="font-medium">
                {format(new Date(request.start_date), "MMM dd")} -{" "}
                {format(new Date(request.end_date), "MMM dd, yyyy")}
              </span>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  status === "APPROVED"
                    ? "bg-green-100 text-green-800"
                    : status === "PENDING"
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {status}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Type: {request.request_type}
              {reviewer && (
                <span className="ml-4">Reviewed by: {reviewer}</span>
              )}
            </p>
          </div>
        </div>
        );
      })}
    </div>
  );
}

// Preferences Tab - Shift preferences management
function PreferencesTab({ employeeId }) {
  const [loading, setLoading] = useState(true);
  const [preferences, setPreferences] = useState([]);
  const [shiftTemplates, setShiftTemplates] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);

  // Fetch preferences and shift templates
  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      try {
        const [prefsRes, templatesRes] = await Promise.all([
          api.get(`/employees/${employeeId}/preferences`),
          api.get("/shift-templates/"),
        ]);
        if (!canceled) {
          setPreferences(prefsRes.data);
          setShiftTemplates(templatesRes.data);
        }
      } catch (e) {
        if (!canceled) {
          const msg = e?.response?.data?.detail || "Failed to load preferences";
          toast.error(msg);
        }
      } finally {
        if (!canceled) setLoading(false);
      }
    })();
    return () => {
      canceled = true;
    };
  }, [employeeId]);

  const handleDelete = async (preferenceId) => {
    if (!confirm("Delete this preference?")) return;
    try {
      await api.delete(`/employees/${employeeId}/preferences/${preferenceId}`);
      setPreferences(preferences.filter((p) => p.preference_id !== preferenceId));
      toast.success("Preference deleted");
    } catch (e) {
      const msg = e?.response?.data?.detail || "Failed to delete preference";
      toast.error(msg);
    }
  };

  const refreshPreferences = async () => {
    try {
      const { data } = await api.get(`/employees/${employeeId}/preferences`);
      setPreferences(data);
    } catch (e) {
      const msg = e?.response?.data?.detail || "Failed to refresh preferences";
      toast.error(msg);
    }
  };

  if (loading) {
    return <Skeleton className="h-64" />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Shift Preferences</h3>
          <p className="text-sm text-gray-600 mt-1">
            Manage employee shift preferences for optimization
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => {
            setEditingId(null);
            setShowAddForm(true);
          }}
        >
          + Add Preference
        </Button>
      </div>

      {/* Add/Edit Form */}
      {showAddForm && (
        <PreferenceForm
          employeeId={employeeId}
          shiftTemplates={shiftTemplates}
          onSuccess={() => {
            setShowAddForm(false);
            refreshPreferences();
          }}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      {/* Preferences List */}
      {preferences.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white mb-4">
            <svg
              className="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
              />
            </svg>
          </div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">No Preferences Set</h4>
          <p className="text-gray-600">
            Add shift preferences to help the optimizer assign preferred shifts.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {preferences.map((pref) => (
            <PreferenceCard
              key={pref.preference_id}
              preference={pref}
              employeeId={employeeId}
              shiftTemplates={shiftTemplates}
              onEdit={(id) => {
                setEditingId(id);
                setShowAddForm(false);
              }}
              onDelete={handleDelete}
              onUpdate={refreshPreferences}
              isEditing={editingId === pref.preference_id}
              onCancelEdit={() => setEditingId(null)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Preference Card Component
function PreferenceCard({
  preference,
  employeeId,
  shiftTemplates,
  onEdit,
  onDelete,
  onUpdate,
  isEditing,
  onCancelEdit,
}) {
  if (isEditing) {
    return (
      <PreferenceForm
        employeeId={employeeId}
        shiftTemplates={shiftTemplates}
        initialData={preference}
        onSuccess={() => {
          onCancelEdit();
          onUpdate();
        }}
        onCancel={onCancelEdit}
      />
    );
  }

  const getWeightColor = (weight) => {
    if (weight >= 0.8) return "bg-green-100 text-green-800";
    if (weight >= 0.5) return "bg-blue-100 text-blue-800";
    return "bg-gray-100 text-gray-800";
  };

  const getWeightLabel = (weight) => {
    if (weight >= 0.8) return "High";
    if (weight >= 0.5) return "Medium";
    return "Low";
  };

  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium ${getWeightColor(
                preference.preference_weight
              )}`}
            >
              {getWeightLabel(preference.preference_weight)} Priority (
              {preference.preference_weight.toFixed(1)})
            </span>
          </div>

          <div className="space-y-1 text-sm">
            {preference.shift_template_name && (
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-700">Shift Template:</span>
                <span className="text-gray-900">{preference.shift_template_name}</span>
              </div>
            )}
            {preference.preferred_day_of_week && (
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-700">Preferred Day:</span>
                <span className="text-gray-900">{preference.preferred_day_of_week}</span>
              </div>
            )}
            {preference.preferred_start_time && preference.preferred_end_time && (
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-700">Preferred Time:</span>
                <span className="text-gray-900">
                  {preference.preferred_start_time} - {preference.preferred_end_time}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={() => onEdit(preference.preference_id)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded"
            title="Edit"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
          <button
            onClick={() => onDelete(preference.preference_id)}
            className="p-2 text-red-600 hover:bg-red-50 rounded"
            title="Delete"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

// Preference Form Component
function PreferenceForm({ employeeId, shiftTemplates, initialData, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    preferred_shift_template_id: initialData?.preferred_shift_template_id || "",
    preferred_day_of_week: initialData?.preferred_day_of_week || "",
    preferred_start_time: initialData?.preferred_start_time || "",
    preferred_end_time: initialData?.preferred_end_time || "",
    preference_weight: initialData?.preference_weight ?? 0.5,
  });
  const [submitting, setSubmitting] = useState(false);

  const daysOfWeek = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const payload = {
        preferred_shift_template_id: formData.preferred_shift_template_id || null,
        preferred_day_of_week: formData.preferred_day_of_week || null,
        preferred_start_time: formData.preferred_start_time || null,
        preferred_end_time: formData.preferred_end_time || null,
        preference_weight: parseFloat(formData.preference_weight),
      };

      if (initialData) {
        // Update existing
        await api.put(
          `/employees/${employeeId}/preferences/${initialData.preference_id}`,
          payload
        );
        toast.success("Preference updated");
      } else {
        // Create new
        await api.post(`/employees/${employeeId}/preferences`, payload);
        toast.success("Preference created");
      }

      onSuccess();
    } catch (e) {
      const msg = e?.response?.data?.detail || "Failed to save preference";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-gray-50">
      <h4 className="font-semibold mb-4">
        {initialData ? "Edit Preference" : "Add New Preference"}
      </h4>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Shift Template */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Shift Template (Optional)
            </label>
            <select
              value={formData.preferred_shift_template_id}
              onChange={(e) =>
                setFormData({ ...formData, preferred_shift_template_id: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">-- Select Template --</option>
              {shiftTemplates.map((t) => (
                <option key={t.shift_template_id} value={t.shift_template_id}>
                  {t.shift_template_name}
                </option>
              ))}
            </select>
          </div>

          {/* Day of Week */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preferred Day (Optional)
            </label>
            <select
              value={formData.preferred_day_of_week}
              onChange={(e) =>
                setFormData({ ...formData, preferred_day_of_week: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">-- Select Day --</option>
              {daysOfWeek.map((day) => (
                <option key={day} value={day}>
                  {day}
                </option>
              ))}
            </select>
          </div>

          {/* Start Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preferred Start Time (Optional)
            </label>
            <input
              type="time"
              value={formData.preferred_start_time}
              onChange={(e) =>
                setFormData({ ...formData, preferred_start_time: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* End Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preferred End Time (Optional)
            </label>
            <input
              type="time"
              value={formData.preferred_end_time}
              onChange={(e) =>
                setFormData({ ...formData, preferred_end_time: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Preference Weight */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Importance / Priority Weight: {parseFloat(formData.preference_weight).toFixed(1)}
          </label>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">Low</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.preference_weight}
              onChange={(e) =>
                setFormData({ ...formData, preference_weight: parseFloat(e.target.value) })
              }
              className="flex-1"
            />
            <span className="text-sm text-gray-600">High</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Higher weights give this preference more importance during optimization
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Saving..." : initialData ? "Update" : "Create"}
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel} disabled={submitting}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
