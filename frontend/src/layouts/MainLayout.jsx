// frontend/src/layouts/MainLayout.jsx
import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { getAuth, logout } from "../lib/auth";

export default function MainLayout() {
  const navigate = useNavigate();
  const { user } = getAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const linkClass = ({ isActive }) =>
    `block rounded px-3 py-2 ${isActive ? "bg-blue-100 text-blue-700" : "text-gray-700 hover:bg-gray-100"}`;

  return (
    <div className="min-h-screen grid grid-rows-[auto_1fr]">
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
          <NavLink to="/" end className={linkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/schedule" className={linkClass}>
            Schedule
          </NavLink>
          <NavLink to="/settings" className={linkClass}>
            Settings
          </NavLink>
          {/* Admin-only Employees link */}
          {user?.is_manager && (
            <NavLink to="/employees" className={linkClass}>
              Employees
            </NavLink>
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