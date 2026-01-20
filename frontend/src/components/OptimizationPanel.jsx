// frontend/src/components/OptimizationPanel.jsx
import React, { useState, useEffect } from 'react';
import { Zap, CheckCircle, XCircle, Clock, AlertCircle, Loader2, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import Button from './ui/Button';
import { 
  triggerOptimization, 
  getAllRuns, 
  getRun, 
  getSolutions, 
  applySolution,
  deleteRun 
} from '../api/optimization';

/**
 * OptimizationPanel Component
 * 
 * Displays optimization controls and results for a weekly schedule.
 * Allows managers to run optimization, view results, and apply solutions.
 * 
 * @param {Object} props
 * @param {number} props.weeklyScheduleId - ID of the weekly schedule
 * @param {Function} props.onSolutionApplied - Callback when solution is applied
 */
export default function OptimizationPanel({ weeklyScheduleId, onSolutionApplied }) {
  const [loading, setLoading] = useState(false);
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [solutions, setSolutions] = useState([]);
  const [applying, setApplying] = useState(false);
  const [polling, setPolling] = useState(false);

  // Load runs for this schedule
  useEffect(() => {
    if (weeklyScheduleId) {
      loadRuns();
    }
  }, [weeklyScheduleId]);

  // Poll for running optimizations
  useEffect(() => {
    if (runs.some(r => r.status === 'RUNNING' || r.status === 'PENDING')) {
      setPolling(true);
      const interval = setInterval(() => {
        loadRuns(true); // Silent reload
      }, 3000); // Poll every 3 seconds

      return () => {
        clearInterval(interval);
        setPolling(false);
      };
    }
  }, [runs]);

  async function loadRuns(silent = false) {
    if (!silent) setLoading(true);
    try {
      const data = await getAllRuns({ weekly_schedule_id: weeklyScheduleId });
      setRuns(data || []);
      
      // Auto-select the most recent completed run
      if (!selectedRun && data && data.length > 0) {
        const completed = data.find(r => r.status === 'COMPLETED');
        if (completed) {
          handleSelectRun(completed);
        }
      }
    } catch (error) {
      if (!silent) {
        console.error('Failed to load optimization runs:', error);
        toast.error('Failed to load optimization history');
      }
    } finally {
      if (!silent) setLoading(false);
    }
  }

  async function handleSelectRun(run) {
    setSelectedRun(run);
    if (run.status === 'COMPLETED') {
      try {
        const solutionsData = await getSolutions(run.run_id);
        setSolutions(solutionsData || []);
      } catch (error) {
        console.error('Failed to load solutions:', error);
        toast.error('Failed to load optimization results');
      }
    } else if (run.status === 'FAILED') {
      // Clear solutions for failed runs
      setSolutions([]);
    }
  }

  async function handleRunOptimization() {
    setLoading(true);
    try {
      const result = await triggerOptimization(weeklyScheduleId);
      toast.success('Optimization started!');
      await loadRuns();
      
      // Auto-select the new run
      if (result.run_id) {
        const newRun = await getRun(result.run_id);
        setSelectedRun(newRun);
      }
    } catch (error) {
      console.error('Failed to run optimization:', error);
      const msg = error?.response?.data?.detail || 'Failed to start optimization';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleApplySolution(overwrite = false) {
    if (!selectedRun) return;
    
    setApplying(true);
    try {
      const result = await applySolution(selectedRun.run_id, overwrite);
      toast.success(result.message || 'Solution applied successfully!');
      if (onSolutionApplied) {
        onSolutionApplied();
      }
    } catch (error) {
      console.error('Failed to apply solution:', error);
      const detail = error?.response?.data?.detail;
      
      // Check if it's a conflict error
      if (error?.response?.status === 409) {
        const shouldOverwrite = window.confirm(
          `${detail}\n\nDo you want to overwrite the existing assignments?`
        );
        if (shouldOverwrite) {
          handleApplySolution(true); // Retry with overwrite
        }
      } else {
        toast.error(detail || 'Failed to apply solution');
      }
    } finally {
      setApplying(false);
    }
  }

  async function handleDeleteRun(runId) {
    if (!window.confirm('Are you sure you want to delete this optimization run?')) {
      return;
    }
    
    try {
      await deleteRun(runId);
      toast.success('Optimization run deleted');
      if (selectedRun?.run_id === runId) {
        setSelectedRun(null);
        setSolutions([]);
      }
      await loadRuns();
    } catch (error) {
      console.error('Failed to delete run:', error);
      toast.error('Failed to delete optimization run');
    }
  }

  function getStatusIcon(status) {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'RUNNING':
      case 'PENDING':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'FAILED':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'CANCELLED':
        return <AlertCircle className="w-5 h-5 text-gray-600" />;
      default:
        return <Clock className="w-5 h-5 text-gray-600" />;
    }
  }

  function getStatusColor(status) {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'RUNNING':
      case 'PENDING':
        return 'bg-blue-100 text-blue-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Zap className="w-6 h-6 text-purple-600 mr-2" />
          <h3 className="text-xl font-semibold text-gray-900">Schedule Optimization</h3>
        </div>
        <Button
          onClick={handleRunOptimization}
          disabled={loading || polling}
          variant="primary"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 mr-2" />
              Run Optimization
            </>
          )}
        </Button>
      </div>

      {/* Optimization History */}
      {runs.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Optimization History</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {runs.map((run) => (
              <div
                key={run.run_id}
                onClick={() => handleSelectRun(run)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedRun?.run_id === run.run_id
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(run.status)}
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">
                          Run #{run.run_id}
                        </span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(run.status)}`}>
                          {run.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {run.started_at && new Date(run.started_at).toLocaleString()}
                        {run.runtime_seconds && ` • ${run.runtime_seconds.toFixed(2)}s`}
                        {run.status === 'FAILED' && run.solver_status && (
                          <span className="ml-2 text-red-600 font-medium">
                            • {run.solver_status}
                          </span>
                        )}
                        {run.status === 'COMPLETED' && run.solution_count > 0 && ` • ${run.solution_count} assignments`}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteRun(run.run_id);
                    }}
                    className="text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete run"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results Preview - Completed with solutions */}
      {selectedRun && selectedRun.status === 'COMPLETED' && solutions.length > 0 && (
        <div className="border-t pt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Optimization Results</h4>

          {(() => {
            const uniqueEmployees = new Set(solutions.map(s => s.user_id)).size;
            const avgPreferenceScore = solutions.length > 0 
              ? (solutions.reduce((sum, s) => sum + (s.assignment_score || 0), 0) / solutions.length).toFixed(2)
              : '0.00';
            
            // Extract metrics from run if available
            const metrics = selectedRun.metrics || {};
            const coveragePct = metrics.shifts_total > 0 
              ? ((metrics.shifts_filled || 0) / metrics.shifts_total * 100).toFixed(1)
              : '0.0';
            const employeeUtilization = metrics.employees_total > 0
              ? ((metrics.employees_assigned || 0) / metrics.employees_total * 100).toFixed(1)
              : '0.0';
            
            return (
              <div className="space-y-4">
                {/* Primary Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-sm text-blue-600 font-medium">Total Assignments</div>
                    <div className="text-2xl font-bold text-blue-900">{solutions.length}</div>
                    {selectedRun.total_assignments && selectedRun.total_assignments !== solutions.length && (
                      <div className="text-xs text-blue-700 mt-1">DB: {selectedRun.total_assignments}</div>
                    )}
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-sm text-green-600 font-medium">Employees Assigned</div>
                    <div className="text-2xl font-bold text-green-900">{uniqueEmployees}</div>
                    {metrics.employees_total && (
                      <div className="text-xs text-green-700 mt-1">
                        {employeeUtilization}% of {metrics.employees_total} total
                      </div>
                    )}
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="text-sm text-purple-600 font-medium">Avg Preference Score</div>
                    <div className="text-2xl font-bold text-purple-900">{avgPreferenceScore}</div>
                    {metrics.avg_preference_score && (
                      <div className="text-xs text-purple-700 mt-1">
                        From metrics: {metrics.avg_preference_score.toFixed(2)}
                      </div>
                    )}
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4">
                    <div className="text-sm text-orange-600 font-medium">Solver Status</div>
                    <div className="text-2xl font-bold text-orange-900">
                      {selectedRun.solver_status || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Coverage & Fairness Metrics */}
                {(metrics.shifts_total || metrics.min_assignments !== undefined) && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {metrics.shifts_total && (
                      <>
                        <div className="bg-emerald-50 rounded-lg p-4">
                          <div className="text-sm text-emerald-600 font-medium">Coverage</div>
                          <div className="text-xl font-bold text-emerald-900">
                            {coveragePct}%
                          </div>
                          <div className="text-xs text-emerald-700 mt-1">
                            {metrics.shifts_filled || 0} / {metrics.shifts_total} shifts
                          </div>
                        </div>
                        <div className="bg-rose-50 rounded-lg p-4">
                          <div className="text-sm text-rose-600 font-medium">Fairness (Min)</div>
                          <div className="text-xl font-bold text-rose-900">
                            {metrics.min_assignments || 0}
                          </div>
                          <div className="text-xs text-rose-700 mt-1">assignments per employee</div>
                        </div>
                        <div className="bg-amber-50 rounded-lg p-4">
                          <div className="text-sm text-amber-600 font-medium">Fairness (Max)</div>
                          <div className="text-xl font-bold text-amber-900">
                            {metrics.max_assignments || 0}
                          </div>
                          <div className="text-xs text-amber-700 mt-1">assignments per employee</div>
                        </div>
                        <div className="bg-violet-50 rounded-lg p-4">
                          <div className="text-sm text-violet-600 font-medium">Fairness (Avg)</div>
                          <div className="text-xl font-bold text-violet-900">
                            {metrics.avg_assignments ? metrics.avg_assignments.toFixed(1) : '0.0'}
                          </div>
                          <div className="text-xs text-violet-700 mt-1">assignments per employee</div>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Secondary Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 font-medium">Runtime</div>
                    <div className="text-xl font-bold text-gray-900">
                      {selectedRun.runtime_seconds?.toFixed(2) || '0'}s
                    </div>
                  </div>
                  {selectedRun.objective_value !== null && selectedRun.objective_value !== undefined && (
                    <div className="bg-indigo-50 rounded-lg p-4">
                      <div className="text-sm text-indigo-600 font-medium">Objective Value</div>
                      <div className="text-xl font-bold text-indigo-900">
                        {selectedRun.objective_value.toFixed(2)}
                      </div>
                    </div>
                  )}
                  {selectedRun.mip_gap !== null && selectedRun.mip_gap !== undefined && (
                    <div className="bg-teal-50 rounded-lg p-4">
                      <div className="text-sm text-teal-600 font-medium">MIP Gap</div>
                      <div className="text-xl font-bold text-teal-900">
                        {(selectedRun.mip_gap * 100).toFixed(2)}%
                      </div>
                    </div>
                  )}
                  <div className="bg-cyan-50 rounded-lg p-4">
                    <div className="text-sm text-cyan-600 font-medium">Solution Quality</div>
                    <div className="text-xl font-bold text-cyan-900">
                      {selectedRun.solver_status === 'OPTIMAL' ? 'Optimal' : 
                       selectedRun.solver_status === 'FEASIBLE' ? 'Feasible' : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          <Button
            onClick={() => handleApplySolution(false)}
            disabled={applying}
            variant="success"
            className="w-full"
          >
            {applying ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Applying Solution...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Apply Solution to Schedule
              </>
            )}
          </Button>
        </div>
      )}

      {/* Failed/Infeasible Results */}
      {selectedRun && selectedRun.status === 'FAILED' && (
        <div className="border-t pt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Optimization Failed</h4>
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex items-start">
              <XCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-sm font-semibold text-red-900">Solver Status:</span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    selectedRun.solver_status === 'INFEASIBLE'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-orange-100 text-orange-800'
                  }`}>
                    {selectedRun.solver_status || 'ERROR'}
                  </span>
                </div>
                {selectedRun.error_message && (
                  <p className="text-sm text-red-800 mt-2">
                    {selectedRun.error_message}
                  </p>
                )}
                {selectedRun.runtime_seconds && (
                  <p className="text-xs text-red-700 mt-2">
                    Runtime: {selectedRun.runtime_seconds.toFixed(2)}s
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h5 className="text-sm font-semibold text-yellow-900 mb-1">What to do next:</h5>
                <ul className="text-sm text-yellow-800 list-disc list-inside space-y-1">
                  <li>Review your system constraints (max hours, max shifts, min rest hours)</li>
                  <li>Check if you have enough employees with the required roles</li>
                  <li>Verify employee availability matches shift requirements</li>
                  <li>Consider reducing the number of required shifts or roles</li>
                  <li>Try adjusting constraint values to be less restrictive</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {runs.length === 0 && !loading && (
        <div className="text-center py-8">
          <Zap className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 mb-4">No optimization runs yet</p>
          <p className="text-sm text-gray-500">
            Click "Run Optimization" to automatically assign employees to shifts
          </p>
        </div>
      )}
    </div>
  );
}
