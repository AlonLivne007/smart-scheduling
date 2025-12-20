// frontend/src/pages/Admin/Schedule/ScheduleListPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";
import toast from "react-hot-toast";
import api from "../../../lib/axios";
import Button from "../../../components/ui/Button";
import Skeleton from "../../../components/ui/Skeleton";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";

export default function ScheduleListPage() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [schedules, setSchedules] = useState([]);
  const [sortBy, setSortBy] = useState("date"); // 'date' or 'coverage'
  const [sortOrder, setSortOrder] = useState("desc"); // 'asc' or 'desc'
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadSchedules();
  }, []);

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

  async function loadSchedules() {
    setLoading(true);
    try {
      const { data } = await api.get("/weekly-schedules/");
      setSchedules(data || []);
    } catch (e) {
      toast.error(extractErrorMessage(e, "Failed to load schedules"));
    } finally {
      setLoading(false);
    }
  }

  function handleSort(field) {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  }

  const sortedSchedules = [...schedules].sort((a, b) => {
    let comparison = 0;

    if (sortBy === "date") {
      const dateA = new Date(a.week_start_date);
      const dateB = new Date(b.week_start_date);
      comparison = dateA - dateB;
    } else if (sortBy === "shifts") {
      comparison = (a.planned_shifts?.length || 0) - (b.planned_shifts?.length || 0);
    } else if (sortBy === "coverage") {
      const coverageA = calculateCoverage(a);
      const coverageB = calculateCoverage(b);
      comparison = coverageA - coverageB;
    }

    return sortOrder === "asc" ? comparison : -comparison;
  });

  function calculateCoverage(schedule) {
    if (!schedule.planned_shifts || schedule.planned_shifts.length === 0) {
      return 0;
    }

    let totalRequired = 0;
    let totalAssigned = 0;

    schedule.planned_shifts.forEach((shift) => {
      const required = shift.required_count || 1;
      const assigned = shift.assignments?.length || 0;
      totalRequired += required;
      totalAssigned += assigned;
    });

    return totalRequired > 0 ? Math.round((totalAssigned / totalRequired) * 100) : 0;
  }

  async function handleDelete(schedule) {
    setDeleting(true);
    try {
      await api.delete(`/weekly-schedules/${schedule.weekly_schedule_id}`);
      toast.success("Schedule deleted successfully");
      setDeleteTarget(null);
      loadSchedules();
    } catch (e) {
      toast.error(extractErrorMessage(e, "Failed to delete schedule"));
    } finally {
      setDeleting(false);
    }
  }

  const SortIcon = ({ field }) => {
    if (sortBy !== field) {
      return <span className="ml-1 text-gray-400">↕</span>;
    }
    return <span className="ml-1">{sortOrder === "asc" ? "↑" : "↓"}</span>;
  };

  return (
    <div className="max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Weekly Schedules</h1>
          <p className="text-gray-600 mt-1">Manage and create weekly shift schedules</p>
        </div>
        <Button variant="primary" onClick={() => navigate("/schedules/create")}>
          + Create New Schedule
        </Button>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow p-6 space-y-3">
          <Skeleton height={50} />
          <Skeleton height={50} />
          <Skeleton height={50} />
        </div>
      ) : schedules.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg
            className="mx-auto h-16 w-16 text-gray-400 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Schedules Yet</h3>
          <p className="text-gray-600 mb-6">
            Get started by creating your first weekly schedule
          </p>
          <Button variant="primary" onClick={() => navigate("/schedules/create")}>
            Create Your First Schedule
          </Button>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 text-gray-700 border-b border-gray-200">
                  <tr>
                    <th
                      className="px-4 py-3 cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort("date")}
                    >
                      <div className="flex items-center font-semibold">
                        Week Starting <SortIcon field="date" />
                      </div>
                    </th>
                    <th className="px-4 py-3 font-semibold">Created By</th>
                    <th
                      className="px-4 py-3 cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort("shifts")}
                    >
                      <div className="flex items-center font-semibold">
                        Shifts <SortIcon field="shifts" />
                      </div>
                    </th>
                    <th
                      className="px-4 py-3 cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort("coverage")}
                    >
                      <div className="flex items-center font-semibold">
                        Coverage <SortIcon field="coverage" />
                      </div>
                    </th>
                    <th className="px-4 py-3 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {sortedSchedules.map((schedule) => {
                    const coverage = calculateCoverage(schedule);
                    const shiftsCount = schedule.planned_shifts?.length || 0;

                    return (
                      <tr
                        key={schedule.weekly_schedule_id}
                        className="hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => navigate(`/schedules/${schedule.weekly_schedule_id}`)}
                      >
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900">
                            {format(new Date(schedule.week_start_date), "MMM dd, yyyy")}
                          </div>
                          <div className="text-xs text-gray-500">
                            Week of {format(new Date(schedule.week_start_date), "MMMM d")}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {schedule.creator?.user_full_name || "Unknown"}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-gray-900 font-medium">{shiftsCount}</span>
                          <span className="text-gray-500 text-xs ml-1">shifts</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-24">
                              <div
                                className={`h-2 rounded-full ${
                                  coverage >= 80
                                    ? "bg-green-500"
                                    : coverage >= 50
                                    ? "bg-yellow-500"
                                    : "bg-red-500"
                                }`}
                                style={{ width: `${coverage}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium text-gray-700 min-w-12">
                              {coverage}%
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div
                            className="flex justify-end gap-2"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => navigate(`/schedules/${schedule.weekly_schedule_id}`)}
                              title="View schedule"
                            >
                              View
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setDeleteTarget(schedule)}
                              className="border-red-300 text-red-700 hover:bg-red-50"
                              title="Delete schedule"
                            >
                              Delete
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Summary */}
          <div className="mt-4 text-sm text-gray-600">
            Showing {schedules.length} schedule{schedules.length !== 1 ? "s" : ""}
          </div>
        </>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <ConfirmDialog
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => handleDelete(deleteTarget)}
          title="Delete Schedule"
          message={`Are you sure you want to delete the schedule for week starting ${format(
            new Date(deleteTarget.week_start_date),
            "MMM dd, yyyy"
          )}?`}
          confirmText="Delete Schedule"
          variant="danger"
          isLoading={deleting}
          sideEffects={
            deleteTarget.planned_shifts?.length > 0
              ? [
                  `This will also delete ${deleteTarget.planned_shifts.length} planned shift${
                    deleteTarget.planned_shifts.length !== 1 ? "s" : ""
                  } and all associated assignments.`,
                ]
              : []
          }
        />
      )}
    </div>
  );
}
