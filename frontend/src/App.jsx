/**
 * App Component
 *
 * Login is the public entry. Everything under "/" is protected.
 * Admin-only pages use AdminRoute on top of ProtectedRoute.
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles/global.css";

import ErrorBoundary from "./components/ErrorBoundary.jsx";
import { LoadingProvider } from "./contexts/LoadingContext.jsx";
import MainLayout from "./layouts/MainLayout.jsx";
import LoginPage from "./pages/login/LoginPage.jsx";
import AddUserPage from "./pages/Admin/AddUser/AddUserPage.jsx";
import EmployeesPage from "./pages/Admin/Employees/EmployeesPage.jsx";
import EditUserPage from "./pages/Admin/Employees/EditUserPage.jsx";
import EmployeeProfilePage from "./pages/Admin/Employees/EmployeeProfilePage.jsx";
import ScheduleListPage from "./pages/Admin/Schedule/ScheduleListPage.jsx";
import CreateScheduleWizardPage from "./pages/Admin/Schedule/CreateScheduleWizardPage.jsx";
import ScheduleCalendarPage from "./pages/Admin/Schedule/ScheduleCalendarPage.jsx";
import ShiftAssignmentPage from "./pages/Admin/Schedule/ShiftAssignmentPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import SchedulePage from "./pages/SchedulePage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import ErrorTestPage from "./pages/debug/ErrorTestPage.jsx";
import InputFieldDemo from "./pages/debug/InputFieldDemo.jsx";
import ConfirmDialogDemo from "./pages/debug/ConfirmDialogDemo.jsx";
import TimeOffRequestPage from "./pages/TimeOff/TimeOffRequestPage.jsx";
import MyTimeOffPage from "./pages/TimeOff/MyTimeOffPage.jsx";
import MyPreferencesPage from "./pages/MyPreferencesPage.jsx";
import TimeOffManagementPage from "./pages/Admin/TimeOffManagementPage.jsx";
import RolesManagementPage from "./pages/Admin/RolesManagementPage.jsx";
import ShiftTemplatesManagementPage from "./pages/Admin/ShiftTemplatesManagementPage.jsx";
import SystemConstraintsPage from "./pages/Admin/SystemConstraintsPage.jsx";
import OptimizationConfigPage from "./pages/Admin/OptimizationConfigPage.jsx";


function getAuth() {
  const token = localStorage.getItem("access_token");
  const user = JSON.parse(localStorage.getItem("auth_user") || "null");
  return { token, user };
}

function ProtectedRoute({ children }) {
  const { token } = getAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function AdminRoute({ children }) {
  const { token, user } = getAuth();
  if (!token) return <Navigate to="/login" replace />;
  if (!user?.is_manager) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <ErrorBoundary>
      <LoadingProvider>
        <BrowserRouter>
          <Routes>
            {/* Public entry */}
            <Route path="/login" element={<LoginPage />} />

          {/* Debug/Testing Routes (development) */}
          <Route path="/debug/error" element={<ErrorTestPage />} />
          <Route path="/debug/input-validation" element={<InputFieldDemo />} />
          <Route path="/debug/confirm-dialog" element={<ConfirmDialogDemo />} />

          {/* Admin only pages (UI guard; backend also enforces) */}
          <Route
            path="/admin/add-user"
            element={
              <AdminRoute>
                <AddUserPage />
              </AdminRoute>
            }
          />        {/* Protected app shell */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="schedule" element={<SchedulePage />} />
          <Route path="settings" element={<SettingsPage />} />

          {/* Schedules list (admin) */}
          <Route
            path="schedules"
            element={
              <AdminRoute>
                <ScheduleListPage />
              </AdminRoute>
            }
          />

          {/* Create schedule wizard (admin) */}
          <Route
            path="schedules/create"
            element={
              <AdminRoute>
                <CreateScheduleWizardPage />
              </AdminRoute>
            }
          />

          {/* Schedule calendar view (admin) */}
          <Route
            path="schedules/:id"
            element={
              <AdminRoute>
                <ScheduleCalendarPage />
              </AdminRoute>
            }
          />

          {/* Shift assignment management (admin) */}
          <Route
            path="schedules/:scheduleId/shifts/:shiftId"
            element={
              <AdminRoute>
                <ShiftAssignmentPage />
              </AdminRoute>
            }
          />

          {/* Employees list (admin) */}
          <Route
            path="employees"
            element={
              <AdminRoute>
                <EmployeesPage />
              </AdminRoute>
            }
          />

          {/* Employee profile (admin) */}
          <Route
            path="employees/:id"
            element={
              <AdminRoute>
                <EmployeeProfilePage />
              </AdminRoute>
            }
          />

          {/* Edit employee (admin) */}
          <Route
            path="employees/edit/:id"
            element={
              <AdminRoute>
                <EditUserPage />
              </AdminRoute>
            }
          />

          {/* Time-Off Request (all employees) */}
          <Route path="time-off/request" element={<TimeOffRequestPage />} />
          
          {/* My Time-Off Requests (all employees) */}
          <Route path="time-off/my-requests" element={<MyTimeOffPage />} />

          {/* My Preferences (all employees) */}
          <Route path="my-preferences" element={<MyPreferencesPage />} />

          {/* Time-Off Management (admin/manager only) */}
          <Route
            path="admin/time-off"
            element={
              <AdminRoute>
                <TimeOffManagementPage />
              </AdminRoute>
            }
          />

          {/* Role Management (admin/manager only) */}
          <Route
            path="admin/roles"
            element={
              <AdminRoute>
                <RolesManagementPage />
              </AdminRoute>
            }
          />

          {/* Shift Template Management (admin/manager only) */}
          <Route
            path="admin/shift-templates"
            element={
              <AdminRoute>
                <ShiftTemplatesManagementPage />
              </AdminRoute>
            }
          />

          {/* System Constraints Management (admin/manager only) */}
          <Route
            path="admin/system-constraints"
            element={
              <AdminRoute>
                <SystemConstraintsPage />
              </AdminRoute>
            }
          />

          {/* Optimization Configuration Management (admin/manager only) */}
          <Route
            path="admin/optimization-config"
            element={
              <AdminRoute>
                <OptimizationConfigPage />
              </AdminRoute>
            }
          />

        </Route>

        {/* fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
      </LoadingProvider>
    </ErrorBoundary>
  );
}
