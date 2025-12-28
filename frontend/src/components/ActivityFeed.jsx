/**
 * ActivityFeed Component
 * 
 * Displays recent system activities with timestamps and action icons.
 * Shows the latest user actions like shift assignments, time-off approvals, etc.
 * 
 * Features:
 * - Shows recent activities with descriptions
 * - Relative timestamps (e.g., "2 minutes ago")
 * - Color-coded activity types with icons
 * - Auto-refresh capability (optional)
 * - Loading and empty states
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Array} props.activities - Array of activity objects
 * @param {boolean} props.isLoading - Whether activities are loading
 * @param {boolean} props.showViewAll - Whether to show "View All" link
 * @param {Function} props.onViewAll - Callback for "View All" button
 * 
 * @example
 * <ActivityFeed 
 *   activities={activities}
 *   isLoading={loading}
 *   showViewAll={true}
 *   onViewAll={() => navigate('/activities')}
 * />
 */

import React from 'react';
import {
  UserPlus,
  ClipboardList,
  CheckCircle,
  XCircle,
  Calendar,
  Activity,
  ArrowRight,
} from 'lucide-react';
import Skeleton from './ui/Skeleton.jsx';

// Icon mapping for different activity types
const ICON_MAP = {
  UserPlus: UserPlus,
  ClipboardList: ClipboardList,
  CheckCircle: CheckCircle,
  XCircle: XCircle,
  Calendar: Calendar,
};

function ActivityFeed({ 
  activities = [], 
  isLoading = false,
  showViewAll = true,
  onViewAll = () => {},
}) {
  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-4 items-center">
            <Skeleton width="40px" height="40px" rounded={true} />
            <div className="flex-1 space-y-2">
              <Skeleton size="small" width="60%" />
              <Skeleton size="small" width="40%" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Empty state
  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8">
        <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-500">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Activity list */}
      <div className="space-y-3">
        {activities.map((activity) => {
          const IconComponent = ICON_MAP[activity.typeConfig?.icon];

          return (
            <div key={activity.id} className="flex gap-4 items-start p-3 rounded-lg hover:bg-gray-50 transition-colors">
              {/* Activity icon */}
              <div className={`${activity.typeConfig?.color} rounded-full p-2 flex-shrink-0 mt-0.5`}>
                {IconComponent ? (
                  <IconComponent className={`w-5 h-5 ${activity.typeConfig?.textColor}`} />
                ) : (
                  <Activity className="w-5 h-5 text-gray-600" />
                )}
              </div>

              {/* Activity details */}
              <div className="flex-1 min-w-0">
                <p className="text-gray-900 text-sm font-medium break-words">
                  {activity.description}
                </p>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                  <span>{activity.user}</span>
                  <span>•</span>
                  <span>{activity.relativeTime}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* View All link */}
      {showViewAll && (
        <button
          onClick={onViewAll}
          className="w-full flex items-center justify-center gap-2 text-blue-600 hover:text-blue-700 font-medium py-2 px-3 rounded-lg hover:bg-blue-50 transition-colors text-sm"
        >
          View All Activities
          <ArrowRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

export default ActivityFeed;
