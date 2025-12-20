/**
 * Settings Page Component
 * 
 * The application settings page for configuring company-level preferences and system integrations.
 * This is a placeholder page that will be expanded with comprehensive settings functionality.
 * 
 * Planned Features:
 * - Company information and branding
 * - User management and permissions
 * - Notification preferences
 * - Integration settings (calendar, email, SMS)
 * - System configuration options
 * - Data export and backup settings
 * - Security and privacy settings
 * 
 * @component
 * @returns {JSX.Element} The settings configuration page
 */
import React, { useEffect, useMemo, useState } from 'react';
import Button from '../components/ui/Button.jsx';
import PageLayout from '../layouts/PageLayout.jsx';
import PageHeader from '../components/ui/PageHeader.jsx';
import { showSuccess, showError, showInfo, showWarning, showLoading, dismissToast } from '../lib/notifications.jsx';
import { Building2, Users, Bell, Shield, Database, Mail } from 'lucide-react';
import Skeleton from '../components/ui/Skeleton.jsx';
import api from '../lib/axios.js';

export default function Settings() {
  const handleTestSuccess = () => showSuccess('Settings saved successfully!');
  const handleTestError = () => showError('Failed to save settings. Please try again.');
  const handleTestInfo = () => showInfo('This is an informational message.');
  const handleTestWarning = () => showWarning('This action cannot be undone.');

  const authUser = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('auth_user') || 'null');
    } catch {
      return null;
    }
  }, []);

  const [assignedLoading, setAssignedLoading] = useState(false);
  const [assignedError, setAssignedError] = useState(null);
  const [assignedShifts, setAssignedShifts] = useState([]);

  const [timeOffLoading, setTimeOffLoading] = useState(false);
  const [timeOffError, setTimeOffError] = useState(null);
  const [timeOffRequests, setTimeOffRequests] = useState([]);
  
  const handleTestLoading = () => {
    const toastId = showLoading('Processing your request...');
    setTimeout(() => {
      dismissToast(toastId);
      showSuccess('Request completed!');
    }, 2000);
  };

  useEffect(() => {
    let canceled = false;

    async function loadMyAssignedShifts() {
      const userId = authUser?.user_id;
      if (!userId) {
        setAssignedShifts([]);
        return;
      }

      setAssignedLoading(true);
      setAssignedError(null);

      try {
        const { data } = await api.get(`/shift-assignments/by-user/${userId}`);
        const baseAssignments = Array.isArray(data) ? data : [];

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

        const enriched = baseAssignments
          .map((a) => ({
            ...a,
            planned_shift: plannedShiftById[Number(a.planned_shift_id)] || null,
          }))
          .sort((a, b) => {
            const ad = a?.planned_shift?.start_time || a?.planned_shift?.date || '';
            const bd = b?.planned_shift?.start_time || b?.planned_shift?.date || '';
            return String(ad).localeCompare(String(bd));
          });

        if (!canceled) setAssignedShifts(enriched);
      } catch (e) {
        const msg =
          e?.response?.data?.detail ||
          e?.message ||
          'Failed to load your assigned shifts.';
        if (!canceled) setAssignedError(msg);
      } finally {
        if (!canceled) setAssignedLoading(false);
      }
    }

    loadMyAssignedShifts();
    return () => {
      canceled = true;
    };
  }, [authUser]);

  useEffect(() => {
    let canceled = false;

    async function loadMyTimeOff() {
      const userId = authUser?.user_id;
      if (!userId) {
        setTimeOffRequests([]);
        return;
      }

      setTimeOffLoading(true);
      setTimeOffError(null);

      try {
        // Always scope to current user. Managers would otherwise receive all requests.
        const { data } = await api.get('/time-off/requests/', { params: { user_id: userId } });
        const list = Array.isArray(data) ? data : [];
        if (!canceled) setTimeOffRequests(list);
      } catch (e) {
        const msg =
          e?.response?.data?.detail ||
          e?.message ||
          'Failed to load your time-off requests.';
        if (!canceled) setTimeOffError(msg);
      } finally {
        if (!canceled) setTimeOffLoading(false);
      }
    }

    loadMyTimeOff();
    return () => {
      canceled = true;
    };
  }, [authUser]);

  return (
    <PageLayout>
      <PageHeader 
        title="Settings" 
        subtitle="Configure company-level preferences and integrations." 
      />
      
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* My Profile */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">My Profile</h3>
            {authUser ? (
              <div className="space-y-2">
                <div>
                  <div className="text-sm text-gray-500">Name</div>
                  <div className="text-gray-900 font-medium">{authUser.user_full_name || '—'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Email</div>
                  <div className="text-gray-900 font-medium">{authUser.user_email || '—'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Role</div>
                  <div className="text-gray-900 font-medium">{authUser.is_manager ? 'Manager' : 'Employee'}</div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-600">Not signed in.</p>
            )}
          </div>

          {/* My Assigned Shifts */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">My Assigned Shifts</h3>

            {assignedLoading ? (
              <Skeleton className="h-40" />
            ) : assignedError ? (
              <div className="text-sm text-red-600">{assignedError}</div>
            ) : assignedShifts.length === 0 ? (
              <p className="text-sm text-gray-600">No shift assignments found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Date</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Shift</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Time</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Location</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {assignedShifts.map((assignment) => {
                      const ps = assignment.planned_shift;
                      const dateLabel = ps?.date ? String(ps.date) : 'N/A';
                      const startLabel = ps?.start_time
                        ? new Date(ps.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : 'N/A';
                      const endLabel = ps?.end_time
                        ? new Date(ps.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : 'N/A';

                      return (
                        <tr key={assignment.assignment_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm">{dateLabel}</td>
                          <td className="px-4 py-3 text-sm">
                            {ps?.shift_template_name || 'N/A'}
                            {assignment.role_name ? (
                              <div className="text-xs text-gray-500">Role: {assignment.role_name}</div>
                            ) : null}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {startLabel} - {endLabel}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{ps?.location || '—'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* My Time-Off Requests */}
          <div className="bg-white rounded-2xl shadow-lg p-6 lg:col-span-2">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">My Time-Off Requests</h3>

            {timeOffLoading ? (
              <Skeleton className="h-40" />
            ) : timeOffError ? (
              <div className="text-sm text-red-600">{timeOffError}</div>
            ) : timeOffRequests.length === 0 ? (
              <p className="text-sm text-gray-600">No time-off requests found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Type</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Start</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">End</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {timeOffRequests.map((r) => {
                      const requestKey = r.request_id ?? r.time_off_request_id ?? `${r.user_id}-${r.start_date}-${r.end_date}`;
                      const startLabel = r.start_date
                        ? new Date(r.start_date).toLocaleDateString()
                        : 'N/A';
                      const endLabel = r.end_date
                        ? new Date(r.end_date).toLocaleDateString()
                        : 'N/A';

                      return (
                        <tr key={requestKey} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900">{r.request_type || 'N/A'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{startLabel}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{endLabel}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{r.status || 'N/A'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Notification Testing - Demo Section */}
          <div className="lg:col-span-2 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl shadow-lg p-6 border border-blue-200">
            <h3 className="text-xl font-semibold text-gray-900 mb-2 flex items-center">
              <Bell className="w-5 h-5 mr-2 text-blue-600" />
              Toast Notifications Demo
            </h3>
            <p className="text-sm text-gray-600 mb-4">Click buttons below to test different notification types:</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <Button variant="primarySolid" onClick={handleTestSuccess} size="small">✓ Success</Button>
              <Button variant="danger" onClick={handleTestError} size="small">✗ Error</Button>
              <Button variant="primary" onClick={handleTestInfo} size="small">ℹ Info</Button>
              <Button variant="secondarySolid" onClick={handleTestWarning} size="small">⚠ Warning</Button>
              <Button variant="success" onClick={handleTestLoading} size="small">⏳ Loading</Button>
            </div>
          </div>

          {/* Company Settings */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Building2 className="w-5 h-5 mr-2 text-blue-600" />
              Company Information
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors" placeholder="Enter company name" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors">
                  <option>Healthcare</option>
                  <option>Retail</option>
                  <option>Manufacturing</option>
                  <option>Services</option>
                </select>
              </div>
            </div>
          </div>
        
          {/* User Management */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Users className="w-5 h-5 mr-2 text-green-600" />
              User Management
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                <span className="text-sm font-medium text-gray-900">Admin Users</span>
                <span className="text-sm text-blue-600 font-semibold">3 users</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                <span className="text-sm font-medium text-gray-900">Regular Users</span>
                <span className="text-sm text-blue-600 font-semibold">117 users</span>
              </div>
            </div>
          </div>
        
          {/* Notifications */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Bell className="w-5 h-5 mr-2 text-yellow-600" />
              Notifications Preferences
            </h3>
            <div className="space-y-3">
              <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors">
                <input type="checkbox" className="mr-3 text-blue-600 focus:ring-blue-500" defaultChecked />
                <span className="text-sm font-medium text-gray-900">Email notifications</span>
              </label>
              <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors">
                <input type="checkbox" className="mr-3 text-blue-600 focus:ring-blue-500" />
                <span className="text-sm font-medium text-gray-900">SMS notifications</span>
              </label>
              <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors">
                <input type="checkbox" className="mr-3 text-blue-600 focus:ring-blue-500" defaultChecked />
                <span className="text-sm font-medium text-gray-900">Push notifications</span>
              </label>
            </div>
          </div>
        
          {/* Security */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Shield className="w-5 h-5 mr-2 text-red-600" />
              Security
            </h3>
            <div className="space-y-3">
              <button className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                <div className="flex items-center">
                  <Shield className="w-4 h-4 mr-3 text-red-600" />
                  <span className="font-medium text-gray-900">Change Password</span>
                </div>
              </button>
              <button className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                <div className="flex items-center">
                  <Database className="w-4 h-4 mr-3 text-blue-600" />
                  <span className="font-medium text-gray-900">Data Export</span>
                </div>
              </button>
            </div>
          </div>
        </div>
    </PageLayout>
  )
}


