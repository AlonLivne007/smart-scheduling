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
    `flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
      isActive 
        ? "bg-blue-50 text-blue-700 shadow-sm" 
        : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
    }`;

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
      <header className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
            </svg>
            <span className="text-xl font-bold">Smart Scheduling</span>
          </div>
          <span className="text-sm text-blue-100 ml-2">Welcome, {user?.user_full_name}</span>
          {user?.is_manager && (
            <span className="ml-2 rounded-full bg-blue-500 px-3 py-1 text-xs font-medium text-white">Manager</span>
          )}
        </div>

        <button
          onClick={handleLogout}
          className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50 transition-all duration-200 shadow-sm"
        >
          Sign out
        </button>
      </header>

      {/* Body: Sidebar + Content */}
      <div className="grid grid-cols-[240px_1fr] min-h-0">
        {/* Sidebar */}
        <aside className="bg-white p-4 space-y-1.5 shadow-sm">
          <NavLink to="/" end className={linkClass} onClick={(e) => handleNavClick(e, "/")}>
            <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
            </svg>
            Dashboard
          </NavLink>
          <NavLink to="/time-off/request" className={linkClass} onClick={(e) => handleNavClick(e, "/time-off/request")}>
            <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm8 7a1 1 0 10-2 0v2H9a1 1 0 100 2h3v2a1 1 0 102 0v-2h3a1 1 0 100-2h-3V9z" clipRule="evenodd" />
            </svg>
            Request Time-Off
          </NavLink>
          <NavLink to="/time-off/my-requests" className={linkClass} onClick={(e) => handleNavClick(e, "/time-off/my-requests")}>
            <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            My Time-Off
          </NavLink>
          <NavLink to="/my-preferences" className={linkClass} onClick={(e) => handleNavClick(e, "/my-preferences")}>
            <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
            My Preferences
          </NavLink>
          {/* Admin-only links */}
          {user?.is_manager && (
            <>
              <div className="pt-3 pb-1">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3">Admin</p>
              </div>
              <NavLink to="/schedules" className={linkClass} onClick={(e) => handleNavClick(e, "/schedules")}>
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                </svg>
                Schedules
              </NavLink>
              <NavLink to="/employees" className={linkClass} onClick={(e) => handleNavClick(e, "/employees")}>
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                </svg>
                Employees
              </NavLink>
              <NavLink
                to="/admin/shift-templates"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/shift-templates")}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
                Shift Templates
              </NavLink>
              <NavLink
                to="/admin/system-constraints"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/system-constraints")}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                System Constraints
              </NavLink>
              <NavLink
                to="/admin/optimization-config"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/optimization-config")}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 4a1 1 0 00-2 0v7.268a2 2 0 000 3.464V16a1 1 0 102 0v-1.268a2 2 0 000-3.464V4zM11 4a1 1 0 10-2 0v1.268a2 2 0 000 3.464V16a1 1 0 102 0V8.732a2 2 0 000-3.464V4zM16 3a1 1 0 011 1v7.268a2 2 0 010 3.464V16a1 1 0 11-2 0v-1.268a2 2 0 010-3.464V4a1 1 0 011-1z" />
                </svg>
                Optimization Config
              </NavLink>
              <NavLink
                to="/admin/roles"
                className={linkClass}
                onClick={(e) => handleNavClick(e, "/admin/roles")}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
                Roles
              </NavLink>
              <NavLink to="/admin/time-off" className={linkClass} onClick={(e) => handleNavClick(e, "/admin/time-off")}>
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
                Manage Time-Off
              </NavLink>
            </>
          )}
        </aside>

        {/* Content */}
        <main className="p-6 overflow-auto bg-gradient-to-br from-gray-50 to-gray-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
}