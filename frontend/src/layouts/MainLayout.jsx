/**
 * MainLayout Component
 * 
 * The main application layout that provides the overall structure for all pages.
 * Includes a header with logo and sign-out button, and a sidebar navigation.
 * 
 * Features:
 * - Responsive header with branded logo
 * - Sidebar navigation with active state highlighting
 * - Main content area that renders child routes
 * - Consistent blue theme throughout
 * 
 * @component
 * @returns {JSX.Element} The main layout structure
 */
import { NavLink, Outlet } from 'react-router-dom'
import Button from '../components/ui/Button.jsx';
import Logo from '../components/ui/Logo.jsx';
import { LogOut, Home, Calendar, Settings, TestTube } from 'lucide-react';

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section - Contains logo and sign-out button */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            {/* Brand logo - medium size for header */}
            <Logo size="medium" />
            {/* Sign out button - danger variant for logout action */}
            <Button variant="danger" size="small">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation - Fixed width sidebar with navigation links */}
        <nav className="bg-white shadow-sm border-r border-gray-200 w-64 min-h-screen">
          <div className="p-4">
            <ul className="space-y-2">
              {/* Home Navigation Link */}
              <li>
                <NavLink 
                  to="/" 
                  end 
                  className={({ isActive }) => 
                    `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`
                  }
                >
                  <Home className="w-4 h-4 mr-3" />
                  Dashboard
                </NavLink>
              </li>
              
              {/* Schedule Navigation Link */}
              <li>
                <NavLink 
                  to="/schedule" 
                  className={({ isActive }) => 
                    `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`
                  }
                >
                  <Calendar className="w-4 h-4 mr-3" />
                  Schedule
                </NavLink>
              </li>
              
              {/* Settings Navigation Link */}
              <li>
                <NavLink 
                  to="/settings" 
                  className={({ isActive }) => 
                    `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`
                  }
                >
                  <Settings className="w-4 h-4 mr-3" />
                  Settings
                </NavLink>
              </li>
              
              {/* Test UI Navigation Link - For development/testing */}
              <li>
                <NavLink 
                  to="/test" 
                  className={({ isActive }) => 
                    `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`
                  }
                >
                  <TestTube className="w-4 h-4 mr-3" />
                  Test UI
                </NavLink>
              </li>
            </ul>
          </div>
        </nav>

        {/* Main Content Area - Renders child route components */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}


