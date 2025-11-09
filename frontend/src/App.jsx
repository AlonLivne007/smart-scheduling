/**
 * App Component
 *
 * Login is the public entry. Everything under "/" is protected.
 * Admin-only pages use AdminRoute on top of ProtectedRoute.
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles/global.css";

import MainLayout from "./layouts/MainLayout.jsx";
import LoginPage from "./pages/login/LoginPage.jsx";
import AddUserPage from "./pages/Admin/AddUser/AddUserPage.jsx";
import EmployeesPage from "./pages/Admin/Employees/EmployeesPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import SchedulePage from "./pages/SchedulePage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import TestPage from "./pages/TestPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";

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
    <BrowserRouter>
      <Routes>
        {/* Public entry */}
        <Route path="/login" element={<LoginPage />} />

        {/* Admin only pages (UI guard; backend also enforces) */}
        <Route
          path="/admin/add-user"
          element={
            <AdminRoute>
              <AddUserPage />
            </AdminRoute>
          }
        />

        {/* Protected app shell */}
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
          <Route path="test" element={<TestPage />} />

          {/* NEW: Employees (admin-only) */}
          <Route
            path="employees"
            element={
              <AdminRoute>
                <EmployeesPage />
              </AdminRoute>
            }
          />

          <Route path="*" element={<NotFoundPage />} />
        </Route>

        {/* fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}