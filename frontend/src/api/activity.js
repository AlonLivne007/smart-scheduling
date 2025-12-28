/**
 * Activity API Helpers
 * 
 * Functions to fetch and format system activity data for the dashboard.
 * 
 * @module api/activity
 */

import api from '../lib/axios.js';
import { formatDistanceToNow } from 'date-fns';

/**
 * Activity types and their configurations
 */
const ACTIVITY_TYPES = {
  USER_CREATED: {
    label: 'User Created',
    icon: 'UserPlus',
    color: 'bg-green-100',
    textColor: 'text-green-700',
  },
  SHIFT_ASSIGNED: {
    label: 'Shift Assigned',
    icon: 'ClipboardList',
    color: 'bg-blue-100',
    textColor: 'text-blue-700',
  },
  TIME_OFF_APPROVED: {
    label: 'Time-off Approved',
    icon: 'CheckCircle',
    color: 'bg-emerald-100',
    textColor: 'text-emerald-700',
  },
  TIME_OFF_REJECTED: {
    label: 'Time-off Rejected',
    icon: 'XCircle',
    color: 'bg-red-100',
    textColor: 'text-red-700',
  },
  SCHEDULE_CREATED: {
    label: 'Schedule Created',
    icon: 'Calendar',
    color: 'bg-purple-100',
    textColor: 'text-purple-700',
  },
};

/**
 * Generate mock activity data for demo purposes
 * Replace with real API endpoint when available
 * 
 * @returns {Array} Array of activity objects
 */
const generateMockActivities = () => {
  const now = new Date();
  
  return [
    {
      id: 1,
      type: 'USER_CREATED',
      description: 'Sarah Mitchell joined the team as Manager',
      timestamp: new Date(now.getTime() - 2 * 60000), // 2 minutes ago
      user: 'Admin',
    },
    {
      id: 2,
      type: 'SHIFT_ASSIGNED',
      description: 'John assigned to Monday 9AM-5PM shift',
      timestamp: new Date(now.getTime() - 15 * 60000), // 15 minutes ago
      user: 'John Manager',
    },
    {
      id: 3,
      type: 'TIME_OFF_APPROVED',
      description: 'Emily\'s time-off request approved for Dec 25-26',
      timestamp: new Date(now.getTime() - 45 * 60000), // 45 minutes ago
      user: 'Manager',
    },
    {
      id: 4,
      type: 'SHIFT_ASSIGNED',
      description: 'Michael assigned to Friday 2PM-10PM shift',
      timestamp: new Date(now.getTime() - 2 * 3600000), // 2 hours ago
      user: 'Schedule Admin',
    },
    {
      id: 5,
      type: 'TIME_OFF_REJECTED',
      description: 'David\'s time-off request rejected for critical period',
      timestamp: new Date(now.getTime() - 4 * 3600000), // 4 hours ago
      user: 'Manager',
    },
  ];
};

/**
 * Fetch recent activities from the backend
 * Currently returns mock data; will integrate with real API when available
 * 
 * @param {number} limit - Maximum number of activities to fetch (default: 10)
 * @returns {Promise<Array>} Array of activity objects with formatted timestamps
 * @throws {Error} If API call fails
 */
export const fetchRecentActivities = async (limit = 10) => {
  try {
    // TODO: Replace with real API endpoint when available
    // const response = await api.get(`/activity-log/?limit=${limit}`);
    // return response.data.map(formatActivity);

    // For now, return mock data
    const activities = generateMockActivities();
    
    return activities.slice(0, limit).map((activity) => ({
      ...activity,
      typeConfig: ACTIVITY_TYPES[activity.type] || ACTIVITY_TYPES.SHIFT_ASSIGNED,
      relativeTime: formatDistanceToNow(activity.timestamp, { addSuffix: true }),
    }));
  } catch (error) {
    console.error('Error fetching recent activities:', error);
    throw error;
  }
};

/**
 * Format a single activity object
 * 
 * @param {Object} activity - Activity object from API
 * @returns {Object} Formatted activity object
 */
const formatActivity = (activity) => {
  return {
    ...activity,
    typeConfig: ACTIVITY_TYPES[activity.type] || ACTIVITY_TYPES.SHIFT_ASSIGNED,
    relativeTime: formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true }),
  };
};

export { ACTIVITY_TYPES };
