// frontend/src/layouts/MainLayout.jsx
import React, { useState, useEffect } from "react";
import { NavLink, Outlet, useNavigate, useLocation } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { getAuth, logout } from "../lib/auth";
import LoadingSpinner from "../components/ui/LoadingSpinner.jsx";

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = getAuth();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [nextLocation, setNextLocation] = useState(null);

  // Detect route changes and show loading spinner
  useEffect(() => {
    if (nextLocation && nextLocation !== location) {
      // Page has loaded, hide spinner
      setIsTransitioning(false);
      setNextLocation(null);
    }
  }, [location, nextLocation]);

  // Intercept NavLink clicks to show spinner
  const handleNavClick = (e, href) => {
    const isSamePage = location.pathname === href;
    if (!isSamePage) {
      setIsTransitioning(true);
      setNextLocation(href);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const linkClass = ({ isActive }) =>
    `block rounded px-3 py-2 ${isActive ? "bg-blue-100 text-blue-700" : "text-gray-700 hover:bg-gray-100"}`;

  return (
    <div className="min-h-screen grid grid-rows-[auto_1fr]">
      {/* Loading spinner overlay during page transitions */}
      {isTransitioning && (
        <div className="fixed inset-0 bg-white bg-opacity-75 backdrop-blur-sm flex items-center justify-center z-40">
          <div className="text-center">
            <div className="relative inline-block">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full blur opacity-75 animate-pulse"></div>
              <div className="relative bg-white rounded-full p-3">
                <svg className="w-10 h-10 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </div>
            <p className="mt-3 text-gray-700 font-medium">Loading...</p>
          </div>
        </div>
      )}
      {/* Toaster component for displaying toast notifications */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        toastOptions={{
          // Define default options
          duration: 4000,
          style: {
            background: '#fff',
            color: '#000',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            borderRadius: '8px',
            padding: '16px',
          },
          // Default options for specific types
          success: {
            duration: 4000,
            style: {
              background: '#f0fdf4',
              color: '#166534',
              border: '1px solid #dcfce7',
            },
            iconTheme: {
              primary: '#16a34a',
              secondary: '#f0fdf4',
            },
          },
          error: {
            duration: 5000,
            style: {
              background: '#fef2f2',
              color: '#991b1b',
              border: '1px solid #fee2e2',
            },
            iconTheme: {
              primary: '#dc2626',
              secondary: '#fef2f2',
            },
          },
          loading: {
            duration: Infinity,
            style: {
              background: '#eff6ff',
              color: '#1e40af',
              border: '1px solid #bfdbfe',
            },
          },
        }}
      />

      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b bg-white">
        <div className="flex items-center gap-3">
          <span className="text-xl font-semibold">Smart Scheduling</span>
          <span className="text-sm text-gray-500">| Welcome, {user?.user_full_name}</span>
          {user?.is_manager && (
            <span className="ml-2 rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">Manager</span>
          )}
        </div>

        <button
          onClick={handleLogout}
          className="rounded bg-gray-100 px-3 py-1.5 text-sm hover:bg-gray-200"
        >
          Sign out
        </button>
      </header>

      {/* Body: Sidebar + Content */}
      <div className="grid grid-cols-[220px_1fr] min-h-0">
        {/* Sidebar */}
        <aside className="border-r bg-white p-3 space-y-1">
          <NavLink to="/" end className={linkClass} onClick={(e) => handleNavClick(e, "/")}>
            Dashboard
          </NavLink>
          <NavLink to="/time-off/request" className={linkClass} onClick={(e) => handleNavClick(e, "/time-off/request")}>
            Request Time-Off
          </NavLink>
          <NavLink to="/time-off/my-requests" className={linkClass} onClick={(e) => handleNavClick(e, "/time-off/my-requests")}>
            My Time-Off
          </NavLink>
          <NavLink to="/my-preferences" className={linkClass} onClick={(e) => handleNavClick(e, "/my-preferences")}>
            My Preferences
          </NavLink>
          <NavLink to="/settings" className={linkClass} onClick={(e) => handleNavClick(e, "/settings")}>
            Settings
          </NavLink>
          {/* Admin-only links */}
          {user?.is_manager && (
            <>
              <NavLink to="/schedules" className={linkClass} onClick={(e) => handleNavClick(e, "/schedules")}>
                Schedules
              </NavLink>
              <NavLink to="/employees" className={linkClass} onClick={(e) => handleNavClick(e, "/employees")}>
                Employees
              </NavLink>
              <NavLink
                to="/admin/shift-templates"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/shift-templates")}
              >
                Shift Templates
              </NavLink>
              <NavLink
                to="/admin/system-constraints"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/system-constraints")}
              >
                System Constraints
              </NavLink>
              <NavLink
                to="/admin/optimization-config"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/optimization-config")}
              >
                Optimization Config
              </NavLink>
              <NavLink
                to="/admin/roles"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/roles")}
              >
                Roles
              </NavLink>
              <NavLink to="/admin/time-off" className={linkClass} onClick={(e) => handleNavClick(e, "/admin/time-off")}>
                Manage Time-Off
              </NavLink>
            </>
          )}
        </aside>

        {/* Content */}
        <main className="p-4 overflow-auto bg-gray-50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}