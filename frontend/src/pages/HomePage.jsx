/**
 * Home Page Component
 * 
 * The main dashboard page that provides an overview of the workforce management system.
 * Displays key metrics, welcome message, and quick actions for users.
 * 
 * Features:
 * - Large branded logo with subtitle
 * - Welcome card with call-to-action buttons
 * - Key metrics cards (employees, shifts, coverage)
 * - Recent activity section
 * - Responsive grid layout
 * 
 * @component
 * @returns {JSX.Element} The home dashboard page
 */
import Button from '../components/ui/Button.jsx';
import Card from '../components/ui/Card.jsx';
import Logo from '../components/ui/Logo.jsx';
import { Users, Clock, TrendingUp, Activity } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Header Section - Logo and subtitle */}
          <div className="lg:col-span-12">
            <div className="text-center mb-8">
              <div className="mb-6">
                <svg 
                  width="80" 
                  height="80" 
                  viewBox="0 0 120 120" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                  className="mx-auto"
                >
                  <g transform="translate(16,16)">
                    <rect x="0" y="6" rx="14" ry="14" width="88" height="88" fill="#ffffff" stroke="#2563eb" strokeWidth="2"/>
                    <rect x="0" y="6" rx="14" ry="14" width="88" height="24" fill="#2563eb"/>
                    <g fill="#ffffff">
                      <rect x="18" y="0" width="10" height="16" rx="3" ry="3"/>
                      <rect x="60" y="0" width="10" height="16" rx="3" ry="3"/>
                    </g>
                    <g stroke="#e2e8f0" strokeWidth="1">
                      <line x1="12" y1="40" x2="76" y2="40"/>
                      <line x1="12" y1="56" x2="76" y2="56"/>
                      <line x1="12" y1="72" x2="76" y2="72"/>
                      <line x1="28" y1="24" x2="28" y2="88"/>
                      <line x1="48" y1="24" x2="48" y2="88"/>
                      <line x1="68" y1="24" x2="68" y2="88"/>
                    </g>
                    <circle cx="58" cy="68" r="12" fill="none" stroke="#1d4ed8" strokeWidth="3"/>
                    <path d="M51 68 l4 4 l10 -10" fill="none" stroke="#1d4ed8" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                  </g>
                </svg>
              </div>
              <h1 className="text-4xl font-bold text-blue-700 mb-2">
                Smart Scheduling
              </h1>
              <p className="text-lg text-blue-500 font-light">
                Workforce Management Dashboard
              </p>
            </div>
          </div>
        
          {/* Welcome Card - Main call-to-action section */}
          <div className="lg:col-span-12">
            <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
              <h2 className="text-2xl font-bold text-blue-600 mb-2">Welcome to your dashboard</h2>
              <p className="text-gray-600 mb-6">Manage your workforce efficiently with our smart scheduling system.</p>
              <div className="flex gap-3">
                <button className="bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200">
                  Get Started
                </button>
                <button className="bg-green-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors duration-200">
                  Learn More
                </button>
              </div>
            </div>
          </div>
        
          {/* Metrics Cards - Key performance indicators */}
          <div className="lg:col-span-4">
            <div className="bg-white rounded-2xl shadow-lg p-6 h-full hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
              <div className="text-center">
                <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Employees</h3>
                <h2 className="text-4xl font-bold text-blue-600 mb-2">120</h2>
                <p className="text-gray-600">Active team members</p>
              </div>
            </div>
          </div>
          
          <div className="lg:col-span-4">
            <div className="bg-white rounded-2xl shadow-lg p-6 h-full hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
              <div className="text-center">
                <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                  <Clock className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Upcoming Shifts</h3>
                <h2 className="text-4xl font-bold text-blue-600 mb-2">24</h2>
                <p className="text-gray-600">Next 7 days</p>
              </div>
            </div>
          </div>
          
          <div className="lg:col-span-4">
            <div className="bg-white rounded-2xl shadow-lg p-6 h-full hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
              <div className="text-center">
                <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Coverage Rate</h3>
                <h2 className="text-4xl font-bold text-blue-600 mb-2">96%</h2>
                <p className="text-gray-600">This week</p>
              </div>
            </div>
          </div>
        
          {/* Recent Activity Section - Shows latest system activity */}
          <div className="lg:col-span-12">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h3>
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No recent activity</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


