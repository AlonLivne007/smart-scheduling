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
    <div className="w-full py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">Configure company-level preferences and integrations.</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Company Settings */}
        <Card>
          <Card.Header>
            <Card.Title className="flex items-center">
              <Building2 className="w-5 h-5 mr-2 text-blue-600" />
              Company Information
            </Card.Title>
          </Card.Header>
          <Card.Body>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Enter company name" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option>Healthcare</option>
                  <option>Retail</option>
                  <option>Manufacturing</option>
                  <option>Services</option>
                </select>
              </div>
            </div>
          </Card.Body>
        </Card>
        
        {/* User Management */}
        <Card>
          <Card.Header>
            <Card.Title className="flex items-center">
              <Users className="w-5 h-5 mr-2 text-green-600" />
              User Management
            </Card.Title>
          </Card.Header>
          <Card.Body>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium">Admin Users</span>
                <span className="text-sm text-gray-500">3 users</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium">Regular Users</span>
                <span className="text-sm text-gray-500">117 users</span>
              </div>
            </div>
          </Card.Body>
        </Card>
        
        {/* Notifications */}
        <Card>
          <Card.Header>
            <Card.Title className="flex items-center">
              <Bell className="w-5 h-5 mr-2 text-yellow-600" />
              Notifications
            </Card.Title>
          </Card.Header>
          <Card.Body>
            <div className="space-y-3">
              <label className="flex items-center">
                <input type="checkbox" className="mr-3" defaultChecked />
                <span className="text-sm">Email notifications</span>
              </label>
              <label className="flex items-center">
                <input type="checkbox" className="mr-3" />
                <span className="text-sm">SMS notifications</span>
              </label>
              <label className="flex items-center">
                <input type="checkbox" className="mr-3" defaultChecked />
                <span className="text-sm">Push notifications</span>
              </label>
            </div>
          </Card.Body>
        </Card>
        
        {/* Security */}
        <Card>
          <Card.Header>
            <Card.Title className="flex items-center">
              <Shield className="w-5 h-5 mr-2 text-red-600" />
              Security
            </Card.Title>
          </Card.Header>
          <Card.Body>
            <div className="space-y-3">
              <button className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
                <div className="flex items-center">
                  <Shield className="w-4 h-4 mr-3 text-red-600" />
                  <span className="font-medium">Change Password</span>
                </div>
              </button>
              <button className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
                <div className="flex items-center">
                  <Database className="w-4 h-4 mr-3 text-blue-600" />
                  <span className="font-medium">Data Export</span>
                </div>
              </button>
            </div>
          </Card.Body>
        </Card>
      </div>
    </div>
  )
}


