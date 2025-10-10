import { NavLink, Outlet } from 'react-router-dom'
import { Button, Logo } from '../components/ui';

export default function MainLayout() {
  return (
    <div className="min-vh-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-bottom">
        <div className="container-fluid">
          <div className="d-flex align-items-center justify-content-between py-3">
            <Logo size="medium" />
            <Button variant="danger" size="small">
              <i className="bi bi-box-arrow-right me-2"></i>Sign Out
            </Button>
          </div>
        </div>
      </header>

      <div className="d-flex">
        {/* Sidebar */}
        <nav className="bg-white shadow-sm border-end" style={{ width: '250px', minHeight: 'calc(100vh - 80px)' }}>
          <div className="p-3">
            <ul className="nav nav-pills flex-column gap-2">
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

        {/* Main Content */}
        <main className="flex-grow-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}


