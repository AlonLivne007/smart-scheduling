/**
 * Settings Page Component
 * 
 * The application settings page for configuring company-level preferences and system integrations.
 * This is a placeholder page that will be expanded with comprehensive settings functionality.
 * 
 * Planned Features:
 * - Company information and branding
 * - User management and permissions
 * - Notification preferences
 * - Integration settings (calendar, email, SMS)
 * - System configuration options
 * - Data export and backup settings
 * - Security and privacy settings
 * 
 * @component
 * @returns {JSX.Element} The settings configuration page
 */
import Card from '../components/ui/Card.jsx';
import { Building2, Users, Bell, Shield, Database, Mail } from 'lucide-react';

export default function Settings() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-blue-700 mb-2">Settings</h1>
          <p className="text-lg text-blue-500 font-light">Configure company-level preferences and integrations.</p>
        </div>
      
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Company Settings */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Building2 className="w-5 h-5 mr-2 text-blue-600" />
              Company Information
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors" placeholder="Enter company name" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors">
                  <option>Healthcare</option>
                  <option>Retail</option>
                  <option>Manufacturing</option>
                  <option>Services</option>
                </select>
              </div>
            </div>
          </div>
        
          {/* User Management */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Users className="w-5 h-5 mr-2 text-green-600" />
              User Management
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                <span className="text-sm font-medium text-gray-900">Admin Users</span>
                <span className="text-sm text-blue-600 font-semibold">3 users</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                <span className="text-sm font-medium text-gray-900">Regular Users</span>
                <span className="text-sm text-blue-600 font-semibold">117 users</span>
              </div>
            </div>
          </div>
        
          {/* Notifications */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Bell className="w-5 h-5 mr-2 text-yellow-600" />
              Notifications
            </h3>
            <div className="space-y-3">
              <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors">
                <input type="checkbox" className="mr-3 text-blue-600 focus:ring-blue-500" defaultChecked />
                <span className="text-sm font-medium text-gray-900">Email notifications</span>
              </label>
              <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors">
                <input type="checkbox" className="mr-3 text-blue-600 focus:ring-blue-500" />
                <span className="text-sm font-medium text-gray-900">SMS notifications</span>
              </label>
              <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors">
                <input type="checkbox" className="mr-3 text-blue-600 focus:ring-blue-500" defaultChecked />
                <span className="text-sm font-medium text-gray-900">Push notifications</span>
              </label>
            </div>
          </div>
        
          {/* Security */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Shield className="w-5 h-5 mr-2 text-red-600" />
              Security
            </h3>
            <div className="space-y-3">
              <button className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                <div className="flex items-center">
                  <Shield className="w-4 h-4 mr-3 text-red-600" />
                  <span className="font-medium text-gray-900">Change Password</span>
                </div>
              </button>
              <button className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                <div className="flex items-center">
                  <Database className="w-4 h-4 mr-3 text-blue-600" />
                  <span className="font-medium text-gray-900">Data Export</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


