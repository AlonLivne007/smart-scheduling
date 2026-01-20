// frontend/src/pages/MyPreferencesPage.jsx
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import api from "../lib/axios";
import Button from "../components/ui/Button";
import Skeleton from "../components/ui/Skeleton";

export default function MyPreferencesPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [preferences, setPreferences] = useState([]);
  const [shiftTemplates, setShiftTemplates] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const authUser = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('auth_user') || 'null');
    } catch {
      return null;
    }
  }, []);

  const userId = authUser?.user_id;

  // Fetch preferences and shift templates
  useEffect(() => {
    if (!userId) {
      toast.error("User not authenticated");
      navigate("/login");
      return;
    }

    let canceled = false;
    (async () => {
      setLoading(true);
      try {
        const [prefsRes, templatesRes] = await Promise.all([
          api.get(`/employee-preferences/users/${userId}`),
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
  }, [userId, navigate]);

  const handleDelete = async (preferenceId) => {
    if (!confirm("Delete this preference?")) return;
    try {
      await api.delete(`/employee-preferences/users/${userId}/preferences/${preferenceId}`);
      setPreferences(preferences.filter((p) => p.preference_id !== preferenceId));
      toast.success("Preference deleted");
    } catch (e) {
      const msg = e?.response?.data?.detail || "Failed to delete preference";
      toast.error(msg);
    }
  };

  const refreshPreferences = async () => {
    try {
      const { data } = await api.get(`/employee-preferences/users/${userId}`);
      setPreferences(data);
    } catch (e) {
      const msg = e?.response?.data?.detail || "Failed to refresh preferences";
      toast.error(msg);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <Skeleton className="h-8 w-64 mb-6" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold mb-2">My Shift Preferences</h1>
        <p className="text-gray-600">
          Set your preferred shifts, days, and times. The system will consider these when
          generating schedules.
        </p>
      </div>

      {/* Add Preference Button */}
      <div className="mb-6">
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
        <div className="mb-6">
          <PreferenceForm
            userId={userId}
            shiftTemplates={shiftTemplates}
            onSuccess={() => {
              setShowAddForm(false);
              refreshPreferences();
            }}
            onCancel={() => setShowAddForm(false)}
          />
        </div>
      )}

      {/* Preferences List */}
      <div className="bg-white rounded-xl shadow">
        {preferences.length === 0 ? (
          <div className="text-center py-12 px-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
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
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Preferences Set</h3>
            <p className="text-gray-600 mb-4">
              Add your shift preferences to help the system assign you to shifts you prefer.
            </p>
            <Button
              variant="primary"
              onClick={() => setShowAddForm(true)}
            >
              Add Your First Preference
            </Button>
          </div>
        ) : (
          <div className="divide-y">
            {preferences.map((pref) => (
              <PreferenceCard
                key={pref.preference_id}
                preference={pref}
                userId={userId}
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

      {/* Info Box */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg
            className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <h4 className="font-medium text-blue-900 mb-1">How Preferences Work</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Preferences are considered during schedule optimization</li>
              <li>• Higher priority preferences are weighted more heavily</li>
              <li>• You can set multiple preferences with different priorities</li>
              <li>• Your manager can view your preferences when creating schedules</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

// Preference Card Component
function PreferenceCard({
  preference,
  userId,
  shiftTemplates,
  onEdit,
  onDelete,
  onUpdate,
  isEditing,
  onCancelEdit,
}) {
  if (isEditing) {
    return (
      <div className="p-6 bg-gray-50">
        <PreferenceForm
          userId={userId}
          shiftTemplates={shiftTemplates}
          initialData={preference}
          onSuccess={() => {
            onCancelEdit();
            onUpdate();
          }}
          onCancel={onCancelEdit}
        />
      </div>
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
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${getWeightColor(
                preference.preference_weight
              )}`}
            >
              {getWeightLabel(preference.preference_weight)} Priority (
              {preference.preference_weight.toFixed(1)})
            </span>
          </div>

          <div className="space-y-2">
            {preference.shift_template_name && (
              <div className="flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span className="font-medium text-gray-700">Shift Template:</span>
                <span className="text-gray-900">{preference.shift_template_name}</span>
              </div>
            )}
            {preference.preferred_day_of_week && (
              <div className="flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <span className="font-medium text-gray-700">Preferred Day:</span>
                <span className="text-gray-900">{preference.preferred_day_of_week}</span>
              </div>
            )}
            {preference.preferred_start_time && preference.preferred_end_time && (
              <div className="flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
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
            className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
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
            className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
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
function PreferenceForm({ userId, shiftTemplates, initialData, onSuccess, onCancel }) {
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
          `/employee-preferences/users/${userId}/preferences/${initialData.preference_id}`,
          payload
        );
        toast.success("Preference updated successfully!");
      } else {
        // Create new
        await api.post(`/employee-preferences/users/${userId}`, payload);
        toast.success("Preference added successfully!");
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
    <div className="border rounded-lg p-6 bg-white">
      <h3 className="font-semibold mb-4 text-lg">
        {initialData ? "Edit Preference" : "Add New Preference"}
      </h3>
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
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Importance / Priority: <span className="font-bold">{parseFloat(formData.preference_weight).toFixed(1)}</span>
          </label>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 font-medium">Low</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.preference_weight}
              onChange={(e) =>
                setFormData({ ...formData, preference_weight: parseFloat(e.target.value) })
              }
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-sm text-gray-600 font-medium">High</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Higher values give this preference more weight during schedule optimization
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2 border-t">
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Saving..." : initialData ? "Update Preference" : "Add Preference"}
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel} disabled={submitting}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
