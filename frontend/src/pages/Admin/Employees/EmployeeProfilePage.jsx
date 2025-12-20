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
        {activeTab === "preferences" && <PreferencesTab />}
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

// Preferences Tab - Placeholder for future implementation
function PreferencesTab() {
  return (
    <div className="text-center py-12">
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
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Preferences Coming Soon</h3>
      <p className="text-gray-600 max-w-md mx-auto">
        Employee preferences and availability management will be available once the backend
        preferences system is implemented.
      </p>
    </div>
  );
}
