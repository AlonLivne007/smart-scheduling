// frontend/src/pages/Admin/Schedule/ScheduleCalendarPage.jsx
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { format, addDays, parseISO } from "date-fns";
import toast from "react-hot-toast";
import { ChevronLeft, ChevronRight, Users, Clock, MapPin, Edit2, Trash2 } from "lucide-react";
import api from "../../../lib/axios";
import Button from "../../../components/ui/Button";
import Skeleton from "../../../components/ui/Skeleton";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";
import OptimizationPanel from "../../../components/OptimizationPanel";

export default function ScheduleCalendarPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [schedule, setSchedule] = useState(null);
  const [plannedShifts, setPlannedShifts] = useState([]);
  const [shiftTemplates, setShiftTemplates] = useState([]);
  const [shiftToDelete, setShiftToDelete] = useState(null);

  const DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  useEffect(() => {
    if (id) {
      loadSchedule();
    }
  }, [id]);

  async function loadSchedule() {
    setLoading(true);
    try {
      // Parse ID as integer - route params are strings
      const scheduleId = parseInt(id, 10);
      if (isNaN(scheduleId)) {
        toast.error("Invalid schedule ID");
        navigate("/schedules");
        return;
      }

      const { data } = await api.get(`/weekly-schedules/${scheduleId}`);
      setSchedule(data);
      setPlannedShifts(data.planned_shifts || []);

      // Load shift templates to get requirements for coverage calculation
      try {
        const templatesRes = await api.get("/shift-templates/");
        setShiftTemplates(templatesRes.data || []);
      } catch (e) {
        console.error("Failed to load shift templates:", e);
        setShiftTemplates([]);
      }
    } catch (e) {
      let msg = "Failed to load schedule";
      if (e?.response?.data?.detail) {
        const detail = e.response.data.detail;
        // Handle validation error array
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
        navigate("/schedules");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteShift(shift) {
    try {
      await api.delete(`/planned-shifts/${shift.planned_shift_id}`);
      toast.success("Shift deleted successfully");
      setShiftToDelete(null);
      loadSchedule(); // Reload to refresh
    } catch (e) {
      let msg = "Failed to delete shift";
      if (e?.response?.data?.detail) {
        const detail = e.response.data.detail;
        // Handle validation error array
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

  function getShiftsForDay(dayIndex) {
    if (!schedule) return [];

    const weekStartDate = parseISO(schedule.week_start_date);
    const targetDate = format(addDays(weekStartDate, dayIndex), "yyyy-MM-dd");

    const shifts = plannedShifts.filter((shift) => shift.date === targetDate);

    const templates = Array.isArray(shiftTemplates) ? shiftTemplates : [];

    // Ensure a stable, chronological ordering within the day.
    return shifts.sort((a, b) => {
      const aStart = a?.start_time ? new Date(a.start_time).getTime() : NaN;
      const bStart = b?.start_time ? new Date(b.start_time).getTime() : NaN;

      if (Number.isFinite(aStart) && Number.isFinite(bStart)) {
        return aStart - bStart;
      }

      // Fallback: use template start_time (time-only) if start_time is missing/invalid.
      const aTplStart = templates.find(
        (t) => Number(t.shift_template_id) === Number(a?.shift_template_id)
      )?.start_time;
      const bTplStart = templates.find(
        (t) => Number(t.shift_template_id) === Number(b?.shift_template_id)
      )?.start_time;

      // Compare as strings in HH:mm:ss format (works lexicographically).
      if (aTplStart && bTplStart) return String(aTplStart).localeCompare(String(bTplStart));
      if (aTplStart) return -1;
      if (bTplStart) return 1;

      // Final fallback: keep deterministic order by id.
      return Number(a?.planned_shift_id || 0) - Number(b?.planned_shift_id || 0);
    });
  }

  function getShiftStatus(shift) {
    const assignments = shift.assignments || [];
    const assignedCount = assignments.length;

    const templates = Array.isArray(shiftTemplates) ? shiftTemplates : [];
    const template = templates.find(
      (t) => Number(t.shift_template_id) === Number(shift.shift_template_id)
    );

    // If we can't load the template, fall back to the simple behavior.
    if (!template || !Array.isArray(template.required_roles)) {
      if (assignedCount === 0) {
        return { status: "empty", color: "red", percentage: 0 };
      }
      return { status: "partial", color: "yellow", percentage: 50 };
    }

    const requiredRoles = template.required_roles || [];
    const totalRequired = requiredRoles.reduce(
      (sum, rr) => sum + (Number(rr.required_count) || 0),
      0
    );

    if (totalRequired === 0) {
      return { status: "no_requirements", color: "gray", percentage: 0 };
    }

    const assignedByRole = assignments.reduce((acc, a) => {
      const roleId = a?.role_id;
      if (roleId === null || roleId === undefined) return acc;
      const key = String(roleId);
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    const totalCovered = requiredRoles.reduce((sum, rr) => {
      const roleIdKey = String(rr.role_id);
      const requiredCount = Number(rr.required_count) || 0;
      const assignedForRole = assignedByRole[roleIdKey] || 0;
      return sum + Math.min(assignedForRole, requiredCount);
    }, 0);

    const percentage = Math.round((totalCovered / totalRequired) * 100);

    if (totalCovered === 0) {
      return { status: "empty", color: "red", percentage: 0 };
    }
    if (totalCovered < totalRequired) {
      return { status: "partial", color: "yellow", percentage };
    }
    return { status: "full", color: "green", percentage: 100 };
  }

  function ShiftCard({ shift }) {
    const status = getShiftStatus(shift);
    const assigned = shift.assignments?.length || 0;

    const templateName =
      shift.shift_template_name ||
      (Array.isArray(shiftTemplates)
        ? shiftTemplates.find(
            (t) => Number(t.shift_template_id) === Number(shift.shift_template_id)
          )?.shift_template_name
        : null);

    const colorClasses = {
      green: "border-green-500 bg-green-50 hover:bg-green-100",
      yellow: "border-yellow-500 bg-yellow-50 hover:bg-yellow-100",
      red: "border-red-500 bg-red-50 hover:bg-red-100",
      gray: "border-gray-300 bg-gray-50 hover:bg-gray-100",
    };

    const statusTextColors = {
      green: "text-green-700",
      yellow: "text-yellow-700",
      red: "text-red-700",
      gray: "text-gray-700",
    };

    return (
      <div
        className={`border-l-4 rounded-lg p-3 mb-2 cursor-pointer transition-colors ${
          colorClasses[status.color]
        }`}
        onClick={() => navigate(`/schedules/${id}/shifts/${shift.planned_shift_id}`)}
      >
        <div className="flex justify-between items-start mb-2">
          <div className="font-semibold text-gray-900">
            {templateName || "Unnamed Shift"}
          </div>
          <div className="flex gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/schedules/${id}/shifts/${shift.shift_id}/edit`);
              }}
              className="p-1 hover:bg-white rounded transition-colors"
              title="Edit shift"
            >
              <Edit2 className="h-4 w-4 text-gray-600" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShiftToDelete(shift);
              }}
              className="p-1 hover:bg-white rounded transition-colors"
              title="Delete shift"
            >
              <Trash2 className="h-4 w-4 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="space-y-1 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>
              {shift.start_time ? format(new Date(shift.start_time), "HH:mm") : "N/A"} - {shift.end_time ? format(new Date(shift.end_time), "HH:mm") : "N/A"}
            </span>
          </div>
          {shift.location && (
            <div className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              <span>{shift.location}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Users className="h-3 w-3" />
            <span className={`font-medium ${statusTextColors[status.color]}`}>
              {assigned} assigned
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton height={80} />
        <div className="grid grid-cols-7 gap-4">
          {[...Array(7)].map((_, i) => (
            <Skeleton key={i} height={400} />
          ))}
        </div>
      </div>
    );
  }

  if (!schedule) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 mb-4">Schedule not found</p>
        <Button variant="primary" onClick={() => navigate("/schedules")}>
          Back to Schedules
        </Button>
      </div>
    );
  }

  const weekStartDate = parseISO(schedule.week_start_date);
  const weekEndDate = addDays(weekStartDate, 6);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Weekly Schedule</h1>
            <p className="text-gray-600 mt-1">
              {format(weekStartDate, "MMMM d")} - {format(weekEndDate, "MMMM d, yyyy")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => navigate("/schedules")}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back to List
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate("/schedules/create")}
            >
              Create New Schedule
            </Button>
          </div>
        </div>
      </div>

      {/* Optimization Panel */}
      <OptimizationPanel 
        weeklyScheduleId={parseInt(id, 10)} 
        onSolutionApplied={loadSchedule}
      />

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-4">
        {DAYS_OF_WEEK.map((dayName, dayIndex) => {
          const dayDate = addDays(weekStartDate, dayIndex);
          const shiftsForDay = getShiftsForDay(dayIndex);

          return (
            <div key={dayIndex} className="bg-white rounded-xl shadow overflow-hidden">
              {/* Day Header */}
              <div className="bg-blue-600 text-white p-3">
                <div className="font-semibold">{dayName}</div>
                <div className="text-sm opacity-90">{format(dayDate, "MMM d")}</div>
              </div>

              {/* Shifts for this day */}
              <div className="p-3 min-h-[300px]">
                {shiftsForDay.length === 0 ? (
                  <div className="text-center text-gray-400 text-sm mt-8">
                    No shifts scheduled
                  </div>
                ) : (
                  shiftsForDay.map((shift) => (
                    <ShiftCard key={shift.planned_shift_id} shift={shift} />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Delete Confirmation Dialog */}
      {shiftToDelete && (
        <ConfirmDialog
          isOpen={!!shiftToDelete}
          title="Delete Shift"
          message={`Are you sure you want to delete this shift? ${
            shiftToDelete.assignments?.length > 0
              ? `This will also remove ${shiftToDelete.assignments.length} assignment(s).`
              : ""
          }`}
          confirmLabel="Delete"
          onConfirm={() => handleDeleteShift(shiftToDelete)}
          onCancel={() => setShiftToDelete(null)}
        />
      )}
    </div>
  );
}
