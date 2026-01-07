/**
 * Settings Page Component
 * 
 * User settings page for profile information and preferences.
 * 
 * @component
 * @returns {JSX.Element} The settings page
 */
import React, { useMemo, useState } from 'react';
import Button from '../components/ui/Button.jsx';
import PageLayout from '../layouts/PageLayout.jsx';
import PageHeader from '../components/ui/PageHeader.jsx';
import { showSuccess, showError } from '../lib/notifications.jsx';
import { User, Bell, Lock } from 'lucide-react';

export default function Settings() {
  const authUser = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('auth_user') || 'null');
    } catch {
      return null;
    }
  }, []);

  const [emailNotifications, setEmailNotifications] = useState(true);
  const [smsNotifications, setSmsNotifications] = useState(false);
  const [pushNotifications, setPushNotifications] = useState(true);

  const handleSaveNotifications = () => {
    // TODO: Implement API call to save notification preferences
    showSuccess('Notification preferences saved successfully!');
  };

  const handleChangePassword = () => {
    // TODO: Implement change password functionality
    showError('Change password feature coming soon!');
  };

  return (
    <PageLayout>
      <PageHeader 
        title="Settings" 
        subtitle="Manage your account settings and preferences" 
      />
      
      <div className="max-w-4xl space-y-6">
        {/* My Profile */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <User className="w-5 h-5 mr-2 text-blue-600" />
            My Profile
          </h3>
          {authUser ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-900">
                    {authUser.user_full_name || '—'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-900">
                    {authUser.user_email || '—'}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-900">
                    {authUser.is_manager ? 'Manager' : 'Employee'}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-600">Not signed in.</p>
          )}
        </div>

        {/* Notification Preferences */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Bell className="w-5 h-5 mr-2 text-yellow-600" />
            Notification Preferences
          </h3>
          <div className="space-y-3 mb-6">
            <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors cursor-pointer">
              <input 
                type="checkbox" 
                className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 rounded" 
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
              />
              <div>
                <div className="text-sm font-medium text-gray-900">Email notifications</div>
                <div className="text-xs text-gray-500">Receive schedule updates via email</div>
              </div>
            </label>
            <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors cursor-pointer">
              <input 
                type="checkbox" 
                className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 rounded" 
                checked={smsNotifications}
                onChange={(e) => setSmsNotifications(e.target.checked)}
              />
              <div>
                <div className="text-sm font-medium text-gray-900">SMS notifications</div>
                <div className="text-xs text-gray-500">Get text messages for urgent updates</div>
              </div>
            </label>
            <label className="flex items-center p-3 rounded-lg hover:bg-blue-50 transition-colors cursor-pointer">
              <input 
                type="checkbox" 
                className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 rounded" 
                checked={pushNotifications}
                onChange={(e) => setPushNotifications(e.target.checked)}
              />
              <div>
                <div className="text-sm font-medium text-gray-900">Push notifications</div>
                <div className="text-xs text-gray-500">Browser notifications for schedule changes</div>
              </div>
            </label>
          </div>
          <Button variant="primary" onClick={handleSaveNotifications}>
            Save Preferences
          </Button>
        </div>
      
        {/* Security */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Lock className="w-5 h-5 mr-2 text-red-600" />
            Security
          </h3>
          <div className="space-y-3">
            <button 
              onClick={handleChangePassword}
              className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Lock className="w-4 h-4 mr-3 text-red-600" />
                  <div>
                    <div className="font-medium text-gray-900">Change Password</div>
                    <div className="text-xs text-gray-500">Update your account password</div>
                  </div>
                </div>
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}


