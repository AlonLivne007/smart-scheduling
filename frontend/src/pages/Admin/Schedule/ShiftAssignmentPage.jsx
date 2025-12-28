// frontend/src/pages/Admin/Schedule/ShiftAssignmentPage.jsx
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { format, parseISO } from "date-fns";
import toast from "react-hot-toast";
import { ChevronLeft, Clock, MapPin, Calendar, Users, Plus, Trash2 } from "lucide-react";
import api from "../../../lib/axios";
import Button from "../../../components/ui/Button";
import Skeleton from "../../../components/ui/Skeleton";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";

export default function ShiftAssignmentPage() {
  const { scheduleId, shiftId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [shift, setShift] = useState(null);
  const [shiftTemplate, setShiftTemplate] = useState(null);
  const [shiftTemplateLoadFailed, setShiftTemplateLoadFailed] = useState(false);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [assignmentToDelete, setAssignmentToDelete] = useState(null);

  useEffect(() => {
    loadData();
  }, [shiftId]);

  async function loadData() {
    setLoading(true);
    setShiftTemplateLoadFailed(false);
    try {
      const parsedShiftId = parseInt(shiftId, 10);
      if (isNaN(parsedShiftId)) {
        toast.error("Invalid shift ID");
        navigate(`/schedules/${scheduleId}`);
        return;
      }

      // Load shift details, users, and roles in parallel
      const [shiftRes, usersRes, rolesRes] = await Promise.all([
        api.get(`/planned-shifts/${parsedShiftId}`),
        api.get("/users/"),
        api.get("/roles/"),
      ]);

      setShift(shiftRes.data);
      setUsers(usersRes.data || []);
      setRoles(rolesRes.data || []);

      // Load shift template to get requirements
      if (shiftRes.data?.shift_template_id) {
        try {
          const templateRes = await api.get(`/shift-templates/${shiftRes.data.shift_template_id}`);
          setShiftTemplate(templateRes.data);
        } catch (e) {
          console.error("Failed to load shift template:", e);
          setShiftTemplate(null);
          setShiftTemplateLoadFailed(true);
        }
      }
    } catch (e) {
      let msg = "Failed to load shift details";
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
      if (e?.response?.status === 404) {
        navigate(`/schedules/${scheduleId}`);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleAddAssignment() {
    // Validation
    if (!selectedUserId) {
      toast.error("Please select an employee");
      return;
    }
    if (!selectedRoleId) {
      toast.error("Please select a role");
      return;
    }

    // Check for duplicate employee
    const alreadyAssigned = shift?.assignments?.some(
      (a) => a.user_id === parseInt(selectedUserId, 10)
    );
    if (alreadyAssigned) {
      toast.error("This employee is already assigned to this shift");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        planned_shift_id: parseInt(shiftId, 10),
        user_id: parseInt(selectedUserId, 10),
        role_id: parseInt(selectedRoleId, 10),
      };

      await api.post("/shift-assignments/", payload);
      toast.success("Assignment created successfully");
      setShowAddForm(false);
      setSelectedUserId("");
      setSelectedRoleId("");
      loadData(); // Reload to get updated assignments
    } catch (e) {
      let msg = "Failed to create assignment";
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
      setSubmitting(false);
    }
  }

  async function handleDeleteAssignment(assignment) {
    try {
      await api.delete(`/shift-assignments/${assignment.assignment_id}`);
      toast.success("Assignment removed successfully");
      setAssignmentToDelete(null);
      loadData(); // Reload to get updated assignments
    } catch (e) {
      let msg = "Failed to delete assignment";
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
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton height={80} />
        <Skeleton height={200} />
        <Skeleton height={300} />
      </div>
    );
  }

  if (!shift) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 mb-4">Shift not found</p>
        <Button variant="primary" onClick={() => navigate(`/schedules/${scheduleId}`)}>
          Back to Schedule
        </Button>
      </div>
    );
  }

  const assignedEmployeeIds = shift.assignments?.map((a) => a.user_id) || [];
  const availableUsers = users.filter((u) => !assignedEmployeeIds.includes(u.user_id));

  // Filter roles based on selected employee
  const getAvailableRoles = () => {
    if (!selectedUserId) {
      return roles; // Show all roles if no employee selected
    }
    const selectedUser = users.find((u) => u.user_id === parseInt(selectedUserId, 10));
    if (!selectedUser || !selectedUser.roles || selectedUser.roles.length === 0) {
      return []; // No roles available for this employee
    }
    return selectedUser.roles;
  };

  // Filter employees based on selected role
  const getAvailableEmployees = () => {
    if (!selectedRoleId) {
      return availableUsers; // Show all available employees if no role selected
    }
    return availableUsers.filter((user) => 
      user.roles && user.roles.some((r) => r.role_id === parseInt(selectedRoleId, 10))
    );
  };

  const filteredRoles = getAvailableRoles();
  const filteredEmployees = getAvailableEmployees();

  // Reset role selection if it becomes invalid after employee change
  const handleEmployeeChange = (userId) => {
    setSelectedUserId(userId);
    if (userId) {
      const selectedUser = users.find((u) => u.user_id === parseInt(userId, 10));
      const userRoleIds = selectedUser?.roles?.map((r) => r.role_id) || [];
      // If current role is not in user's roles, reset it
      if (selectedRoleId && !userRoleIds.includes(parseInt(selectedRoleId, 10))) {
        setSelectedRoleId("");
      }
    }
  };

  // Reset employee selection if it becomes invalid after role change
  const handleRoleChange = (roleId) => {
    setSelectedRoleId(roleId);
    if (roleId) {
      const usersWithRole = availableUsers.filter((user) =>
        user.roles && user.roles.some((r) => r.role_id === parseInt(roleId, 10))
      );
      const userIds = usersWithRole.map((u) => u.user_id);
      // If current employee doesn't have this role, reset it
      if (selectedUserId && !userIds.includes(parseInt(selectedUserId, 10))) {
        setSelectedUserId("");
      }
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-semibold">Shift Assignment</h1>
          <Button
            variant="outline"
            onClick={() => navigate(`/schedules/${scheduleId}`)}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back to Schedule
          </Button>
        </div>

        {/* Shift Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div className="flex items-center gap-2 text-gray-700">
            <Calendar className="h-5 w-5 text-blue-600" />
            <span className="font-medium">
              {shift.date ? format(parseISO(shift.date), "EEEE, MMMM d, yyyy") : "N/A"}
            </span>
          </div>
          <div className="flex items-center gap-2 text-gray-700">
            <Clock className="h-5 w-5 text-blue-600" />
            <span className="font-medium">
              {shift.start_time ? format(new Date(shift.start_time), "HH:mm") : "N/A"} -{" "}
              {shift.end_time ? format(new Date(shift.end_time), "HH:mm") : "N/A"}
            </span>
          </div>
          {shift.location && (
            <div className="flex items-center gap-2 text-gray-700">
              <MapPin className="h-5 w-5 text-blue-600" />
              <span className="font-medium">{shift.location}</span>
            </div>
          )}
          <div className="flex items-center gap-2 text-gray-700">
            <Users className="h-5 w-5 text-blue-600" />
            <span className="font-medium">
              {shift.shift_template_name || "Unnamed Shift"}
            </span>
          </div>
        </div>
      </div>

      {/* Shift Requirements */}
      {shift?.shift_template_id && (
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Shift Requirements</h2>

          {shiftTemplateLoadFailed && (
            <p className="text-sm text-red-700">
              Unable to load requirements for this shift template.
            </p>
          )}

          {!shiftTemplateLoadFailed && (!shiftTemplate || !Array.isArray(shiftTemplate.required_roles)) && (
            <p className="text-sm text-gray-600">Loading requirements…</p>
          )}

          {!shiftTemplateLoadFailed &&
            shiftTemplate &&
            Array.isArray(shiftTemplate.required_roles) &&
            shiftTemplate.required_roles.length === 0 && (
              <p className="text-sm text-gray-600">No requirements configured for this shift.</p>
            )}

          {!shiftTemplateLoadFailed &&
            shiftTemplate &&
            Array.isArray(shiftTemplate.required_roles) &&
            shiftTemplate.required_roles.length > 0 && (
              <div className="space-y-3">
                {shiftTemplate.required_roles.map((req) => {
                  const assignedCount = shift.assignments?.filter(
                    (a) => a.role_id === req.role_id
                  ).length || 0;
                  const requiredCount = req.required_count || 0;
                  const isFilled = assignedCount >= requiredCount;
                  const percentage = requiredCount > 0 ? (assignedCount / requiredCount) * 100 : 0;

                  return (
                    <div key={req.role_id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-gray-900">{req.role_name}</div>
                        <div
                          className={`text-sm font-semibold ${
                            isFilled
                              ? "text-green-700"
                              : assignedCount > 0
                                ? "text-yellow-700"
                                : "text-red-700"
                          }`}
                        >
                          {assignedCount}/{requiredCount} assigned
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            isFilled
                              ? "bg-green-500"
                              : assignedCount > 0
                                ? "bg-yellow-500"
                                : "bg-red-500"
                          }`}
                          style={{ width: `${Math.min(percentage, 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
        </div>
      )}

      {/* Assignments List */}
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            Assigned Employees ({shift.assignments?.length || 0})
          </h2>
          <Button
            variant="primary"
            onClick={() => setShowAddForm(!showAddForm)}
            disabled={filteredEmployees.length === 0 && !selectedRoleId}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Assignment
          </Button>
        </div>

        {/* Add Assignment Form */}
        {showAddForm && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h3 className="font-semibold text-gray-900 mb-3">New Assignment</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employee
                  {selectedRoleId && (
                    <span className="text-xs text-gray-500 ml-1">
                      (filtered by role)
                    </span>
                  )}
                </label>
                <select
                  value={selectedUserId}
                  onChange={(e) => handleEmployeeChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select employee...</option>
                  {filteredEmployees.map((user) => (
                    <option key={user.user_id} value={user.user_id}>
                      {user.user_full_name}
                    </option>
                  ))}
                </select>
                {selectedRoleId && filteredEmployees.length === 0 && (
                  <p className="text-xs text-red-600 mt-1">
                    No employees available for this role
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                  {selectedUserId && (
                    <span className="text-xs text-gray-500 ml-1">
                      (filtered by employee)
                    </span>
                  )}
                </label>
                <select
                  value={selectedRoleId}
                  onChange={(e) => handleRoleChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select role...</option>
                  {filteredRoles.map((role) => (
                    <option key={role.role_id} value={role.role_id}>
                      {role.role_name}
                    </option>
                  ))}
                </select>
                {selectedUserId && filteredRoles.length === 0 && (
                  <p className="text-xs text-red-600 mt-1">
                    This employee has no roles assigned
                  </p>
                )}
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button
                variant="primary"
                onClick={handleAddAssignment}
                disabled={submitting}
              >
                {submitting ? "Adding..." : "Add Assignment"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowAddForm(false);
                  setSelectedUserId("");
                  setSelectedRoleId("");
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Assignments List */}
        {(!shift.assignments || shift.assignments.length === 0) ? (
          <div className="text-center py-8 text-gray-500">
            <Users className="h-12 w-12 mx-auto mb-2 text-gray-400" />
            <p>No employees assigned to this shift yet</p>
            {filteredEmployees.length > 0 && (
              <p className="text-sm mt-1">Click "Add Assignment" to assign employees</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {shift.assignments.map((assignment) => (
              <div
                key={assignment.assignment_id}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <Users className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">
                      {assignment.user_full_name}
                    </div>
                    <div className="text-sm text-gray-600">
                      {assignment.role_name || "No role specified"}
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setAssignmentToDelete(assignment)}
                  className="border-red-300 text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {assignmentToDelete && (
        <ConfirmDialog
          isOpen={!!assignmentToDelete}
          title="Remove Assignment"
          message={`Are you sure you want to remove ${assignmentToDelete.user_full_name} from this shift?`}
          confirmLabel="Remove"
          onConfirm={() => handleDeleteAssignment(assignmentToDelete)}
          onCancel={() => setAssignmentToDelete(null)}
        />
      )}
    </div>
  );
}
