// frontend/src/pages/Admin/Schedule/CreateScheduleWizardPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { format, addDays, startOfWeek } from "date-fns";
import toast from "react-hot-toast";
import api from "../../../lib/axios";
import Button from "../../../components/ui/Button";
import InputField from "../../../components/ui/InputField";
import Skeleton from "../../../components/ui/Skeleton";

export default function CreateScheduleWizardPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [loadingRoles, setLoadingRoles] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [roles, setRoles] = useState([]);

  // Form data
  const [weekStartDate, setWeekStartDate] = useState("");
  const [selectedTemplates, setSelectedTemplates] = useState([]);
  const [selectedDays, setSelectedDays] = useState([]);

  // Requirements per template: { [templateId]: Array<{ role_id: number, required_count: number }> }
  const [templateRequirements, setTemplateRequirements] = useState({});
  const [newReqRoleId, setNewReqRoleId] = useState({});
  const [newReqCount, setNewReqCount] = useState({});

  const DAYS_OF_WEEK = [
    { id: 0, name: "Monday", short: "Mon" },
    { id: 1, name: "Tuesday", short: "Tue" },
    { id: 2, name: "Wednesday", short: "Wed" },
    { id: 3, name: "Thursday", short: "Thu" },
    { id: 4, name: "Friday", short: "Fri" },
    { id: 5, name: "Saturday", short: "Sat" },
    { id: 6, name: "Sunday", short: "Sun" },
  ];

  // Load shift templates on mount
  useEffect(() => {
    loadTemplates();
    loadRoles();
  }, []);

  async function loadTemplates() {
    setLoadingTemplates(true);
    try {
      const { data } = await api.get("/shift-templates/");
      setTemplates(data || []);

      const initialReqs = (data || []).reduce((acc, tpl) => {
        const reqs = Array.isArray(tpl.required_roles) ? tpl.required_roles : [];
        acc[tpl.shift_template_id] = reqs
          .filter((r) => r && r.role_id)
          .map((r) => ({
            role_id: Number(r.role_id),
            required_count: Number(r.required_count) || 1,
          }));
        return acc;
      }, {});
      setTemplateRequirements(initialReqs);
    } catch (e) {
      let msg = "Failed to load templates";
      if (e?.response?.data?.detail) {
        const detail = e.response.data.detail;
        if (Array.isArray(detail)) {
          msg = detail.map(err => err.msg || JSON.stringify(err)).join(", ");
        } else if (typeof detail === 'string') {
          msg = detail;
        } else {
          msg = JSON.stringify(detail);
        }
      } else if (e.message) {
        msg = e.message;
      }
      toast.error(msg);
    } finally {
      setLoadingTemplates(false);
    }
  }

  async function loadRoles() {
    setLoadingRoles(true);
    try {
      const { data } = await api.get("/roles/");
      setRoles(data || []);
    } catch (e) {
      let msg = "Failed to load roles";
      if (e?.response?.data?.detail) {
        const detail = e.response.data.detail;
        if (Array.isArray(detail)) {
          msg = detail.map((err) => err.msg || JSON.stringify(err)).join(", ");
        } else if (typeof detail === "string") {
          msg = detail;
        } else {
          msg = JSON.stringify(detail);
        }
      } else if (e.message) {
        msg = e.message;
      }
      toast.error(msg);
    } finally {
      setLoadingRoles(false);
    }
  }

  function getRoleName(roleId) {
    const r = roles.find((x) => x.role_id === Number(roleId));
    return r?.role_name || `Role ${roleId}`;
  }

  function handleNext() {
    // Validate current step
    if (currentStep === 1 && !weekStartDate) {
      toast.error("Please select a week start date");
      return;
    }
    if (currentStep === 2 && selectedTemplates.length === 0) {
      toast.error("Please select at least one shift template");
      return;
    }
    if (currentStep === 2) {
      const templatesMissingReqs = selectedTemplates
        .map((templateId) => {
          const reqs = templateRequirements[templateId] || [];
          return reqs.length === 0 ? templateId : null;
        })
        .filter(Boolean);

      if (templatesMissingReqs.length > 0) {
        const names = templatesMissingReqs
          .map((templateId) => templates.find((t) => t.shift_template_id === templateId)?.shift_template_name || `Template ${templateId}`)
          .join(", ");
        toast.error(`Please add requirements for: ${names}`);
        return;
      }
    }
    if (currentStep === 3 && selectedDays.length === 0) {
      toast.error("Please select at least one day of the week");
      return;
    }

    setCurrentStep((prev) => Math.min(prev + 1, 4));
  }

  function handleBack() {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  }

  function toggleTemplate(templateId) {
    setSelectedTemplates((prev) =>
      prev.includes(templateId)
        ? prev.filter((id) => id !== templateId)
        : [...prev, templateId]
    );
  }

  function toggleDay(dayId) {
    setSelectedDays((prev) =>
      prev.includes(dayId) ? prev.filter((id) => id !== dayId) : [...prev, dayId]
    );
  }

  async function handleSubmit() {
    setLoading(true);
    try {
      // Get current user ID from localStorage
      const authUser = JSON.parse(localStorage.getItem("auth_user") || "{}");
      const userId = authUser?.user_id;

      if (!userId) {
        toast.error("User not authenticated. Please log in again.");
        navigate("/login");
        return;
      }

      // Step 1: Create weekly schedule
      const schedulePayload = {
        week_start_date: weekStartDate,
        created_by_id: userId,
      };

      const { data: schedule } = await api.post("/weekly-schedules/", schedulePayload);

      // Step 1.5: Ensure selected templates have requirements (update templates)
      const templateUpdatePayloads = selectedTemplates.map((templateId) => ({
        templateId,
        payload: {
          required_roles: (templateRequirements[templateId] || []).map((r) => ({
            role_id: Number(r.role_id),
            required_count: Number(r.required_count) || 1,
          })),
        },
      }));

      await Promise.all(
        templateUpdatePayloads.map(({ templateId, payload }) =>
          api.put(`/shift-templates/${templateId}`, payload)
        )
      );

      // Step 2: Create planned shifts for each selected template and day
      const shiftsToCreate = [];
      selectedDays.forEach((dayOffset) => {
        selectedTemplates.forEach((templateId) => {
          const shiftDate = addDays(new Date(weekStartDate), dayOffset);
          shiftsToCreate.push({
            weekly_schedule_id: schedule.weekly_schedule_id,
            shift_template_id: templateId,
            date: format(shiftDate, "yyyy-MM-dd"),
          });
        });
      });

      // Create all shifts
      await Promise.all(
        shiftsToCreate.map((shift) => api.post("/planned-shifts/", shift))
      );

      toast.success(
        `Schedule created with ${shiftsToCreate.length} planned shifts!`
      );
      navigate(`/schedules/${schedule.weekly_schedule_id}`);
    } catch (e) {
      let msg = "Failed to create schedule";
      if (e?.response?.data?.detail) {
        const detail = e.response.data.detail;
        if (Array.isArray(detail)) {
          msg = detail.map(err => err.msg || JSON.stringify(err)).join(", ");
        } else if (typeof detail === 'string') {
          msg = detail;
        } else {
          msg = JSON.stringify(detail);
        }
      } else if (e.message) {
        msg = e.message;
      }
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  function addRequirement(templateId) {
    const roleId = Number(newReqRoleId[templateId]);
    const count = Math.max(1, Number(newReqCount[templateId]) || 1);

    if (!roleId) {
      toast.error("Please select a role");
      return;
    }

    setTemplateRequirements((prev) => {
      const existing = prev[templateId] || [];
      const next = existing.some((r) => Number(r.role_id) === roleId)
        ? existing.map((r) =>
            Number(r.role_id) === roleId ? { ...r, required_count: count } : r
          )
        : [...existing, { role_id: roleId, required_count: count }];
      return { ...prev, [templateId]: next };
    });

    setNewReqRoleId((prev) => ({ ...prev, [templateId]: "" }));
    setNewReqCount((prev) => ({ ...prev, [templateId]: 1 }));
  }

  function removeRequirement(templateId, roleId) {
    setTemplateRequirements((prev) => {
      const existing = prev[templateId] || [];
      const next = existing.filter((r) => Number(r.role_id) !== Number(roleId));
      return { ...prev, [templateId]: next };
    });
  }

  // Get the next Monday as default suggestion
  const getNextMonday = () => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const daysUntilMonday = dayOfWeek === 0 ? 1 : 8 - dayOfWeek; // If Sunday, next day; else days until next Monday
    const nextMonday = addDays(today, daysUntilMonday);
    return format(nextMonday, "yyyy-MM-dd");
  };

  const steps = [
    { number: 1, title: "Week Start Date", icon: "📅" },
    { number: 2, title: "Shift Templates", icon: "📋" },
    { number: 3, title: "Days of Week", icon: "📆" },
    { number: 4, title: "Review & Create", icon: "✓" },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Create Weekly Schedule</h1>
        <p className="text-gray-600 mt-1">
          Follow the steps to create a new weekly schedule
        </p>
      </div>

      {/* Step Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <React.Fragment key={step.number}>
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-semibold mb-2 ${
                    currentStep >= step.number
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {step.icon}
                </div>
                <div
                  className={`text-sm font-medium text-center ${
                    currentStep >= step.number ? "text-blue-600" : "text-gray-500"
                  }`}
                >
                  {step.title}
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`h-1 flex-1 mx-2 mt-[-20px] ${
                    currentStep > step.number ? "bg-blue-600" : "bg-gray-200"
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Content Card */}
      <div className="bg-white rounded-xl shadow p-8 mb-6">
        {/* Step 1: Select Week Start Date */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Select Week Start Date</h2>
              <p className="text-gray-600 text-sm mb-6">
                Choose the Monday that starts the week for this schedule
              </p>
            </div>

            <div className="max-w-md">
              <InputField
                label="Week Start Date (Monday)"
                type="date"
                value={weekStartDate}
                onChange={(e) => setWeekStartDate(e.target.value)}
                required
              />
              <p className="mt-2 text-sm text-gray-500">
                Suggested next Monday: {getNextMonday()}
              </p>
              {!weekStartDate && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => setWeekStartDate(getNextMonday())}
                >
                  Use Next Monday
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Step 2: Select Shift Templates */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Select Shift Templates</h2>
              <p className="text-gray-600 text-sm mb-6">
                Choose which types of shifts to include in this schedule
              </p>
            </div>

            {loadingTemplates ? (
              <div className="space-y-3">
                <Skeleton height={60} />
                <Skeleton height={60} />
                <Skeleton height={60} />
              </div>
            ) : templates.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <p className="text-gray-600 mb-4">
                  No shift templates found. Please create templates first.
                </p>
                <Button variant="primary" onClick={() => navigate("/settings")}>
                  Go to Settings
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map((template) => (
                  <label
                    key={template.shift_template_id}
                    className={`flex items-start gap-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedTemplates.includes(template.shift_template_id)
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:bg-gray-50"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedTemplates.includes(template.shift_template_id)}
                      onChange={() => toggleTemplate(template.shift_template_id)}
                      className="mt-1 h-5 w-5"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {template.shift_template_name}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {template.start_time} - {template.end_time}
                      </div>
                      {template.location && (
                        <div className="text-xs text-gray-500 mt-1">
                          📍 {template.location}
                        </div>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            )}

            <div className="mt-4 text-sm text-gray-600">
              Selected: {selectedTemplates.length} template(s)
            </div>

            {/* Requirements editor for selected templates */}
            {selectedTemplates.length > 0 && (
              <div className="mt-6 border-t pt-6">
                <h3 className="text-lg font-semibold mb-2">Shift Requirements</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Add required roles for each selected template (these requirements are saved on the template).
                </p>

                {loadingRoles ? (
                  <div className="space-y-2">
                    <Skeleton height={40} />
                    <Skeleton height={40} />
                  </div>
                ) : roles.length === 0 ? (
                  <div className="text-sm text-red-700">
                    No roles found. Create roles first.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {selectedTemplates.map((templateId) => {
                      const template = templates.find((t) => t.shift_template_id === templateId);
                      const reqs = templateRequirements[templateId] || [];

                      return (
                        <div key={templateId} className="border border-gray-200 rounded-lg p-4">
                          <div className="font-medium text-gray-900 mb-2">
                            {template?.shift_template_name || `Template ${templateId}`}
                          </div>

                          {reqs.length === 0 ? (
                            <div className="text-sm text-red-700 mb-3">No requirements yet — please add at least one.</div>
                          ) : (
                            <div className="space-y-2 mb-3">
                              {reqs.map((r) => (
                                <div key={r.role_id} className="flex items-center justify-between text-sm">
                                  <div className="text-gray-800">
                                    {getRoleName(r.role_id)}
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <div className="text-gray-700">
                                      {r.required_count} required
                                    </div>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => removeRequirement(templateId, r.role_id)}
                                    >
                                      Remove
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                              <select
                                value={newReqRoleId[templateId] || ""}
                                onChange={(e) =>
                                  setNewReqRoleId((prev) => ({ ...prev, [templateId]: e.target.value }))
                                }
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              >
                                <option value="">Select role…</option>
                                {roles.map((role) => (
                                  <option key={role.role_id} value={role.role_id}>
                                    {role.role_name}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Count</label>
                              <input
                                type="number"
                                min={1}
                                value={newReqCount[templateId] ?? 1}
                                onChange={(e) =>
                                  setNewReqCount((prev) => ({ ...prev, [templateId]: e.target.value }))
                                }
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                            </div>

                            <div className="flex items-end">
                              <Button
                                variant="primary"
                                onClick={() => addRequirement(templateId)}
                                disabled={roles.length === 0}
                              >
                                Add / Update
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Select Days of Week */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Select Days of Week</h2>
              <p className="text-gray-600 text-sm mb-6">
                Choose which days to create shifts for
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {DAYS_OF_WEEK.map((day) => (
                <label
                  key={day.id}
                  className={`flex flex-col items-center justify-center p-6 border rounded-lg cursor-pointer transition-colors ${
                    selectedDays.includes(day.id)
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:bg-gray-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedDays.includes(day.id)}
                    onChange={() => toggleDay(day.id)}
                    className="hidden"
                  />
                  <div className="text-3xl mb-2">
                    {selectedDays.includes(day.id) ? "✓" : day.short[0]}
                  </div>
                  <div className="font-medium text-gray-900">{day.short}</div>
                  <div className="text-xs text-gray-500">{day.name}</div>
                </label>
              ))}
            </div>

            <div className="flex gap-4 mt-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedDays([0, 1, 2, 3, 4])}
              >
                Select Weekdays
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedDays([5, 6])}
              >
                Select Weekend
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedDays([0, 1, 2, 3, 4, 5, 6])}
              >
                Select All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedDays([])}
              >
                Clear
              </Button>
            </div>

            <div className="mt-4 text-sm text-gray-600">
              Selected: {selectedDays.length} day(s)
            </div>
          </div>
        )}

        {/* Step 4: Review & Submit */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Review & Create</h2>
              <p className="text-gray-600 text-sm mb-6">
                Review your schedule configuration before creating
              </p>
            </div>

            <div className="space-y-6">
              {/* Week Start Date */}
              <div className="border-b pb-4">
                <div className="text-sm text-gray-500 mb-1">Week Start Date</div>
                <div className="font-medium text-gray-900">
                  {weekStartDate
                    ? format(new Date(weekStartDate), "EEEE, MMMM d, yyyy")
                    : "Not selected"}
                </div>
              </div>

              {/* Selected Templates */}
              <div className="border-b pb-4">
                <div className="text-sm text-gray-500 mb-2">
                  Shift Templates ({selectedTemplates.length})
                </div>
                <div className="space-y-2">
                  {selectedTemplates.map((templateId) => {
                    const template = templates.find((t) => t.shift_template_id === templateId);
                    return template ? (
                      <div key={templateId} className="flex items-center gap-2 text-sm">
                        <span className="w-2 h-2 bg-blue-500 rounded-full" />
                        <span className="font-medium">{template.shift_template_name}</span>
                        <span className="text-gray-500">
                          ({template.start_time} - {template.end_time})
                        </span>
                      </div>
                    ) : null;
                  })}
                </div>
              </div>

              {/* Selected Days */}
              <div className="border-b pb-4">
                <div className="text-sm text-gray-500 mb-2">
                  Days of Week ({selectedDays.length})
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedDays
                    .sort((a, b) => a - b)
                    .map((dayId) => {
                      const day = DAYS_OF_WEEK.find((d) => d.id === dayId);
                      return day ? (
                        <span
                          key={dayId}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                        >
                          {day.name}
                        </span>
                      ) : null;
                    })}
                </div>
              </div>

              {/* Total Shifts */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-sm text-blue-800 font-medium mb-1">
                  Total Shifts to Create
                </div>
                <div className="text-3xl font-bold text-blue-900">
                  {selectedTemplates.length * selectedDays.length}
                </div>
                <div className="text-sm text-blue-700 mt-1">
                  {selectedTemplates.length} template(s) × {selectedDays.length} day(s)
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="secondary"
          onClick={() => (currentStep === 1 ? navigate("/schedules") : handleBack())}
          disabled={loading}
        >
          {currentStep === 1 ? "Cancel" : "Back"}
        </Button>

        {currentStep < 4 ? (
          <Button variant="primary" onClick={handleNext}>
            Next Step
          </Button>
        ) : (
          <Button variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Creating Schedule..." : "Create Schedule"}
          </Button>
        )}
      </div>
    </div>
  );
}
