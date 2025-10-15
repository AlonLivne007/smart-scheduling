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
import { Button, Logo } from '../components/ui';

export default function MainLayout() {
  return (
    <div className="min-vh-100">
      {/* Header Section - Contains logo and sign-out button */}
      <header className="bg-white shadow-sm border-bottom">
        <div className="container-fluid">
          <div className="d-flex align-items-center justify-content-between py-3">
            {/* Brand logo - medium size for header */}
            <Logo size="medium" />
            {/* Sign out button - danger variant for logout action */}
            <Button variant="danger" size="small">
              <i className="bi bi-box-arrow-right me-2"></i>Sign Out
            </Button>
          </div>
        </div>
      </header>

      <div className="d-flex">
        {/* Sidebar Navigation - Fixed width sidebar with navigation links */}
        <nav className="bg-white shadow-sm border-end" style={{ width: '250px', minHeight: 'calc(100vh - 80px)' }}>
          <div className="p-3">
            <ul className="nav nav-pills flex-column gap-2">
              {/* Home Navigation Link */}
              <li className="nav-item">
                <NavLink 
                  to="/" 
                  end 
                  className={({ isActive }) => 
                    `nav-link d-flex align-items-center rounded-3 ${
                      isActive 
                        ? 'bg-primary text-white' 
                        : 'text-muted hover-bg-light'
                    }`
                  }
                >
                  <i className="bi bi-house me-3"></i>Home
                </NavLink>
              </li>
              
              {/* Schedule Navigation Link */}
              <li className="nav-item">
                <NavLink 
                  to="/schedule" 
                  className={({ isActive }) => 
                    `nav-link d-flex align-items-center rounded-3 ${
                      isActive 
                        ? 'bg-primary text-white' 
                        : 'text-muted hover-bg-light'
                    }`
                  }
                >
                  <i className="bi bi-calendar3 me-3"></i>Schedule
                </NavLink>
              </li>
              
              {/* Employees Navigation Link */}
              <li className="nav-item">
                <NavLink 
                  to="/employees" 
                  className={({ isActive }) => 
                    `nav-link d-flex align-items-center rounded-3 ${
                      isActive 
                        ? 'bg-primary text-white' 
                        : 'text-muted hover-bg-light'
                    }`
                  }
                >
                  <i className="bi bi-people me-3"></i>Employees
                </NavLink>
              </li>
              
              {/* Reports Navigation Link */}
              <li className="nav-item">
                <NavLink 
                  to="/reports" 
                  className={({ isActive }) => 
                    `nav-link d-flex align-items-center rounded-3 ${
                      isActive 
                        ? 'bg-primary text-white' 
                        : 'text-muted hover-bg-light'
                    }`
                  }
                >
                  <i className="bi bi-graph-up me-3"></i>Reports
                </NavLink>
              </li>
              
              {/* Test UI Navigation Link - For development/testing */}
              <li className="nav-item">
                <NavLink 
                  to="/test" 
                  className={({ isActive }) => 
                    `nav-link d-flex align-items-center rounded-3 ${
                      isActive 
                        ? 'bg-primary text-white' 
                        : 'text-muted hover-bg-light'
                    }`
                  }
                >
                  <i className="bi bi-palette me-3"></i>Test UI
                </NavLink>
              </li>
            </ul>
          </div>
        </nav>

        {/* Main Content Area - Renders child route components */}
        <main className="flex-grow-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}


