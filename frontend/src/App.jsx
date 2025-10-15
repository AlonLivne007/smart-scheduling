/**
 * App Component
 * 
 * The main application component that sets up routing for the entire application.
 * Uses React Router for client-side navigation with a nested route structure.
 * 
 * Route Structure:
 * - MainLayout wraps all pages and provides consistent navigation
 * - Home page is the default route (/)
 * - Schedule, Settings, and Test pages are nested under MainLayout
 * - NotFound page handles 404 errors
 * 
 * @component
 * @returns {JSX.Element} The main application with routing
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import MainLayout from './layouts/MainLayout.jsx'
import Home from './pages/Home.jsx'
import Schedule from './pages/Schedule.jsx'
import Settings from './pages/Settings.jsx'
import TestPage from './pages/TestPage.jsx'
import NotFound from './pages/NotFound.jsx'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Main layout route - wraps all pages with header and sidebar */}
        <Route path="/" element={<MainLayout />}>
          {/* Home page - dashboard with metrics and overview */}
          <Route index element={<Home />} />
          
          {/* Schedule page - for managing employee schedules */}
          <Route path="schedule" element={<Schedule />} />
          
          {/* Settings page - application configuration */}
          <Route path="settings" element={<Settings />} />
          
          {/* Test page - UI component showcase for development */}
          <Route path="test" element={<TestPage />} />
          
          {/* 404 page - handles any unmatched routes */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
