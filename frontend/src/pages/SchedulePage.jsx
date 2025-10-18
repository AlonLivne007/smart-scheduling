/**
 * Schedule Page Component
 * 
 * The schedule management page for creating and managing employee schedules.
 * This is a placeholder page that will be expanded with full scheduling functionality.
 * 
 * Planned Features:
 * - Calendar view for schedule visualization
 * - Drag-and-drop schedule creation
 * - Employee availability management
 * - Shift templates and patterns
 * - Schedule conflict detection
 * - Export and sharing capabilities
 * 
 * @component
 * @returns {JSX.Element} The schedule management page
 */
import Card from '../components/ui/Card.jsx';
import { Calendar, Plus, Users, Clock } from 'lucide-react';

export default function Schedule() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-blue-700 mb-2">Schedule Management</h1>
          <p className="text-lg text-blue-500 font-light">Build and manage your company schedules here.</p>
        </div>
      
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg p-6 h-full">
              <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Plus className="w-5 h-5 mr-2 text-blue-600" />
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-3 text-blue-600" />
                    <span className="font-medium text-gray-900">Create New Schedule</span>
                  </div>
                </button>
                <button className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                  <div className="flex items-center">
                    <Users className="w-4 h-4 mr-3 text-green-600" />
                    <span className="font-medium text-gray-900">Assign Employees</span>
                  </div>
                </button>
                <button className="w-full text-left p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-3 text-purple-600" />
                    <span className="font-medium text-gray-900">Set Shift Times</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Schedule Overview</h3>
              <div className="text-center py-12">
                <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No schedules created yet</h3>
                <p className="text-gray-500 mb-4">Start by creating your first schedule to manage your workforce.</p>
                <button className="bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200">
                  Create Schedule
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


