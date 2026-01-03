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
 * Fetch recent activities from the API
 * @param {number} limit - Maximum number of activities to fetch
 * @param {Object} filters - Optional filters (user_id, entity_type)
 * @returns {Promise<Array>} List of formatted activities
 */
export const fetchRecentActivities = async (limit = 10, filters = {}) => {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit);
    
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.entity_type) params.append('entity_type', filters.entity_type);
    
    const response = await api.get(`/activities/?${params.toString()}`);
    
    // Transform backend activities to frontend format
    return response.data.map(activity => ({
      id: activity.activity_id,
      type: `${activity.entity_type}_${activity.action_type}`,
      description: activity.details || `${activity.action_type} on ${activity.entity_type} #${activity.entity_id}`,
      user: activity.user_full_name || 'System',
      timestamp: activity.created_at,
      relativeTime: formatDistanceToNow(new Date(activity.created_at), { addSuffix: true }),
      typeConfig: ACTIVITY_TYPES[`${activity.entity_type}_${activity.action_type}`] || ACTIVITY_TYPES.SHIFT_ASSIGNED,
      metadata: {
        action: activity.action_type,
        entity: activity.entity_type,
        entityId: activity.entity_id,
        userId: activity.user_id
      }
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
