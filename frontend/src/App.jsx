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
import './styles/global.css'
import MainLayout from './layouts/MainLayout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import HomePage from './pages/HomePage.jsx'
import SchedulePage from './pages/SchedulePage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'
import TestPage from './pages/TestPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Login page - standalone page without layout */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Main layout route - wraps all pages with header and sidebar */}
        <Route path="/" element={<MainLayout />}>
          {/* Home page - dashboard with metrics and overview */}
          <Route index element={<HomePage />} />
          
          {/* Schedule page - for managing employee schedules */}
          <Route path="schedule" element={<SchedulePage />} />
          
          {/* Settings page - application configuration */}
          <Route path="settings" element={<SettingsPage />} />
          
          {/* Test page - UI component showcase for development */}
          <Route path="test" element={<TestPage />} />
          
          {/* 404 page - handles any unmatched routes */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
