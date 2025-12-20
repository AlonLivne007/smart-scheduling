// frontend/src/pages/Admin/Employees/EmployeeProfilePage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { format } from "date-fns";
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

  useEffect(() => {
    let canceled = false;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get(`/shift-assignments/by-user/${employeeId}`);
        if (!canceled) setAssignments(data || []);
      } catch (e) {
        if (!canceled) {
          const msg = e?.response?.data?.detail || e.message || "Failed to load shifts";
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
                  {assignment.planned_shift?.shift_date
                    ? format(new Date(assignment.planned_shift.shift_date), "EEE, MMM dd")
                    : "N/A"}
                </td>
                <td className="px-4 py-3 text-sm">
                  {assignment.planned_shift?.template?.template_name || "N/A"}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {assignment.planned_shift?.template?.start_time || "N/A"} -{" "}
                  {assignment.planned_shift?.template?.end_time || "N/A"}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      assignment.assignment_status === "CONFIRMED"
                        ? "bg-green-100 text-green-800"
                        : assignment.assignment_status === "PENDING"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {assignment.assignment_status || "N/A"}
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

  const pending = requests.filter((r) => r.request_status === "PENDING");
  const approved = requests.filter((r) => r.request_status === "APPROVED");
  const rejected = requests.filter((r) => r.request_status === "REJECTED");

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
      {requests.map((request) => (
        <div
          key={request.request_id}
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
                  request.request_status === "APPROVED"
                    ? "bg-green-100 text-green-800"
                    : request.request_status === "PENDING"
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {request.request_status}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Type: {request.request_type}
              {request.approver_name && (
                <span className="ml-4">Reviewed by: {request.approver_name}</span>
              )}
            </p>
          </div>
        </div>
      ))}
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
